import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'monitor_editais_token';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor: inject Authorization header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 → clear token → redirect to /login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      // Only redirect if not already on login/register page
      if (
        !window.location.pathname.includes('/login') &&
        !window.location.pathname.includes('/register')
      ) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth Service ──────────────────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

/**
 * POST /auth/login
 * Backend uses OAuth2PasswordRequestForm (form-data, NOT JSON).
 * Fields: username (email) and password.
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await api.post<LoginResponse>('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
}

/**
 * POST /auth/register
 * Backend expects JSON: { name, email, password }
 */
export async function register(name: string, email: string, password: string): Promise<UserResponse> {
  const response = await api.post<UserResponse>('/auth/register', {
    name,
    email,
    password,
  });
  return response.data;
}

/**
 * GET /users/me
 * Returns the authenticated user's data.
 */
export async function getMe(): Promise<UserResponse> {
  const response = await api.get<UserResponse>('/users/me');
  return response.data;
}

// ── Notices Service ───────────────────────────────────────────────────────────

export interface InstitutionBasicResponse {
  id: number;
  name: string;
  initials: string;
  state: string;
  official_site_url: string;
}

export interface NoticeResponse {
  id: number;
  institution_id: number;
  source_id: number;
  title: string;
  url: string;
  notice_type: string;
  detected_at: string;
  publication_date: string | null;
  description: string | null;
  is_active: boolean;
}

export interface NoticeDetailResponse extends NoticeResponse {
  institution: InstitutionBasicResponse | null;
}

export interface NoticesFilters {
  keyword?: string;
  state?: string;
  notice_type?: string;
  detected_after?: string;
  detected_before?: string;
  skip?: number;
  limit?: number;
}

/**
 * GET /notices
 * Public endpoint — lists active notices with optional filters.
 */
export async function getNotices(filters: NoticesFilters = {}): Promise<NoticeResponse[]> {
  const params: Record<string, string | number> = {};

  if (filters.keyword) params.keyword = filters.keyword;
  if (filters.state) params.state = filters.state;
  if (filters.notice_type) params.notice_type = filters.notice_type;
  if (filters.detected_after) params.detected_after = filters.detected_after;
  if (filters.detected_before) params.detected_before = filters.detected_before;
  if (filters.skip !== undefined) params.skip = filters.skip;
  if (filters.limit !== undefined) params.limit = filters.limit;

  const response = await api.get<NoticeResponse[]>('/notices/', { params });
  return response.data;
}

/**
 * GET /notices/{id}
 * Public endpoint — returns a single notice with institution details.
 */
export async function getNoticeById(id: number): Promise<NoticeDetailResponse> {
  const response = await api.get<NoticeDetailResponse>(`/notices/${id}`);
  return response.data;
}

// ── Alerts Service ────────────────────────────────────────────────────────────

export interface UserAlertResponse {
  id: number;
  user_id: number;
  keyword: string;
  institution_id: number | null;
  notice_type: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface UserAlertCreate {
  keyword: string;
  notice_type?: string;
}

export interface UserAlertUpdate {
  keyword?: string;
  notice_type?: string;
  is_active?: boolean;
}

/**
 * GET /alerts
 * Authenticated — lists all alerts for the current user.
 */
export async function getAlerts(skip = 0, limit = 50): Promise<UserAlertResponse[]> {
  const response = await api.get<UserAlertResponse[]>('/alerts/', {
    params: { skip, limit },
  });
  return response.data;
}

/**
 * POST /alerts
 * Authenticated — creates a new alert.
 */
export async function createAlert(data: UserAlertCreate): Promise<UserAlertResponse> {
  const response = await api.post<UserAlertResponse>('/alerts/', data);
  return response.data;
}

/**
 * PUT /alerts/{id}
 * Authenticated — partially updates an alert.
 */
export async function updateAlert(id: number, data: UserAlertUpdate): Promise<UserAlertResponse> {
  const response = await api.put<UserAlertResponse>(`/alerts/${id}`, data);
  return response.data;
}

/**
 * DELETE /alerts/{id}
 * Authenticated — soft-deletes an alert (sets is_active=false).
 */
export async function deleteAlert(id: number): Promise<UserAlertResponse> {
  const response = await api.delete<UserAlertResponse>(`/alerts/${id}`);
  return response.data;
}

// ── Notifications Service ─────────────────────────────────────────────────────

export interface NotificationResponse {
  id: number;
  user_id: number;
  notice_id: number;
  status: string;
  sent_at: string | null;
  error_message: string | null;
  created_at: string;
}

/**
 * GET /notifications
 * Authenticated — lists notifications for the current user.
 */
export async function getNotifications(skip = 0, limit = 50): Promise<NotificationResponse[]> {
  const response = await api.get<NotificationResponse[]>('/notifications/', {
    params: { skip, limit },
  });
  return response.data;
}

// ── Admin Institutions Service ────────────────────────────────────────────────

export interface InstitutionResponse {
  id: number;
  name: string;
  initials: string;
  state: string;
  official_site_url: string;
  logo_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface InstitutionCreate {
  name: string;
  initials: string;
  state: string;
  official_site_url: string;
  logo_url?: string | null;
  is_active?: boolean;
}

export interface InstitutionUpdate {
  name?: string;
  initials?: string;
  state?: string;
  official_site_url?: string;
  logo_url?: string | null;
  is_active?: boolean;
}

export async function getAdminInstitutions(skip = 0, limit = 20): Promise<InstitutionResponse[]> {
  const response = await api.get<InstitutionResponse[]>('/admin/institutions/', {
    params: { skip, limit },
  });
  return response.data;
}

export async function createAdminInstitution(data: InstitutionCreate): Promise<InstitutionResponse> {
  const response = await api.post<InstitutionResponse>('/admin/institutions/', data);
  return response.data;
}

export async function updateAdminInstitution(id: number, data: InstitutionUpdate): Promise<InstitutionResponse> {
  const response = await api.put<InstitutionResponse>(`/admin/institutions/${id}`, data);
  return response.data;
}

export async function deleteAdminInstitution(id: number): Promise<InstitutionResponse> {
  const response = await api.delete<InstitutionResponse>(`/admin/institutions/${id}`);
  return response.data;
}

// ── Admin Sources Service ─────────────────────────────────────────────────────

export interface MonitoredSourceResponse {
  id: number;
  institution_id: number;
  name: string;
  url: string;
  source_type: string;
  check_frequency_minutes: number;
  last_checked_at: string | null;
  last_success_at: string | null;
  last_error_message: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface MonitoredSourceCreate {
  institution_id: number;
  name: string;
  url: string;
  source_type: string;
  check_frequency_minutes: number;
  is_active?: boolean;
}

export interface MonitoredSourceUpdate {
  institution_id?: number;
  name?: string;
  url?: string;
  source_type?: string;
  check_frequency_minutes?: number;
  is_active?: boolean;
}

export async function getAdminSources(skip = 0, limit = 20): Promise<MonitoredSourceResponse[]> {
  const response = await api.get<MonitoredSourceResponse[]>('/admin/sources/', {
    params: { skip, limit },
  });
  return response.data;
}

export async function createAdminSource(data: MonitoredSourceCreate): Promise<MonitoredSourceResponse> {
  const response = await api.post<MonitoredSourceResponse>('/admin/sources/', data);
  return response.data;
}

export async function updateAdminSource(id: number, data: MonitoredSourceUpdate): Promise<MonitoredSourceResponse> {
  const response = await api.put<MonitoredSourceResponse>(`/admin/sources/${id}`, data);
  return response.data;
}

export async function deleteAdminSource(id: number): Promise<MonitoredSourceResponse> {
  const response = await api.delete<MonitoredSourceResponse>(`/admin/sources/${id}`);
  return response.data;
}

// ── Admin National Coverage Service ──────────────────────────────────────────

export type CoverageStatus =
  | 'verified'
  | 'partial'
  | 'source_not_found'
  | 'temporarily_unavailable'
  | 'manual_review'
  | 'unsupported'
  | 'inactive';

export interface InventoryCoverage {
  census_raw_total: number;
  eligible_census_total: number;
  post_census_total: number;
  inventory_total: number;
  eligible_total: number;
  registered: number;
  percent: number;
}

export interface CoverageStage {
  institutions: number;
  percent: number;
}

export interface CoverageBreakdownItem {
  key: string;
  label: string;
  inventory_total: number;
  eligible_total: number;
  mapped_sources: number;
  institutions_with_source: number;
  institutions_without_source: number;
  verified: number;
  partial: number;
  manual_review: number;
  source_not_found: number;
  capture_validated: number;
  active_monitoring: number;
}

export interface SpiderBreakdownItem {
  spider: string;
  sources: number;
  institutions: number;
}

export interface CoverageBreakdown {
  regions: CoverageBreakdownItem[];
  states: CoverageBreakdownItem[];
  administrative_categories: CoverageBreakdownItem[];
  academic_organizations: CoverageBreakdownItem[];
  spiders: SpiderBreakdownItem[];
}

export interface CoveragePendingItem {
  official_code: string;
  official_name: string;
  state: string;
  region: string;
  status: string;
  reason: string;
}

export interface CoverageResponse {
  inventory_total: number;
  eligible_target_total: number;
  mapped_source_total_inventory: number;
  mapped_source_total_eligible: number;
  institutions_with_source: number;
  institutions_without_source: number;
  verified_source_institutions: number;
  partial_source_institutions: number;
  manual_review_institutions: number;
  source_not_found_institutions: number;
  validated_capture_total: number;
  active_monitoring_total: number;
  inventory: InventoryCoverage;
  mapped: CoverageStage;
  verified: CoverageStage;
  capture_validated: CoverageStage;
  active_monitoring: CoverageStage;
  institution_status_counts: Record<string, number>;
  source_status_counts: Record<string, number>;
  breakdown: CoverageBreakdown;
  last_audit: string | null;
  pending: CoveragePendingItem[];
}

export interface CoverageInstitutionItem {
  official_code: string;
  official_name: string;
  initials: string;
  state: string;
  region: string;
  administrative_category_code: number | null;
  administrative_category: string | null;
  academic_organization_code: number | null;
  academic_organization: string | null;
  eligibility_status: string;
  eligibility_reason: string | null;
  coverage_status: string;
  coverage_notes: string | null;
  source_count: number;
  source_statuses: string[];
  has_source: boolean;
  registered: boolean;
  institution_active: boolean | null;
  source_active: boolean;
  capture_validated: boolean;
  active_monitoring: boolean;
}

export interface CoverageInstitutionList {
  total: number;
  skip: number;
  limit: number;
  items: CoverageInstitutionItem[];
}

export interface CoverageSummaryFilters {
  region?: string;
  state?: string;
  administrative_category_code?: number;
  source_status?: CoverageStatus;
}

export interface CoverageInstitutionFilters {
  region?: string;
  state?: string;
  administrative_category_code?: number;
  academic_organization_code?: number;
  eligibility_status?: string;
  coverage_status?: CoverageStatus;
  verification_status?: CoverageStatus;
  institution_active?: boolean;
  source_active?: boolean;
  has_source?: boolean;
  manual_review?: boolean;
  skip?: number;
  limit?: number;
}

export async function getAdminCoverage(
  filters: CoverageSummaryFilters = {}
): Promise<CoverageResponse> {
  const response = await api.get<CoverageResponse>('/admin/coverage', { params: filters });
  return response.data;
}

export async function getAdminCoverageRegions(): Promise<CoverageBreakdownItem[]> {
  const response = await api.get<CoverageBreakdownItem[]>('/admin/coverage/regions');
  return response.data;
}

export async function getAdminCoverageInstitutions(
  filters: CoverageInstitutionFilters = {}
): Promise<CoverageInstitutionList> {
  const response = await api.get<CoverageInstitutionList>('/admin/coverage/institutions', {
    params: filters,
  });
  return response.data;
}

export interface CrawlerRunSummary {
  sources_checked: number;
  items_found: number;
  new_items: number;
  failed_sources: number;
}

export interface CrawlerRunInstitution {
  id: number;
  name: string;
  initials: string;
}

export interface CrawlerRunResponse {
  id: number;
  source_id: number;
  source_name: string;
  source_url: string;
  institution: CrawlerRunInstitution;
  status: string;
  items_found: number;
  new_items: number;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface CrawlerSourceStatusResponse {
  source_id: number;
  source_name: string;
  source_url: string;
  source_type: string;
  institution_id: number;
  institution_name: string;
  institution_initials: string;
  is_active: boolean;
  last_checked_at: string | null;
  last_success_at: string | null;
  last_error_message: string | null;
  health_status: 'inactive' | 'never_checked' | 'error' | 'warning' | 'ok';
  last_run: CrawlerRunResponse | null;
}

export interface CrawlerStatusResponse {
  total_sources: number;
  active_sources: number;
  inactive_sources: number;
  ok_sources: number;
  warning_sources: number;
  error_sources: number;
  never_checked_sources: number;
  total_active_notices: number;
  last_run: CrawlerRunResponse | null;
  last_run_items_found: number;
  last_run_new_items: number;
}

export async function runAdminCrawler(): Promise<CrawlerRunSummary> {
  const response = await api.post<CrawlerRunSummary>('/admin/run-crawler');
  return response.data;
}

export async function runAdminCrawlerSource(sourceId: number): Promise<CrawlerRunSummary> {
  const response = await api.post<CrawlerRunSummary>(`/admin/run-crawler/source/${sourceId}`);
  return response.data;
}

export async function getCrawlerStatus(): Promise<CrawlerStatusResponse> {
  const response = await api.get<CrawlerStatusResponse>('/admin/crawler/status');
  return response.data;
}

export async function getCrawlerSourcesStatus(): Promise<CrawlerSourceStatusResponse[]> {
  const response = await api.get<CrawlerSourceStatusResponse[]>('/admin/crawler/sources-status');
  return response.data;
}

export async function getCrawlerRuns(skip = 0, limit = 20): Promise<CrawlerRunResponse[]> {
  const response = await api.get<CrawlerRunResponse[]>('/admin/crawler/runs', {
    params: { skip, limit },
  });
  return response.data;
}
export { TOKEN_KEY };
export default api;

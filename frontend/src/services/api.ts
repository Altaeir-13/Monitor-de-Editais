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

  const response = await api.get<NoticeResponse[]>('/notices', { params });
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

export { TOKEN_KEY };
export default api;

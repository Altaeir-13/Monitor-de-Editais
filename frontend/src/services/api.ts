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

export { TOKEN_KEY };
export default api;

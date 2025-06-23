const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login/`,
    LOGOUT: `${API_BASE_URL}/auth/logout/`,
    REFRESH: `${API_BASE_URL}/auth/refresh/`,
  },
  USERS: {
    ME: `${API_BASE_URL}/users/me/`,
    LIST: `${API_BASE_URL}/users/`,
    CREATE: `${API_BASE_URL}/users/`,
  },
};

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};

export const getAuthHeader = (token: string) => ({
  'Authorization': `Bearer ${token}`,
});

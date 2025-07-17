const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const API_ENDPOINTS = {
  BASE_URL: API_BASE_URL,
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
  TENANTS: {
    REGISTER: `${API_BASE_URL}/tenants/register/`,
    INFO: `${API_BASE_URL}/tenants/info`,
    CONFIG: `${API_BASE_URL}/tenants/config/`,
  },
  PETS: {
    LIST: `${API_BASE_URL}/pets/`,
    DETAIL: (id: number) => `${API_BASE_URL}/pets/${id}/`,
    VACINAS: (petId: number) => `${API_BASE_URL}/pets/${petId}/vacinas/`,
    HISTORICO: (petId: number) => `${API_BASE_URL}/pets/${petId}/historico/`,
  },
  CLIENTES: {
    LIST: `${API_BASE_URL}/clientes/`,
    DETAIL: (id: number) => `${API_BASE_URL}/clientes/${id}/`,
  },
  AGENDAMENTOS: {
    LIST: `${API_BASE_URL}/agendamentos/`,
    DETAIL: (id: number) => `${API_BASE_URL}/agendamentos/${id}/`,
  },
  PRODUTOS: {
    LIST: `${API_BASE_URL}/produtos/`,
    DETAIL: (id: number) => `${API_BASE_URL}/produtos/${id}/`,
  },
  VENDAS: {
    LIST: `${API_BASE_URL}/vendas/`,
    DETAIL: (id: number) => `${API_BASE_URL}/vendas/${id}/`,
  },
};

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};

export const getAuthHeader = (token: string) => ({
  'Authorization': `Bearer ${token}`,
});

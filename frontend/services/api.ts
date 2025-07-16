import { API_ENDPOINTS, getAuthHeader } from '@/config/api';
import { LoginCredentials, LoginResponse, User, CreateUserData } from '@/types';
import { getTenantHeaders } from '@/lib/tenant';

export class AuthService {
  static async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getTenantHeaders(),
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Falha no login');
    }

    return response.json();
  }

  static async logout(): Promise<void> {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      await fetch(API_ENDPOINTS.AUTH.LOGOUT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader(token),
          ...getTenantHeaders(),
        },
      });
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  }

  static async refreshToken(refresh: string): Promise<{ access: string }> {
    const response = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getTenantHeaders(),
      },
      body: JSON.stringify({ refresh }),
    });

    if (!response.ok) {
      throw new Error('Falha ao atualizar token');
    }

    return response.json();
  }

  static async getCurrentUser(token: string): Promise<User> {
    const response = await fetch(API_ENDPOINTS.USERS.ME, {
      headers: {
        ...getAuthHeader(token),
        ...getTenantHeaders(),
      },
    });

    if (!response.ok) {
      throw new Error('Falha ao buscar dados do usuário');
    }

    return response.json();
  }

  static async createUser(userData: CreateUserData, token: string): Promise<User> {
    const response = await fetch(API_ENDPOINTS.USERS.CREATE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(token),
        ...getTenantHeaders(),
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro ao criar usuário');
    }

    return response.json();
  }

  static async listUsers(token: string): Promise<User[]> {
    const response = await fetch(API_ENDPOINTS.USERS.LIST, {
      headers: {
        ...getAuthHeader(token),
        ...getTenantHeaders(),
      },
    });

    if (!response.ok) {
      throw new Error('Falha ao listar usuários');
    }

    return response.json();
  }
}

export const authService = {
  login: AuthService.login,
  logout: AuthService.logout,
  refreshToken: AuthService.refreshToken,
  getCurrentUser: AuthService.getCurrentUser,
  createUser: AuthService.createUser,
  listUsers: AuthService.listUsers,
};

export default {
  auth: authService,
};

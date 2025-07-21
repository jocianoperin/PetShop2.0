import { API_ENDPOINTS, getAuthHeader } from '@/config/api';
import { LoginCredentials, LoginResponse, User, CreateUserData, Tenant } from '@/types';
import { getTenantHeaders, getCurrentTenant, storeTenantData, addRecentTenant } from '@/lib/tenant';

// Create a base API client that automatically includes tenant headers
export class ApiClient {
  static async request<T>(
    url: string, 
    options: RequestInit = {}, 
    customTenantId?: string
  ): Promise<T> {
    // Get tenant headers (either from custom tenant ID or from current tenant)
    const tenantHeaders = customTenantId 
      ? { 'X-Tenant-ID': customTenantId }
      : getTenantHeaders();
    
    // Merge headers - don't set Content-Type for FormData
    const headers = {
      ...(!(options.body instanceof FormData) && { 'Content-Type': 'application/json' }),
      ...options.headers,
      ...tenantHeaders,
    };
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });
      
      if (!response.ok) {
        try {
          const errorData = await response.json();
          
          // Check for tenant-specific errors
          if (response.status === 404 && errorData.code === 'TENANT_NOT_FOUND') {
            throw new Error(`Tenant não encontrado: ${customTenantId || getCurrentTenant()}`);
          }
          
          if (response.status === 403 && errorData.code === 'TENANT_INACTIVE') {
            throw new Error(`Tenant inativo ou suspenso: ${customTenantId || getCurrentTenant()}`);
          }
          
          throw new Error(errorData.detail || `API Error: ${response.status}`);
        } catch (e) {
          if (e instanceof Error) {
            throw e;
          }
          throw new Error(`API Error: ${response.status}`);
        }
      }
      
      // Extract tenant information from response headers if available
      const tenantIdHeader = response.headers.get('X-Tenant-ID');
      const tenantNameHeader = response.headers.get('X-Tenant-Name');
      
      if (tenantIdHeader && tenantNameHeader) {
        // Store basic tenant info from headers
        const basicTenant: Partial<Tenant> = {
          subdomain: tenantIdHeader,
          name: tenantNameHeader,
        };
        
        // We'll update this with more complete info if it comes in the response body
        console.log('Tenant info from headers:', basicTenant);
      }
      
      return response.json();
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }
  
  static async get<T>(url: string, token?: string, customTenantId?: string): Promise<T> {
    const headers = token ? getAuthHeader(token) : {};
    return this.request<T>(url, { headers }, customTenantId);
  }
  
  static async post<T>(url: string, data: any, token?: string, customTenantId?: string): Promise<T> {
    const headers = token ? getAuthHeader(token) : {};
    return this.request<T>(
      url, 
      {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      },
      customTenantId
    );
  }
  
  static async put<T>(url: string, data: any, token?: string, customTenantId?: string): Promise<T> {
    const headers = token ? getAuthHeader(token) : {};
    return this.request<T>(
      url, 
      {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      },
      customTenantId
    );
  }
  
  static async delete<T>(url: string, token?: string, customTenantId?: string): Promise<T> {
    const headers = token ? getAuthHeader(token) : {};
    return this.request<T>(
      url, 
      {
        method: 'DELETE',
        headers,
      },
      customTenantId
    );
  }
  
  static async postFormData<T>(url: string, formData: FormData, token?: string, customTenantId?: string): Promise<T> {
    const headers = token ? getAuthHeader(token) : {};
    return this.request<T>(
      url, 
      {
        method: 'POST',
        headers,
        body: formData,
      },
      customTenantId
    );
  }
  
  // New method to fetch tenant information
  static async fetchTenantInfo(tenantId: string): Promise<Tenant> {
    return this.get<Tenant>(`${API_ENDPOINTS.TENANTS.INFO}/${tenantId}`, undefined, tenantId);
  }
}

export class AuthService {
  static async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      // For login, we explicitly use the tenant_id from credentials
      const response = await ApiClient.post<LoginResponse>(
        API_ENDPOINTS.AUTH.LOGIN, 
        credentials,
        undefined,
        credentials.tenant_id
      );
      
      // Store tenant information if available
      if (response.tenant) {
        storeTenantData(response.tenant);
        addRecentTenant(response.tenant);
      } else if (response.user?.tenant) {
        storeTenantData(response.user.tenant);
        addRecentTenant(response.user.tenant);
      }
      
      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  static async logout(): Promise<void> {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      await ApiClient.post<void>(API_ENDPOINTS.AUTH.LOGOUT, {}, token);
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  }

  static async refreshToken(refresh: string): Promise<{ access: string }> {
    return ApiClient.post<{ access: string }>(
      API_ENDPOINTS.AUTH.REFRESH, 
      { refresh }
    );
  }

  static async getCurrentUser(token: string): Promise<User> {
    const user = await ApiClient.get<User>(API_ENDPOINTS.USERS.ME, token);
    
    // Store tenant information if available in user data
    if (user.tenant) {
      storeTenantData(user.tenant);
      addRecentTenant(user.tenant);
    }
    
    return user;
  }

  static async createUser(userData: CreateUserData, token: string): Promise<User> {
    return ApiClient.post<User>(API_ENDPOINTS.USERS.CREATE, userData, token);
  }

  static async listUsers(token: string): Promise<User[]> {
    return ApiClient.get<User[]>(API_ENDPOINTS.USERS.LIST, token);
  }
  
  static async getTenantInfo(tenantId: string): Promise<Tenant> {
    return ApiClient.get<Tenant>(`${API_ENDPOINTS.TENANTS.INFO}/${tenantId}`, undefined, tenantId);
  }
  
  static async validateTenant(tenantId: string): Promise<boolean> {
    try {
      await this.getTenantInfo(tenantId);
      return true;
    } catch (error) {
      return false;
    }
  }
}

export const authService = {
  login: AuthService.login,
  logout: AuthService.logout,
  refreshToken: AuthService.refreshToken,
  getCurrentUser: AuthService.getCurrentUser,
  createUser: AuthService.createUser,
  listUsers: AuthService.listUsers,
  getTenantInfo: AuthService.getTenantInfo,
  validateTenant: AuthService.validateTenant,
};

export default {
  auth: authService,
};

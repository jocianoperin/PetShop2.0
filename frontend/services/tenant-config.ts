import { API_ENDPOINTS } from '@/config/api';
import { ApiClient } from './api';
import { getCurrentTenant } from '@/lib/tenant';
import { Tenant } from '@/lib/tenant';

export interface TenantConfig {
  name: string;
  logo_url?: string | null;
  theme?: {
    primary_color?: string;
    secondary_color?: string;
    accent_color?: string;
  };
  settings?: Record<string, any>;
}

// Use API_ENDPOINTS from config
const API_BASE_URL = API_ENDPOINTS.BASE_URL || 'http://127.0.0.1:8000/api';

const TENANT_ENDPOINTS = {
  CONFIG: `${API_BASE_URL}/tenants/config`,
  UPLOAD_LOGO: `${API_BASE_URL}/tenants/upload-logo`,
  INFO: (tenantId: string) => `${API_BASE_URL}/tenants/${tenantId}`,
};

export class TenantConfigService {
  /**
   * Get tenant configuration
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns Tenant configuration
   */
  static async getTenantConfig(token?: string, customTenantId?: string): Promise<TenantConfig> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to fetch tenant configuration");
    }
    
    return ApiClient.get<TenantConfig>(TENANT_ENDPOINTS.CONFIG, token, tenantId);
  }

  /**
   * Update tenant configuration
   * @param configData Updated configuration data
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns Updated tenant configuration
   */
  static async updateTenantConfig(configData: Partial<TenantConfig>, token?: string, customTenantId?: string): Promise<TenantConfig> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to update tenant configuration");
    }
    
    return ApiClient.put<TenantConfig>(TENANT_ENDPOINTS.CONFIG, configData, token, tenantId);
  }

  /**
   * Upload tenant logo
   * @param logoFile Logo file to upload
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns URL of the uploaded logo
   */
  static async uploadLogo(logoFile: File, token?: string, customTenantId?: string): Promise<{ logo_url: string }> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to upload logo");
    }
    
    const formData = new FormData();
    formData.append('logo', logoFile);
    
    return ApiClient.postFormData<{ logo_url: string }>(TENANT_ENDPOINTS.UPLOAD_LOGO, formData, token, tenantId);
  }

  /**
   * Get tenant information
   * @param tenantId Tenant ID
   * @param token Auth token (optional)
   * @returns Tenant information
   */
  static async getTenantInfo(tenantId: string, token?: string): Promise<Tenant> {
    if (!tenantId) {
      throw new Error("Tenant ID is required to fetch tenant information");
    }
    
    return ApiClient.get<Tenant>(TENANT_ENDPOINTS.INFO(tenantId), token, tenantId);
  }
}

export const tenantConfigService = {
  getTenantConfig: TenantConfigService.getTenantConfig,
  updateTenantConfig: TenantConfigService.updateTenantConfig,
  uploadLogo: TenantConfigService.uploadLogo,
  getTenantInfo: TenantConfigService.getTenantInfo,
};

export default tenantConfigService;
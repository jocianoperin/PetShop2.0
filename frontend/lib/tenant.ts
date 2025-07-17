/**
 * Tenant detection and management utilities
 */

export interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  schema_name: string;
  is_active: boolean;
  plan_type: string;
  created_at: string;
  logo_url?: string;
  theme?: {
    primary_color?: string;
    secondary_color?: string;
    accent_color?: string;
  };
}

// Storage keys
const TENANT_STORAGE_KEY = 'current_tenant';
const TENANT_DATA_STORAGE_KEY = 'tenant_data';
const RECENT_TENANTS_KEY = 'recent_tenants';

/**
 * Extract tenant subdomain from hostname
 */
export function getTenantFromHostname(hostname: string): string | null {
  // Remove port if present
  const cleanHostname = hostname.split(':')[0];
  
  // Split by dots and check if we have a subdomain
  const parts = cleanHostname.split('.');
  
  // If we have at least 3 parts (subdomain.domain.tld), extract subdomain
  if (parts.length >= 3) {
    return parts[0];
  }
  
  // For development, check for localhost patterns like tenant1.localhost
  if (parts.length === 2 && parts[1] === 'localhost') {
    return parts[0];
  }
  
  return null;
}

/**
 * Store a tenant in the recent tenants list
 */
export function addRecentTenant(tenant: Tenant): void {
  if (typeof window === 'undefined') return;
  
  try {
    const recentTenantsJson = localStorage.getItem(RECENT_TENANTS_KEY);
    const recentTenants: Tenant[] = recentTenantsJson ? JSON.parse(recentTenantsJson) : [];
    
    // Check if tenant already exists in the list
    const existingIndex = recentTenants.findIndex(t => t.subdomain === tenant.subdomain);
    
    if (existingIndex >= 0) {
      // Remove the existing entry
      recentTenants.splice(existingIndex, 1);
    }
    
    // Add to the beginning of the list
    recentTenants.unshift(tenant);
    
    // Keep only the last 5 tenants
    const trimmedList = recentTenants.slice(0, 5);
    
    localStorage.setItem(RECENT_TENANTS_KEY, JSON.stringify(trimmedList));
  } catch (e) {
    console.error('Error storing recent tenant:', e);
  }
}

/**
 * Get list of recently accessed tenants
 */
export function getRecentTenants(): Tenant[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const recentTenantsJson = localStorage.getItem(RECENT_TENANTS_KEY);
    return recentTenantsJson ? JSON.parse(recentTenantsJson) : [];
  } catch (e) {
    console.error('Error retrieving recent tenants:', e);
    return [];
  }
}

/**
 * Get current tenant from browser environment
 */
export function getCurrentTenant(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  
  // First try to get from hostname
  const tenantFromHostname = getTenantFromHostname(window.location.hostname);
  if (tenantFromHostname) {
    return tenantFromHostname;
  }
  
  // Fallback to localStorage for development
  return localStorage.getItem(TENANT_STORAGE_KEY);
}

/**
 * Set current tenant (for development/testing)
 */
export function setCurrentTenant(tenantId: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TENANT_STORAGE_KEY, tenantId);
  }
}

/**
 * Clear current tenant
 */
export function clearCurrentTenant(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TENANT_STORAGE_KEY);
    localStorage.removeItem(TENANT_DATA_STORAGE_KEY);
  }
}

/**
 * Store tenant data in local storage
 */
export function storeTenantData(tenant: Tenant): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TENANT_DATA_STORAGE_KEY, JSON.stringify(tenant));
    setCurrentTenant(tenant.subdomain);
  }
}

/**
 * Get stored tenant data
 */
export function getStoredTenantData(): Tenant | null {
  if (typeof window === 'undefined') {
    return null;
  }
  
  const tenantData = localStorage.getItem(TENANT_DATA_STORAGE_KEY);
  if (!tenantData) {
    return null;
  }
  
  try {
    return JSON.parse(tenantData) as Tenant;
  } catch (e) {
    console.error('Error parsing tenant data:', e);
    return null;
  }
}

/**
 * Check if we're in a multitenant environment
 */
export function isMultitenantEnvironment(): boolean {
  return getCurrentTenant() !== null;
}

/**
 * Get tenant-aware API headers
 */
export function getTenantHeaders(): Record<string, string> {
  const tenant = getCurrentTenant();
  if (!tenant) {
    return {};
  }
  
  return {
    'X-Tenant-ID': tenant,
  };
}

/**
 * Build tenant-aware URL for redirects
 */
export function buildTenantUrl(path: string = '/'): string {
  const tenant = getCurrentTenant();
  if (!tenant) {
    return path;
  }
  
  // For development with localhost
  if (typeof window !== 'undefined' && window.location.hostname.includes('localhost')) {
    const port = window.location.port ? `:${window.location.port}` : '';
    return `http://${tenant}.localhost${port}${path}`;
  }
  
  // For production with actual domains
  const protocol = typeof window !== 'undefined' ? window.location.protocol : 'https:';
  const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
  
  // Extract base domain (remove subdomain if present)
  const parts = hostname.split('.');
  let baseDomain = hostname;
  
  if (parts.length >= 3) {
    // Remove the first part (current subdomain)
    baseDomain = parts.slice(1).join('.');
  }
  
  const port = typeof window !== 'undefined' && window.location.port ? `:${window.location.port}` : '';
  
  return `${protocol}//${tenant}.${baseDomain}${port}${path}`;
}

/**
 * Redirect to tenant-specific URL
 */
export function redirectToTenant(tenant: string, path: string = '/'): void {
  if (typeof window !== 'undefined') {
    const tenantUrl = buildTenantUrl(path);
    window.location.href = tenantUrl;
  }
}
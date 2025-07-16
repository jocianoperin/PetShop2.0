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
}

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
  return localStorage.getItem('current_tenant');
}

/**
 * Set current tenant (for development/testing)
 */
export function setCurrentTenant(tenantId: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('current_tenant', tenantId);
  }
}

/**
 * Clear current tenant
 */
export function clearCurrentTenant(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('current_tenant');
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
  const port = typeof window !== 'undefined' && window.location.port ? `:${window.location.port}` : '';
  
  return `${protocol}//${tenant}.${hostname}${port}${path}`;
}
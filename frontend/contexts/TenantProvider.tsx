'use client';

import { createContext, useContext, ReactNode, useState, useEffect } from 'react';
import { Tenant } from '@/types';
import { 
  getCurrentTenant, 
  getTenantFromHostname, 
  setCurrentTenant, 
  clearCurrentTenant,
  getStoredTenantData,
  storeTenantData
} from '@/lib/tenant';

interface TenantContextType {
  tenant: Tenant | null;
  tenantId: string | null;
  isLoading: boolean;
  setTenant: (tenant: Tenant | null) => void;
  detectTenant: () => string | null;
  clearTenant: () => void;
  fetchTenantInfo: (tenantId: string) => Promise<Tenant | null>;
}

const TenantContext = createContext<TenantContextType | null>(null);

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenantState] = useState<Tenant | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Detect tenant from hostname or localStorage
  const detectTenant = (): string | null => {
    if (typeof window === 'undefined') return null;
    
    // Try to detect from hostname first
    const hostnameTenat = getTenantFromHostname(window.location.hostname);
    if (hostnameTenat) {
      return hostnameTenat;
    }
    
    // Fallback to stored tenant
    return getCurrentTenant();
  };

  // Set tenant and update related state
  const setTenant = (newTenant: Tenant | null) => {
    setTenantState(newTenant);
    if (newTenant) {
      setTenantId(newTenant.subdomain);
      setCurrentTenant(newTenant.subdomain);
      storeTenantData(newTenant);
      
      // Apply tenant theme if available
      if (newTenant.theme && typeof document !== 'undefined') {
        applyTenantTheme(newTenant);
      }
    } else {
      setTenantId(null);
    }
  };

  // Apply tenant theme to document
  const applyTenantTheme = (tenant: Tenant) => {
    if (!tenant.theme) return;
    
    const root = document.documentElement;
    
    if (tenant.theme.primary_color) {
      root.style.setProperty('--primary', tenant.theme.primary_color);
    }
    
    if (tenant.theme.secondary_color) {
      root.style.setProperty('--secondary', tenant.theme.secondary_color);
    }
    
    if (tenant.theme.accent_color) {
      root.style.setProperty('--accent', tenant.theme.accent_color);
    }
  };

  // Clear tenant data
  const clearTenant = () => {
    setTenantState(null);
    setTenantId(null);
    clearCurrentTenant();
    
    // Reset theme variables
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      root.style.removeProperty('--primary');
      root.style.removeProperty('--secondary');
      root.style.removeProperty('--accent');
    }
  };
  
  // Fetch tenant information from API
  const fetchTenantInfo = async (tenantId: string): Promise<Tenant | null> => {
    try {
      // In a real implementation, this would make an API call to get tenant details
      // For now, we'll simulate it with stored data
      const storedTenant = getStoredTenantData();
      
      if (storedTenant && storedTenant.subdomain === tenantId) {
        return storedTenant;
      }
      
      // Mock API call for demo purposes
      // In production, this would be an actual API call
      const mockTenant: Tenant = {
        id: tenantId,
        name: `Pet Shop ${tenantId.charAt(0).toUpperCase() + tenantId.slice(1)}`,
        subdomain: tenantId,
        schema_name: `tenant_${tenantId}`,
        is_active: true,
        plan_type: 'basic',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        logo_url: null,
        theme: {
          primary_color: '#0ea5e9',
          secondary_color: '#f97316',
          accent_color: '#8b5cf6'
        }
      };
      
      // Store the tenant data
      storeTenantData(mockTenant);
      return mockTenant;
    } catch (error) {
      console.error('Error fetching tenant info:', error);
      return null;
    }
  };

  // Initialize tenant detection on mount
  useEffect(() => {
    const initializeTenant = async () => {
      // Detect tenant ID from hostname or localStorage
      const detectedTenantId = detectTenant();
      setTenantId(detectedTenantId);
      
      if (detectedTenantId) {
        // Try to get tenant data from localStorage first
        const storedTenant = getStoredTenantData();
        
        if (storedTenant && storedTenant.subdomain === detectedTenantId) {
          setTenantState(storedTenant);
          
          // Apply tenant theme if available
          if (storedTenant.theme) {
            applyTenantTheme(storedTenant);
          }
        } else {
          // If not in localStorage, fetch from API
          const tenantInfo = await fetchTenantInfo(detectedTenantId);
          if (tenantInfo) {
            setTenantState(tenantInfo);
            
            // Apply tenant theme if available
            if (tenantInfo.theme) {
              applyTenantTheme(tenantInfo);
            }
          }
        }
      }
      
      setIsLoading(false);
    };
    
    initializeTenant();
  }, []);

  // Add a listener for hostname changes (for development with subdomain switching)
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleHostnameChange = async () => {
      const detectedTenantId = getTenantFromHostname(window.location.hostname);
      if (detectedTenantId && detectedTenantId !== tenantId) {
        setTenantId(detectedTenantId);
        setCurrentTenant(detectedTenantId);
        
        // Try to get tenant data from localStorage first
        const storedTenant = getStoredTenantData();
        
        if (storedTenant && storedTenant.subdomain === detectedTenantId) {
          setTenantState(storedTenant);
          
          // Apply tenant theme if available
          if (storedTenant.theme) {
            applyTenantTheme(storedTenant);
          }
        } else {
          // If not in localStorage, fetch from API
          const tenantInfo = await fetchTenantInfo(detectedTenantId);
          if (tenantInfo) {
            setTenantState(tenantInfo);
            
            // Apply tenant theme if available
            if (tenantInfo.theme) {
              applyTenantTheme(tenantInfo);
            }
          }
        }
      }
    };

    window.addEventListener('popstate', handleHostnameChange);
    return () => window.removeEventListener('popstate', handleHostnameChange);
  }, [tenantId]);

  return (
    <TenantContext.Provider value={{
      tenant,
      tenantId,
      isLoading,
      setTenant,
      detectTenant,
      clearTenant,
      fetchTenantInfo,
    }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant deve ser usado dentro de um TenantProvider');
  }
  return context;
}
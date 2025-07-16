'use client';

import { createContext, useContext, ReactNode, useState, useEffect } from 'react';
import { Tenant } from '@/types';
import { getCurrentTenant, getTenantFromHostname, setCurrentTenant } from '@/lib/tenant';

interface TenantContextType {
  tenant: Tenant | null;
  tenantId: string | null;
  isLoading: boolean;
  setTenant: (tenant: Tenant | null) => void;
  detectTenant: () => string | null;
}

const TenantContext = createContext<TenantContextType | null>(null);

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenantState] = useState<Tenant | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

  const setTenant = (newTenant: Tenant | null) => {
    setTenantState(newTenant);
    if (newTenant) {
      setTenantId(newTenant.subdomain);
      setCurrentTenant(newTenant.subdomain);
    } else {
      setTenantId(null);
    }
  };

  useEffect(() => {
    // Detect tenant on mount
    const detectedTenantId = detectTenant();
    setTenantId(detectedTenantId);
    setIsLoading(false);
  }, []);

  return (
    <TenantContext.Provider value={{
      tenant,
      tenantId,
      isLoading,
      setTenant,
      detectTenant,
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
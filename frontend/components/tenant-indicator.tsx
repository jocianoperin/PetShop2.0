'use client';

import { useTenant } from '@/contexts/TenantProvider';
import { Badge } from '@/components/ui/badge';
import { Building, CheckCircle, AlertCircle } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface TenantIndicatorProps {
  showDetails?: boolean; // Whether to show more details in the badge
  className?: string; // Additional CSS classes
}

/**
 * A component that displays the current tenant information
 * Useful for showing users which tenant they're currently working with
 */
export function TenantIndicator({ showDetails = false, className = '' }: TenantIndicatorProps) {
  const { tenant, tenantId, isLoading } = useTenant();

  if (isLoading) {
    return (
      <Badge variant="outline" className={`gap-1 px-2 py-1 rounded-lg ${className}`}>
        <Building className="h-3.5 w-3.5 text-gray-500" />
        <span className="text-xs text-gray-500">Carregando...</span>
      </Badge>
    );
  }

  if (!tenant || !tenantId) {
    return (
      <Badge variant="outline" className={`gap-1 px-2 py-1 rounded-lg border-red-200 ${className}`}>
        <AlertCircle className="h-3.5 w-3.5 text-red-500" />
        <span className="text-xs text-red-500">Sem tenant</span>
      </Badge>
    );
  }

  // Basic indicator with tooltip
  if (!showDetails) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className={`gap-1 px-2 py-1 rounded-lg border-green-200 ${className}`}>
              <CheckCircle className="h-3.5 w-3.5 text-green-500" />
              <span className="text-xs text-green-500">{tenant.name}</span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1 text-xs">
              <p><strong>Tenant:</strong> {tenant.name}</p>
              <p><strong>Subdomínio:</strong> {tenant.subdomain}</p>
              <p><strong>Plano:</strong> {tenant.plan_type || 'Básico'}</p>
              <p><strong>ID:</strong> {tenant.id}</p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Enhanced indicator with more details
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`gap-1 px-2 py-1 rounded-lg border-green-200 ${className}`}>
            <CheckCircle className="h-3.5 w-3.5 text-green-500" />
            <div className="flex flex-col">
              <span className="text-xs text-green-500">{tenant.name}</span>
              <span className="text-xs text-gray-500">{tenant.subdomain}</span>
            </div>
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1 text-xs">
            <p><strong>Tenant:</strong> {tenant.name}</p>
            <p><strong>Subdomínio:</strong> {tenant.subdomain}</p>
            <p><strong>Plano:</strong> {tenant.plan_type || 'Básico'}</p>
            <p><strong>ID:</strong> {tenant.id}</p>
            <p><strong>Status:</strong> {tenant.is_active ? 'Ativo' : 'Inativo'}</p>
            <p><strong>Criado em:</strong> {new Date(tenant.created_at).toLocaleDateString()}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
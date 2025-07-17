import { useState, useEffect, useCallback } from 'react';
import { useTenantData, useTenantCreate, useTenantUpdate, useTenantDelete } from './useTenantData';
import { useTenantApi } from './useTenantApi';
import { Agendamento } from '@/lib/api';

/**
 * Hook for managing agendamentos with tenant isolation
 */
export function useAgendamentos() {
  const tenantApi = useTenantApi();
  
  // Use tenant-aware data fetching
  const { 
    data: agendamentos, 
    isLoading, 
    error, 
    refresh 
  } = useTenantData(tenantApi.getAgendamentos, []);
  
  // Use tenant-aware create operation
  const { 
    create, 
    isCreating, 
    error: createError 
  } = useTenantCreate<Agendamento, Omit<Agendamento, 'id' | 'status'>>(tenantApi.createAgendamento);
  
  // Use tenant-aware update operation
  const { 
    update, 
    isUpdating, 
    error: updateError 
  } = useTenantUpdate<Agendamento, Partial<Agendamento>>(tenantApi.updateAgendamento);
  
  // Use tenant-aware delete operation
  const { 
    remove, 
    isDeleting, 
    error: deleteError 
  } = useTenantDelete(tenantApi.deleteAgendamento);
  
  return {
    agendamentos,
    isLoading,
    error,
    refresh,
    create,
    isCreating,
    createError,
    update,
    isUpdating,
    updateError,
    remove,
    isDeleting,
    deleteError
  };
}
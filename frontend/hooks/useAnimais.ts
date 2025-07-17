import { useState, useEffect, useCallback } from 'react';
import { useTenantData, useTenantCreate, useTenantUpdate, useTenantDelete } from './useTenantData';
import { useTenantApi } from './useTenantApi';
import { Animal } from '@/lib/api';

/**
 * Hook for managing animais with tenant isolation
 */
export function useAnimais() {
  const tenantApi = useTenantApi();
  
  // Use tenant-aware data fetching
  const { 
    data: animais, 
    isLoading, 
    error, 
    refresh 
  } = useTenantData(tenantApi.getAnimais, []);
  
  // Use tenant-aware create operation
  const { 
    create, 
    isCreating, 
    error: createError 
  } = useTenantCreate<Animal, Omit<Animal, 'id'>>(tenantApi.createAnimal);
  
  // Use tenant-aware update operation
  const { 
    update, 
    isUpdating, 
    error: updateError 
  } = useTenantUpdate<Animal, Partial<Animal>>(tenantApi.updateAnimal);
  
  // Use tenant-aware delete operation
  const { 
    remove, 
    isDeleting, 
    error: deleteError 
  } = useTenantDelete(tenantApi.deleteAnimal);
  
  // Custom function to get animals by cliente
  const getByCliente = useCallback(async (clienteId: number) => {
    try {
      return await tenantApi.getAnimaisByCliente(clienteId);
    } catch (error) {
      console.error('Error fetching animals by cliente:', error);
      throw error;
    }
  }, [tenantApi]);
  
  return {
    animais,
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
    deleteError,
    getByCliente
  };
}
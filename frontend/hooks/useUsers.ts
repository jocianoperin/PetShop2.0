import { useState, useEffect, useCallback } from 'react';
import { useTenantData, useTenantCreate, useTenantUpdate, useTenantDelete } from './useTenantData';
import { useTenantApi } from './useTenantApi';
import { Usuario, CreateUserData } from '@/lib/api';

/**
 * Hook for managing users with tenant isolation
 */
export function useUsers() {
  const tenantApi = useTenantApi();
  
  // Use tenant-aware data fetching
  const { 
    data: users, 
    isLoading, 
    error, 
    refresh 
  } = useTenantData(tenantApi.getUsers, []);
  
  // Use tenant-aware create operation
  const { 
    create, 
    isCreating, 
    error: createError 
  } = useTenantCreate<Usuario, CreateUserData>(tenantApi.createUser);
  
  // Use tenant-aware update operation
  const { 
    update, 
    isUpdating, 
    error: updateError 
  } = useTenantUpdate<Usuario, Partial<CreateUserData>>(tenantApi.updateUser);
  
  // Use tenant-aware delete operation
  const { 
    remove, 
    isDeleting, 
    error: deleteError 
  } = useTenantDelete(tenantApi.deleteUser);
  
  return {
    users,
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
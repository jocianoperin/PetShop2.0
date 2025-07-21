import { renderHook } from '@testing-library/react-hooks';
import { useTenantValidation } from './useTenantValidation';
import { useTenant } from '@/contexts/TenantProvider';
import { useAuth } from '@/contexts/AuthProvider';
import { authService } from '@/services/api';

// Mock the hooks and services
jest.mock('@/contexts/TenantProvider');
jest.mock('@/contexts/AuthProvider');
jest.mock('@/services/api');

describe('useTenantValidation', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Default mock implementations
    (useTenant as jest.Mock).mockReturnValue({
      tenant: { id: 'tenant1', name: 'Tenant 1', is_active: true },
      tenantId: 'tenant1',
      isLoading: false
    });
    
    (useAuth as jest.Mock).mockReturnValue({
      user: { id: 1, permissions: ['view_pets', 'edit_pets'] },
      isAuthenticated: true,
      isLoading: false
    });
    
    (authService.validateTenant as jest.Mock).mockResolvedValue(true);
  });
  
  it('should validate tenant correctly', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useTenantValidation({ validateWithBackend: true })
    );
    
    // Initial state should be validating
    expect(result.current.isValidating).toBe(true);
    
    await waitForNextUpdate();
    
    // After validation, should be valid
    expect(result.current.isValid).toBe(true);
    expect(result.current.error).toBe(null);
  });
  
  it('should detect invalid tenant', async () => {
    // Mock tenant as inactive
    (useTenant as jest.Mock).mockReturnValue({
      tenant: { id: 'tenant1', name: 'Tenant 1', is_active: false },
      tenantId: 'tenant1',
      isLoading: false
    });
    
    const { result, waitForNextUpdate } = renderHook(() => 
      useTenantValidation()
    );
    
    await waitForNextUpdate();
    
    expect(result.current.isValid).toBe(false);
    expect(result.current.error).toBe('Tenant inválido ou inativo');
  });
  
  it('should validate data ownership correctly', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useTenantValidation()
    );
    
    await waitForNextUpdate();
    
    // Data with matching tenant_id should be valid
    expect(result.current.validateDataOwnership({ id: 1, name: 'Test', tenant_id: 'tenant1' })).toBe(true);
    
    // Data with different tenant_id should be invalid
    expect(result.current.validateDataOwnership({ id: 1, name: 'Test', tenant_id: 'tenant2' })).toBe(false);
    
    // Data without tenant_id should be valid (backward compatibility)
    expect(result.current.validateDataOwnership({ id: 1, name: 'Test' })).toBe(true);
    
    // Array of data should be validated item by item
    expect(result.current.validateDataOwnership([
      { id: 1, name: 'Test 1', tenant_id: 'tenant1' },
      { id: 2, name: 'Test 2', tenant_id: 'tenant1' }
    ])).toBe(true);
    
    // Array with any invalid item should be invalid
    expect(result.current.validateDataOwnership([
      { id: 1, name: 'Test 1', tenant_id: 'tenant1' },
      { id: 2, name: 'Test 2', tenant_id: 'tenant2' }
    ])).toBe(false);
  });
  
  it('should check permissions correctly', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useTenantValidation({ requiredPermissions: ['view_pets'] })
    );
    
    await waitForNextUpdate();
    
    // User has the required permission
    expect(result.current.hasPermissions).toBe(true);
    
    // Reset hook with a permission the user doesn't have
    const { result: result2, waitForNextUpdate: waitForNextUpdate2 } = renderHook(() => 
      useTenantValidation({ requiredPermissions: ['admin_access'] })
    );
    
    await waitForNextUpdate2();
    
    // User doesn't have the required permission
    expect(result2.current.hasPermissions).toBe(false);
  });
});
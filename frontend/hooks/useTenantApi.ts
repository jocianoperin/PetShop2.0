import { useCallback } from 'react';
import { useTenant } from '@/contexts/TenantProvider';
import { api } from '@/lib/api';
import { useTenantValidation } from './useTenantValidation';
import { toast } from '@/components/ui/use-toast';

/**
 * Custom hook that provides tenant-aware API methods
 * This ensures all API calls include the current tenant context
 * and validates data ownership
 */
export function useTenantApi() {
  const { tenant, tenantId } = useTenant();
  const { validateDataOwnership } = useTenantValidation();
  
  // Helper function to add tenant_id to data objects
  const addTenantToData = useCallback(<T extends Record<string, any>>(data: T): T => {
    if (!tenantId) return data;
    
    // Add tenant_id to the data if it doesn't already have one
    return {
      ...data,
      tenant_id: data.tenant_id || tenantId
    };
  }, [tenantId]);
  
  // Helper function to validate response data belongs to current tenant
  const validateResponse = useCallback(<T extends { tenant_id?: string }>(data: T | T[]): T | T[] => {
    if (!validateDataOwnership(data)) {
      console.error('Data validation failed: tenant mismatch');
      toast({
        title: "Erro de validação",
        description: "Os dados recebidos não pertencem ao tenant atual.",
        variant: "destructive"
      });
      throw new Error('Tenant data validation failed');
    }
    return data;
  }, [validateDataOwnership]);
  
  // Clients (Clientes)
  const getClientes = useCallback(async () => {
    const data = await api.getClientes(tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const getCliente = useCallback(async (id: number) => {
    const data = await api.getCliente(id, tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const createCliente = useCallback(async (data: Omit<any, 'id'>) => {
    const tenantData = addTenantToData(data);
    const response = await api.createCliente(tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const updateCliente = useCallback(async (id: number, data: Partial<any>) => {
    const tenantData = addTenantToData(data);
    const response = await api.updateCliente(id, tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const deleteCliente = useCallback(async (id: number) => {
    return api.deleteCliente(id, tenantId || undefined);
  }, [tenantId]);
  
  // Animals (Animais)
  const getAnimais = useCallback(async () => {
    const data = await api.getAnimais(tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const getAnimal = useCallback(async (id: number) => {
    const data = await api.getAnimal(id, tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const getAnimaisByCliente = useCallback(async (clienteId: number) => {
    const data = await api.getAnimaisByCliente(clienteId, tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const createAnimal = useCallback(async (data: Omit<any, 'id'>) => {
    const tenantData = addTenantToData(data);
    const response = await api.createAnimal(tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const updateAnimal = useCallback(async (id: number, data: Partial<any>) => {
    const tenantData = addTenantToData(data);
    const response = await api.updateAnimal(id, tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const deleteAnimal = useCallback(async (id: number) => {
    return api.deleteAnimal(id, tenantId || undefined);
  }, [tenantId]);
  
  // Services (Serviços)
  const getServicos = useCallback(async () => {
    const data = await api.getServicos(tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const getServico = useCallback(async (id: number) => {
    const data = await api.getServico(id, tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const createServico = useCallback(async (data: Omit<any, 'id'>) => {
    const tenantData = addTenantToData(data);
    const response = await api.createServico(tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const updateServico = useCallback(async (id: number, data: Partial<any>) => {
    const tenantData = addTenantToData(data);
    const response = await api.updateServico(id, tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const deleteServico = useCallback(async (id: number) => {
    return api.deleteServico(id, tenantId || undefined);
  }, [tenantId]);
  
  // Appointments (Agendamentos)
  const getAgendamentos = useCallback(async () => {
    const data = await api.getAgendamentos(tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const getAgendamento = useCallback(async (id: number) => {
    const data = await api.getAgendamento(id, tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const createAgendamento = useCallback(async (data: Omit<any, 'id' | 'status'>) => {
    const tenantData = addTenantToData(data);
    const response = await api.createAgendamento(tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const updateAgendamento = useCallback(async (id: number, data: Partial<any>) => {
    const tenantData = addTenantToData(data);
    const response = await api.updateAgendamento(id, tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const deleteAgendamento = useCallback(async (id: number) => {
    return api.deleteAgendamento(id, tenantId || undefined);
  }, [tenantId]);
  
  // Lodging (Hospedagens)
  const getHospedagens = useCallback(async () => {
    const data = await api.getHospedagens(tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const getHospedagem = useCallback(async (id: number) => {
    const data = await api.getHospedagem(id, tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const createHospedagem = useCallback(async (data: Omit<any, 'id' | 'status'>) => {
    const tenantData = addTenantToData(data);
    const response = await api.createHospedagem(tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const updateHospedagem = useCallback(async (id: number, data: Partial<any>) => {
    const tenantData = addTenantToData(data);
    const response = await api.updateHospedagem(id, tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const deleteHospedagem = useCallback(async (id: number) => {
    return api.deleteHospedagem(id, tenantId || undefined);
  }, [tenantId]);
  
  // Financial entries (Lançamentos)
  const getLancamentos = useCallback(async () => {
    const data = await api.getLancamentos(tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const getLancamento = useCallback(async (id: number) => {
    const data = await api.getLancamento(id, tenantId || undefined);
    return validateResponse(data);
  }, [tenantId, validateResponse]);
  
  const createLancamento = useCallback(async (data: Omit<any, 'id'>) => {
    const tenantData = addTenantToData(data);
    const response = await api.createLancamento(tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const updateLancamento = useCallback(async (id: number, data: Partial<any>) => {
    const tenantData = addTenantToData(data);
    const response = await api.updateLancamento(id, tenantData, tenantId || undefined);
    return validateResponse(response);
  }, [tenantId, addTenantToData, validateResponse]);
  
  const deleteLancamento = useCallback(async (id: number) => {
    return api.deleteLancamento(id, tenantId || undefined);
  }, [tenantId]);
  
  // Tenant configuration
  const getTenantConfig = useCallback(async () => {
    const data = await api.getTenantConfig(tenantId || undefined);
    return data; // No validation needed for tenant config
  }, [tenantId]);
  
  const updateTenantConfig = useCallback(async (data: any) => {
    const response = await api.updateTenantConfig(data, tenantId || undefined);
    return response; // No validation needed for tenant config
  }, [tenantId]);
  
  return {
    // Tenant info
    tenant,
    tenantId,
    
    // Helper functions
    addTenantToData,
    validateResponse,
    
    // Clients
    getClientes,
    getCliente,
    createCliente,
    updateCliente,
    deleteCliente,
    
    // Animals
    getAnimais,
    getAnimal,
    getAnimaisByCliente,
    createAnimal,
    updateAnimal,
    deleteAnimal,
    
    // Services
    getServicos,
    getServico,
    createServico,
    updateServico,
    deleteServico,
    
    // Appointments
    getAgendamentos,
    getAgendamento,
    createAgendamento,
    updateAgendamento,
    deleteAgendamento,
    
    // Lodging
    getHospedagens,
    getHospedagem,
    createHospedagem,
    updateHospedagem,
    deleteHospedagem,
    
    // Financial entries
    getLancamentos,
    getLancamento,
    createLancamento,
    updateLancamento,
    deleteLancamento,
    
    // Tenant configuration
    getTenantConfig,
    updateTenantConfig,
  };
}
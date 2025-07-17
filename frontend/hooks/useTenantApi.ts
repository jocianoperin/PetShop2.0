import { useCallback } from 'react';
import { useTenant } from '@/contexts/TenantProvider';
import { api } from '@/lib/api';

/**
 * Custom hook that provides tenant-aware API methods
 * This ensures all API calls include the current tenant context
 */
export function useTenantApi() {
  const { tenantId } = useTenant();
  
  // Clients (Clientes)
  const getClientes = useCallback(() => {
    return api.getClientes(tenantId || undefined);
  }, [tenantId]);
  
  const getCliente = useCallback((id: number) => {
    return api.getCliente(id, tenantId || undefined);
  }, [tenantId]);
  
  const createCliente = useCallback((data: Omit<any, 'id'>) => {
    return api.createCliente(data, tenantId || undefined);
  }, [tenantId]);
  
  const updateCliente = useCallback((id: number, data: Partial<any>) => {
    return api.updateCliente(id, data, tenantId || undefined);
  }, [tenantId]);
  
  const deleteCliente = useCallback((id: number) => {
    return api.deleteCliente(id, tenantId || undefined);
  }, [tenantId]);
  
  // Animals (Animais)
  const getAnimais = useCallback(() => {
    return api.getAnimais(tenantId || undefined);
  }, [tenantId]);
  
  const getAnimal = useCallback((id: number) => {
    return api.getAnimal(id, tenantId || undefined);
  }, [tenantId]);
  
  const getAnimaisByCliente = useCallback((clienteId: number) => {
    return api.getAnimaisByCliente(clienteId, tenantId || undefined);
  }, [tenantId]);
  
  const createAnimal = useCallback((data: Omit<any, 'id'>) => {
    return api.createAnimal(data, tenantId || undefined);
  }, [tenantId]);
  
  const updateAnimal = useCallback((id: number, data: Partial<any>) => {
    return api.updateAnimal(id, data, tenantId || undefined);
  }, [tenantId]);
  
  const deleteAnimal = useCallback((id: number) => {
    return api.deleteAnimal(id, tenantId || undefined);
  }, [tenantId]);
  
  // Services (Serviços)
  const getServicos = useCallback(() => {
    return api.getServicos(tenantId || undefined);
  }, [tenantId]);
  
  const getServico = useCallback((id: number) => {
    return api.getServico(id, tenantId || undefined);
  }, [tenantId]);
  
  const createServico = useCallback((data: Omit<any, 'id'>) => {
    return api.createServico(data, tenantId || undefined);
  }, [tenantId]);
  
  const updateServico = useCallback((id: number, data: Partial<any>) => {
    return api.updateServico(id, data, tenantId || undefined);
  }, [tenantId]);
  
  const deleteServico = useCallback((id: number) => {
    return api.deleteServico(id, tenantId || undefined);
  }, [tenantId]);
  
  // Appointments (Agendamentos)
  const getAgendamentos = useCallback(() => {
    return api.getAgendamentos(tenantId || undefined);
  }, [tenantId]);
  
  const getAgendamento = useCallback((id: number) => {
    return api.getAgendamento(id, tenantId || undefined);
  }, [tenantId]);
  
  const createAgendamento = useCallback((data: Omit<any, 'id' | 'status'>) => {
    return api.createAgendamento(data, tenantId || undefined);
  }, [tenantId]);
  
  const updateAgendamento = useCallback((id: number, data: Partial<any>) => {
    return api.updateAgendamento(id, data, tenantId || undefined);
  }, [tenantId]);
  
  const deleteAgendamento = useCallback((id: number) => {
    return api.deleteAgendamento(id, tenantId || undefined);
  }, [tenantId]);
  
  // Lodging (Hospedagens)
  const getHospedagens = useCallback(() => {
    return api.getHospedagens(tenantId || undefined);
  }, [tenantId]);
  
  const getHospedagem = useCallback((id: number) => {
    return api.getHospedagem(id, tenantId || undefined);
  }, [tenantId]);
  
  const createHospedagem = useCallback((data: Omit<any, 'id' | 'status'>) => {
    return api.createHospedagem(data, tenantId || undefined);
  }, [tenantId]);
  
  const updateHospedagem = useCallback((id: number, data: Partial<any>) => {
    return api.updateHospedagem(id, data, tenantId || undefined);
  }, [tenantId]);
  
  const deleteHospedagem = useCallback((id: number) => {
    return api.deleteHospedagem(id, tenantId || undefined);
  }, [tenantId]);
  
  // Financial entries (Lançamentos)
  const getLancamentos = useCallback(() => {
    return api.getLancamentos(tenantId || undefined);
  }, [tenantId]);
  
  const getLancamento = useCallback((id: number) => {
    return api.getLancamento(id, tenantId || undefined);
  }, [tenantId]);
  
  const createLancamento = useCallback((data: Omit<any, 'id'>) => {
    return api.createLancamento(data, tenantId || undefined);
  }, [tenantId]);
  
  const updateLancamento = useCallback((id: number, data: Partial<any>) => {
    return api.updateLancamento(id, data, tenantId || undefined);
  }, [tenantId]);
  
  const deleteLancamento = useCallback((id: number) => {
    return api.deleteLancamento(id, tenantId || undefined);
  }, [tenantId]);
  
  // Tenant configuration
  const getTenantConfig = useCallback(() => {
    return api.getTenantConfig(tenantId || undefined);
  }, [tenantId]);
  
  const updateTenantConfig = useCallback((data: any) => {
    return api.updateTenantConfig(data, tenantId || undefined);
  }, [tenantId]);
  
  return {
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
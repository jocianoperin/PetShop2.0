import { API_ENDPOINTS } from '@/config/api';
import { ApiClient } from './api';
import { getCurrentTenant } from '@/lib/tenant';

export interface Pet {
  id: number;
  nome: string;
  foto?: string;
  especie: string;
  raca: string;
  porte: string;
  sexo: string;
  nascimento: string;
  peso: string;
  cor: string;
  tutorId: number;
  tutorNome: string;
  tutorTelefone: string;
  tutorEmail: string;
  endereco: string;
  observacoes?: string;
  status: string;
  tenant_id?: string; // Add tenant_id field to track ownership
}

export interface Vacina {
  id: number;
  petId: number;
  nome: string;
  dataAplicacao: string;
  dataVencimento: string;
  veterinario: string;
  lote: string;
  status: string;
  tenant_id?: string; // Add tenant_id field to track ownership
}

export interface HistoricoServico {
  id: number;
  petId: number;
  data: string;
  tipo: string;
  descricao: string;
  profissional: string;
  valor: number;
  observacoes?: string;
  tenant_id?: string; // Add tenant_id field to track ownership
}

// Use API_ENDPOINTS from config
const API_BASE_URL = API_ENDPOINTS.BASE_URL || 'http://127.0.0.1:8000/api';

const PET_ENDPOINTS = {
  LIST: `${API_BASE_URL}/pets/`,
  DETAIL: (id: number) => `${API_BASE_URL}/pets/${id}/`,
  VACINAS: (petId: number) => `${API_BASE_URL}/pets/${petId}/vacinas/`,
  HISTORICO: (petId: number) => `${API_BASE_URL}/pets/${petId}/historico/`,
  CREATE: `${API_BASE_URL}/pets/`,
  UPDATE: (id: number) => `${API_BASE_URL}/pets/${id}/`,
  DELETE: (id: number) => `${API_BASE_URL}/pets/${id}/`,
};

export class PetsService {
  static async getPets(token: string, customTenantId?: string): Promise<Pet[]> {
    // Use the tenant from context or the custom tenant ID if provided
    const tenantId = customTenantId || getCurrentTenant();
    return ApiClient.get<Pet[]>(PET_ENDPOINTS.LIST, token, tenantId);
  }

  static async getPet(id: number, token: string, customTenantId?: string): Promise<Pet> {
    const tenantId = customTenantId || getCurrentTenant();
    return ApiClient.get<Pet>(PET_ENDPOINTS.DETAIL(id), token, tenantId);
  }

  static async getVacinas(petId: number, token: string, customTenantId?: string): Promise<Vacina[]> {
    const tenantId = customTenantId || getCurrentTenant();
    return ApiClient.get<Vacina[]>(PET_ENDPOINTS.VACINAS(petId), token, tenantId);
  }

  static async getHistorico(petId: number, token: string, customTenantId?: string): Promise<HistoricoServico[]> {
    const tenantId = customTenantId || getCurrentTenant();
    return ApiClient.get<HistoricoServico[]>(PET_ENDPOINTS.HISTORICO(petId), token, tenantId);
  }

  static async createPet(petData: Partial<Pet>, token: string, customTenantId?: string): Promise<Pet> {
    const tenantId = customTenantId || getCurrentTenant();
    // Ensure the pet is associated with the current tenant
    const petWithTenant = {
      ...petData,
      tenant_id: tenantId
    };
    return ApiClient.post<Pet>(PET_ENDPOINTS.CREATE, petWithTenant, token, tenantId);
  }

  static async updatePet(id: number, petData: Partial<Pet>, token: string, customTenantId?: string): Promise<Pet> {
    const tenantId = customTenantId || getCurrentTenant();
    // Ensure the pet is associated with the current tenant
    const petWithTenant = {
      ...petData,
      tenant_id: tenantId
    };
    return ApiClient.put<Pet>(PET_ENDPOINTS.UPDATE(id), petWithTenant, token, tenantId);
  }

  static async deletePet(id: number, token: string, customTenantId?: string): Promise<void> {
    const tenantId = customTenantId || getCurrentTenant();
    return ApiClient.delete<void>(PET_ENDPOINTS.DELETE(id), token, tenantId);
  }
  
  // Validate if a pet belongs to the current tenant
  static validatePetTenant(pet: Pet, tenantId?: string): boolean {
    const currentTenant = tenantId || getCurrentTenant();
    // If pet has tenant_id, check if it matches current tenant
    // If pet doesn't have tenant_id, assume it's valid (for backward compatibility)
    return !pet.tenant_id || pet.tenant_id === currentTenant;
  }
}

export const petsService = {
  getPets: PetsService.getPets,
  getPet: PetsService.getPet,
  getVacinas: PetsService.getVacinas,
  getHistorico: PetsService.getHistorico,
  createPet: PetsService.createPet,
  updatePet: PetsService.updatePet,
  deletePet: PetsService.deletePet,
};

export default petsService;
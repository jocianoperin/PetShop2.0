import { API_ENDPOINTS } from '@/config/api';
import { ApiClient } from './api';
import { getCurrentTenant, getTenantHeaders } from '@/lib/tenant';

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
  /**
   * Get all pets for the current tenant
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns List of pets for the tenant
   */
  static async getPets(token?: string, customTenantId?: string): Promise<Pet[]> {
    // Use the tenant from context or the custom tenant ID if provided
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to fetch pets");
    }
    
    const pets = await ApiClient.get<Pet[]>(PET_ENDPOINTS.LIST, token, tenantId);
    
    // Filter pets to ensure they belong to the current tenant
    return pets.filter(pet => PetsService.validatePetTenant(pet, tenantId));
  }

  /**
   * Get a specific pet by ID
   * @param id Pet ID
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns Pet details
   */
  static async getPet(id: number, token?: string, customTenantId?: string): Promise<Pet> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to fetch pet details");
    }
    
    const pet = await ApiClient.get<Pet>(PET_ENDPOINTS.DETAIL(id), token, tenantId);
    
    // Validate that the pet belongs to the current tenant
    if (!PetsService.validatePetTenant(pet, tenantId)) {
      throw new Error(`Pet with ID ${id} does not belong to the current tenant`);
    }
    
    return pet;
  }

  /**
   * Get all vaccines for a specific pet
   * @param petId Pet ID
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns List of vaccines
   */
  static async getVacinas(petId: number, token?: string, customTenantId?: string): Promise<Vacina[]> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to fetch pet vaccines");
    }
    
    // First verify that the pet belongs to the current tenant
    try {
      await PetsService.getPet(petId, token, tenantId);
    } catch (error) {
      throw new Error(`Cannot fetch vaccines: Pet with ID ${petId} does not belong to the current tenant`);
    }
    
    const vacinas = await ApiClient.get<Vacina[]>(PET_ENDPOINTS.VACINAS(petId), token, tenantId);
    
    // Filter vaccines to ensure they belong to the current tenant
    return vacinas.filter(vacina => !vacina.tenant_id || vacina.tenant_id === tenantId);
  }

  /**
   * Get service history for a specific pet
   * @param petId Pet ID
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns List of service history entries
   */
  static async getHistorico(petId: number, token?: string, customTenantId?: string): Promise<HistoricoServico[]> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to fetch pet history");
    }
    
    // First verify that the pet belongs to the current tenant
    try {
      await PetsService.getPet(petId, token, tenantId);
    } catch (error) {
      throw new Error(`Cannot fetch history: Pet with ID ${petId} does not belong to the current tenant`);
    }
    
    const historico = await ApiClient.get<HistoricoServico[]>(PET_ENDPOINTS.HISTORICO(petId), token, tenantId);
    
    // Filter history entries to ensure they belong to the current tenant
    return historico.filter(entry => !entry.tenant_id || entry.tenant_id === tenantId);
  }

  /**
   * Create a new pet
   * @param petData Pet data
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns Created pet
   */
  static async createPet(petData: Partial<Pet>, token?: string, customTenantId?: string): Promise<Pet> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to create a pet");
    }
    
    // Always ensure the pet is associated with the current tenant
    const petWithTenant = {
      ...petData,
      tenant_id: tenantId
    };
    
    return ApiClient.post<Pet>(PET_ENDPOINTS.CREATE, petWithTenant, token, tenantId);
  }

  /**
   * Update an existing pet
   * @param id Pet ID
   * @param petData Updated pet data
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   * @returns Updated pet
   */
  static async updatePet(id: number, petData: Partial<Pet>, token?: string, customTenantId?: string): Promise<Pet> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to update a pet");
    }
    
    // First verify that the pet belongs to the current tenant
    try {
      await PetsService.getPet(id, token, tenantId);
    } catch (error) {
      throw new Error(`Cannot update: Pet with ID ${id} does not belong to the current tenant`);
    }
    
    // Ensure the pet is associated with the current tenant
    const petWithTenant = {
      ...petData,
      tenant_id: tenantId
    };
    
    return ApiClient.put<Pet>(PET_ENDPOINTS.UPDATE(id), petWithTenant, token, tenantId);
  }

  /**
   * Delete a pet
   * @param id Pet ID
   * @param token Auth token (optional)
   * @param customTenantId Optional tenant ID override
   */
  static async deletePet(id: number, token?: string, customTenantId?: string): Promise<void> {
    const tenantId = customTenantId || getCurrentTenant();
    
    if (!tenantId) {
      throw new Error("Tenant ID is required to delete a pet");
    }
    
    // First verify that the pet belongs to the current tenant
    try {
      await PetsService.getPet(id, token, tenantId);
    } catch (error) {
      throw new Error(`Cannot delete: Pet with ID ${id} does not belong to the current tenant`);
    }
    
    return ApiClient.delete<void>(PET_ENDPOINTS.DELETE(id), token, tenantId);
  }
  
  /**
   * Validate if a pet belongs to the current tenant
   * @param pet Pet object
   * @param tenantId Optional tenant ID override
   * @returns Boolean indicating if the pet belongs to the tenant
   */
  static validatePetTenant(pet: Pet, tenantId?: string): boolean {
    const currentTenant = tenantId || getCurrentTenant();
    
    if (!currentTenant) {
      return false;
    }
    
    // If pet has tenant_id, check if it matches current tenant
    // If pet doesn't have tenant_id, assume it's valid (for backward compatibility)
    return !pet.tenant_id || pet.tenant_id === currentTenant;
  }
  
  /**
   * Validate if multiple pets belong to the current tenant
   * @param pets Array of pet objects
   * @param tenantId Optional tenant ID override
   * @returns Boolean indicating if all pets belong to the tenant
   */
  static validateMultiplePetsTenant(pets: Pet[], tenantId?: string): boolean {
    return pets.every(pet => PetsService.validatePetTenant(pet, tenantId));
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
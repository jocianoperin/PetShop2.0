import { API_ENDPOINTS } from '@/config/api';
import { ApiClient } from './api';

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
}

// Add API endpoints for pets
const API_BASE_URL = 'http://127.0.0.1:8000/api';

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
  static async getPets(token: string): Promise<Pet[]> {
    return ApiClient.get<Pet[]>(PET_ENDPOINTS.LIST, token);
  }

  static async getPet(id: number, token: string): Promise<Pet> {
    return ApiClient.get<Pet>(PET_ENDPOINTS.DETAIL(id), token);
  }

  static async getVacinas(petId: number, token: string): Promise<Vacina[]> {
    return ApiClient.get<Vacina[]>(PET_ENDPOINTS.VACINAS(petId), token);
  }

  static async getHistorico(petId: number, token: string): Promise<HistoricoServico[]> {
    return ApiClient.get<HistoricoServico[]>(PET_ENDPOINTS.HISTORICO(petId), token);
  }

  static async createPet(petData: Partial<Pet>, token: string): Promise<Pet> {
    return ApiClient.post<Pet>(PET_ENDPOINTS.CREATE, petData, token);
  }

  static async updatePet(id: number, petData: Partial<Pet>, token: string): Promise<Pet> {
    return ApiClient.put<Pet>(PET_ENDPOINTS.UPDATE(id), petData, token);
  }

  static async deletePet(id: number, token: string): Promise<void> {
    return ApiClient.delete<void>(PET_ENDPOINTS.DELETE(id), token);
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
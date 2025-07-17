const API_BASE_URL = 'http://localhost:8000/api';

// Interfaces para autenticação
export interface Usuario {
  id?: number;
  username: string;
  email: string;
  nome: string;
  is_admin: boolean;
  ativo: boolean;
  tenant?: {
    id: string;
    name: string;
    subdomain: string;
    schema_name: string;
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: Usuario;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  nome: string;
  is_admin: boolean;
}

// Interfaces para tipagem
export interface Cliente {
  id?: number;
  nome: string;
  email: string;
  telefone: string;
  endereco: string;
}

export interface Animal {
  id?: number;
  nome: string;
  especie: string;
  raca: string;
  idade: number;
  tutor: number; // ID do tutor
}

export interface Servico {
  id: number;
  nome: string;
  descricao: string;
  valor: number;
  duracao: number; // em minutos
}

export interface Agendamento {
  id?: number;
  pet: number; // ID do pet
  servico: number; // ID do serviço
  data_hora: string;
  status: 'agendado' | 'concluido' | 'cancelado';
  observacoes?: string;
}

export interface Hospedagem {
  id?: number;
  pet: number; // ID do pet
  check_in: string;
  check_out: string;
  box: number; // ID do box
  status: 'reservado' | 'ativo' | 'concluido' | 'cancelado';
  observacoes?: string;
  valor_diaria: number;
}

export interface Lancamento {
  id?: number;
  tipo: 'receita' | 'despesa';
  descricao: string;
  valor: number;
  data: string;
  categoria: string;
  observacoes?: string;
}

import { getCurrentTenant, getTenantHeaders } from './tenant';

// Função para tratamento de erros HTTP
async function handleResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    // Check for tenant-specific errors
    if (response.status === 404 && data.code === 'TENANT_NOT_FOUND') {
      throw new Error(`Tenant não encontrado: ${getCurrentTenant()}`);
    }
    
    if (response.status === 403 && data.code === 'TENANT_INACTIVE') {
      throw new Error(`Tenant inativo ou suspenso: ${getCurrentTenant()}`);
    }
    
    const error = new Error(data.message || data.detail || 'Erro na requisição');
    (error as any).response = data;
    throw error;
  }
  return data as T;
}

// Função para armazenar o token JWT
const setAuthToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('authToken', token);
  }
};

// Função para obter o token JWT
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken');
  }
  return null;
};

// Função para adicionar o token de autenticação e tenant nas requisições
const authFetch = async (url: string, options: RequestInit = {}, customTenantId?: string) => {
  const token = getAuthToken();
  const headers = new Headers(options.headers);
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  // Add tenant headers
  const tenantHeaders = customTenantId 
    ? { 'X-Tenant-ID': customTenantId }
    : getTenantHeaders();
    
  Object.entries(tenantHeaders).forEach(([key, value]) => {
    headers.set(key, value);
  });
  
  return fetch(url, {
    ...options,
    headers,
  });
};

export const api = {
  // Clientes
  getClientes: async (customTenantId?: string): Promise<Cliente[]> => {
    const response = await authFetch(`${API_BASE_URL}/clientes/`, {}, customTenantId);
    return handleResponse<Cliente[]>(response);
  },
  
  getCliente: async (id: number, customTenantId?: string): Promise<Cliente> => {
    const response = await authFetch(`${API_BASE_URL}/clientes/${id}/`, {}, customTenantId);
    return handleResponse<Cliente>(response);
  },
  
  createCliente: async (data: Omit<Cliente, 'id'>, customTenantId?: string): Promise<Cliente> => {
    const response = await authFetch(`${API_BASE_URL}/clientes/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Cliente>(response);
  },
  
  updateCliente: async (id: number, data: Partial<Cliente>, customTenantId?: string): Promise<Cliente> => {
    const response = await authFetch(`${API_BASE_URL}/clientes/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Cliente>(response);
  },
  
  deleteCliente: async (id: number, customTenantId?: string): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/clientes/${id}/`, {
      method: 'DELETE',
    }, customTenantId);
    if (!response.ok) {
      throw new Error('Falha ao excluir cliente');
    }
  },
  
  // Animais
  getAnimais: async (customTenantId?: string): Promise<Animal[]> => {
    const response = await authFetch(`${API_BASE_URL}/animais/`, {}, customTenantId);
    return handleResponse<Animal[]>(response);
  },
  
  getAnimal: async (id: number, customTenantId?: string): Promise<Animal> => {
    const response = await authFetch(`${API_BASE_URL}/animais/${id}/`, {}, customTenantId);
    return handleResponse<Animal>(response);
  },
  
  getAnimaisByCliente: async (clienteId: number, customTenantId?: string): Promise<Animal[]> => {
    const response = await authFetch(`${API_BASE_URL}/animais/?tutor=${clienteId}`, {}, customTenantId);
    return handleResponse<Animal[]>(response);
  },
  
  createAnimal: async (data: Omit<Animal, 'id'>, customTenantId?: string): Promise<Animal> => {
    const response = await authFetch(`${API_BASE_URL}/animais/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Animal>(response);
  },
  
  updateAnimal: async (id: number, data: Partial<Animal>, customTenantId?: string): Promise<Animal> => {
    const response = await authFetch(`${API_BASE_URL}/animais/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Animal>(response);
  },
  
  deleteAnimal: async (id: number, customTenantId?: string): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/animais/${id}/`, {
      method: 'DELETE',
    }, customTenantId);
    if (!response.ok) {
      throw new Error('Falha ao excluir animal');
    }
  },
  
  // Serviços
  getServicos: async (customTenantId?: string): Promise<Servico[]> => {
    const response = await authFetch(`${API_BASE_URL}/servicos/`, {}, customTenantId);
    return handleResponse<Servico[]>(response);
  },
  
  getServico: async (id: number, customTenantId?: string): Promise<Servico> => {
    const response = await authFetch(`${API_BASE_URL}/servicos/${id}/`, {}, customTenantId);
    return handleResponse<Servico>(response);
  },
  
  createServico: async (data: Omit<Servico, 'id'>, customTenantId?: string): Promise<Servico> => {
    const response = await authFetch(`${API_BASE_URL}/servicos/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Servico>(response);
  },
  
  updateServico: async (id: number, data: Partial<Servico>, customTenantId?: string): Promise<Servico> => {
    const response = await authFetch(`${API_BASE_URL}/servicos/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Servico>(response);
  },
  
  deleteServico: async (id: number, customTenantId?: string): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/servicos/${id}/`, {
      method: 'DELETE',
    }, customTenantId);
    if (!response.ok) {
      throw new Error('Falha ao excluir serviço');
    }
  },
  
  // Agendamentos
  getAgendamentos: async (customTenantId?: string) => {
    const response = await authFetch(`${API_BASE_URL}/agendamentos/`, {}, customTenantId);
    return handleResponse<any[]>(response);
  },
  
  getAgendamento: async (id: number, customTenantId?: string): Promise<Agendamento> => {
    const response = await authFetch(`${API_BASE_URL}/agendamentos/${id}/`, {}, customTenantId);
    return handleResponse<Agendamento>(response);
  },
  
  createAgendamento: async (data: Omit<Agendamento, 'id' | 'status'>, customTenantId?: string): Promise<Agendamento> => {
    const response = await authFetch(`${API_BASE_URL}/agendamentos/`, {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        status: 'agendado' as const
      }),
    }, customTenantId);
    return handleResponse<Agendamento>(response);
  },
  
  updateAgendamento: async (id: number, data: Partial<Agendamento>, customTenantId?: string): Promise<Agendamento> => {
    const response = await authFetch(`${API_BASE_URL}/agendamentos/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Agendamento>(response);
  },
  
  deleteAgendamento: async (id: number, customTenantId?: string): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/agendamentos/${id}/`, {
      method: 'DELETE',
    }, customTenantId);
    if (!response.ok) {
      throw new Error('Falha ao excluir agendamento');
    }
  },
  
  // Hospedagens
  getHospedagens: async (customTenantId?: string): Promise<Hospedagem[]> => {
    const response = await authFetch(`${API_BASE_URL}/hospedagens/`, {}, customTenantId);
    return handleResponse<Hospedagem[]>(response);
  },
  
  getHospedagem: async (id: number, customTenantId?: string): Promise<Hospedagem> => {
    const response = await authFetch(`${API_BASE_URL}/hospedagens/${id}/`, {}, customTenantId);
    return handleResponse<Hospedagem>(response);
  },
  
  createHospedagem: async (data: Omit<Hospedagem, 'id' | 'status'>, customTenantId?: string): Promise<Hospedagem> => {
    const response = await authFetch(`${API_BASE_URL}/hospedagens/`, {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        status: 'reservado' as const
      }),
    }, customTenantId);
    return handleResponse<Hospedagem>(response);
  },
  
  updateHospedagem: async (id: number, data: Partial<Hospedagem>, customTenantId?: string): Promise<Hospedagem> => {
    const response = await authFetch(`${API_BASE_URL}/hospedagens/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Hospedagem>(response);
  },
  
  deleteHospedagem: async (id: number, customTenantId?: string): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/hospedagens/${id}/`, {
      method: 'DELETE',
    }, customTenantId);
    if (!response.ok) {
      throw new Error('Falha ao excluir hospedagem');
    }
  },
  
  // Lançamentos Financeiros
  getLancamentos: async (customTenantId?: string): Promise<Lancamento[]> => {
    const response = await authFetch(`${API_BASE_URL}/lancamentos/`, {}, customTenantId);
    return handleResponse<Lancamento[]>(response);
  },
  
  getLancamento: async (id: number, customTenantId?: string): Promise<Lancamento> => {
    const response = await authFetch(`${API_BASE_URL}/lancamentos/${id}/`, {}, customTenantId);
    return handleResponse<Lancamento>(response);
  },
  
  createLancamento: async (data: Omit<Lancamento, 'id'>, customTenantId?: string): Promise<Lancamento> => {
    const response = await authFetch(`${API_BASE_URL}/lancamentos/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Lancamento>(response);
  },
  
  updateLancamento: async (id: number, data: Partial<Lancamento>, customTenantId?: string): Promise<Lancamento> => {
    const response = await authFetch(`${API_BASE_URL}/lancamentos/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Lancamento>(response);
  },
  
  deleteLancamento: async (id: number, customTenantId?: string): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/lancamentos/${id}/`, {
      method: 'DELETE',
    }, customTenantId);
    if (!response.ok) {
      throw new Error('Falha ao excluir lançamento');
    }
  },

  // Autenticação
  login: async (data: LoginData & { tenant_id?: string }): Promise<AuthResponse> => {
    // Get tenant headers if tenant_id is provided
    const tenantHeaders = data.tenant_id ? { 'X-Tenant-ID': data.tenant_id } : getTenantHeaders();
    
    const headers = new Headers({
      'Content-Type': 'application/json',
    });
    
    // Add tenant headers
    Object.entries(tenantHeaders).forEach(([key, value]) => {
      headers.set(key, value);
    });
    
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    
    const authData = await handleResponse<AuthResponse>(response);
    setAuthToken(authData.access_token);
    
    // Store tenant information if available
    if (authData.user?.tenant) {
      // Import these functions dynamically to avoid circular dependencies
      const { storeTenantData, addRecentTenant } = await import('./tenant');
      storeTenantData(authData.user.tenant);
      addRecentTenant(authData.user.tenant);
    }
    
    return authData;
  },

  logout: (): void => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
  },

  getCurrentUser: async (customTenantId?: string): Promise<Usuario> => {
    const response = await authFetch(`${API_BASE_URL}/auth/me`, {}, customTenantId);
    const userData = await handleResponse<Usuario>(response);
    
    // Store tenant information if available
    if (userData.tenant) {
      // Import these functions dynamically to avoid circular dependencies
      const { storeTenantData, addRecentTenant } = await import('./tenant');
      storeTenantData(userData.tenant);
      addRecentTenant(userData.tenant);
    }
    
    return userData;
  },

  // Gerenciamento de usuários
  getUsers: async (customTenantId?: string): Promise<Usuario[]> => {
    const response = await authFetch(`${API_BASE_URL}/auth/users`, {}, customTenantId);
    return handleResponse<Usuario[]>(response);
  },

  createUser: async (data: CreateUserData, customTenantId?: string): Promise<Usuario> => {
    const response = await authFetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Usuario>(response);
  },

  updateUser: async (id: number, data: Partial<CreateUserData>, customTenantId?: string): Promise<Usuario> => {
    const response = await authFetch(`${API_BASE_URL}/auth/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<Usuario>(response);
  },

  deleteUser: async (id: number, customTenantId?: string): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/auth/users/${id}`, {
      method: 'DELETE',
    }, customTenantId);
    if (!response.ok) {
      throw new Error('Falha ao excluir usuário');
    }
  },
  
  // Tenant-specific operations
  getTenantInfo: async (tenantId: string): Promise<any> => {
    const response = await authFetch(`${API_BASE_URL}/tenants/${tenantId}`, {}, tenantId);
    return handleResponse<any>(response);
  },
  
  getTenantConfig: async (customTenantId?: string): Promise<any> => {
    const response = await authFetch(`${API_BASE_URL}/tenants/config`, {}, customTenantId);
    return handleResponse<any>(response);
  },
  
  updateTenantConfig: async (data: any, customTenantId?: string): Promise<any> => {
    const response = await authFetch(`${API_BASE_URL}/tenants/config`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, customTenantId);
    return handleResponse<any>(response);
  },
  
  validateTenant: async (tenantId: string): Promise<boolean> => {
    try {
      await api.getTenantInfo(tenantId);
      return true;
    } catch (error) {
      return false;
    }
  }
};

export default api;

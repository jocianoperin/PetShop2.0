const API_BASE_URL = 'http://localhost:8000/api';

// Interfaces para autenticação
export interface Usuario {
  id?: number;
  username: string;
  email: string;
  nome: string;
  is_admin: boolean;
  ativo: boolean;
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

// Função para tratamento de erros HTTP
async function handleResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.message || 'Erro na requisição');
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

// Função para adicionar o token de autenticação nas requisições
const authFetch = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  const headers = new Headers(options.headers);
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  return fetch(url, {
    ...options,
    headers,
  });
};

export const api = {
  // Clientes
  getClientes: async (): Promise<Cliente[]> => {
    const response = await authFetch(`${API_BASE_URL}/clientes/`);
    return handleResponse<Cliente[]>(response);
  },
  
  createCliente: async (data: Omit<Cliente, 'id'>): Promise<Cliente> => {
    const response = await authFetch(`${API_BASE_URL}/clientes/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return handleResponse<Cliente>(response);
  },
  
  // Animais
  getAnimais: async (): Promise<Animal[]> => {
    const response = await authFetch(`${API_BASE_URL}/animais/`);
    return handleResponse<Animal[]>(response);
  },
  
  createAnimal: async (data: Omit<Animal, 'id'>): Promise<Animal> => {
    const response = await authFetch(`${API_BASE_URL}/animais/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return handleResponse<Animal>(response);
  },
  
  // Serviços
  getServicos: async (): Promise<Servico[]> => {
    const response = await authFetch(`${API_BASE_URL}/servicos/`);
    return handleResponse<Servico[]>(response);
  },
  
  // Agendamentos
  getAgendamentos: async () => {
    const response = await authFetch(`${API_BASE_URL}/agendamentos/`);
    return handleResponse<any[]>(response);
  },
  
  createAgendamento: async (data: Omit<Agendamento, 'id' | 'status'>): Promise<Agendamento> => {
    const response = await authFetch(`${API_BASE_URL}/agendamentos/`, {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        status: 'agendado' as const
      }),
    });
    return handleResponse<Agendamento>(response);
  },
  
  // Hospedagens
  getHospedagens: async (): Promise<Hospedagem[]> => {
    const response = await authFetch(`${API_BASE_URL}/hospedagens/`);
    return handleResponse<Hospedagem[]>(response);
  },
  
  createHospedagem: async (data: Omit<Hospedagem, 'id' | 'status'>): Promise<Hospedagem> => {
    const response = await authFetch(`${API_BASE_URL}/hospedagens/`, {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        status: 'reservado' as const
      }),
    });
    return handleResponse<Hospedagem>(response);
  },
  
  // Lançamentos Financeiros
  getLancamentos: async (): Promise<Lancamento[]> => {
    const response = await authFetch(`${API_BASE_URL}/lancamentos/`);
    return handleResponse<Lancamento[]>(response);
  },
  
  createLancamento: async (data: Omit<Lancamento, 'id'>): Promise<Lancamento> => {
    const response = await authFetch(`${API_BASE_URL}/lancamentos/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return handleResponse<Lancamento>(response);
  },

  // Autenticação
  login: async (data: LoginData): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    const authData = await handleResponse<AuthResponse>(response);
    setAuthToken(authData.access_token);
    return authData;
  },

  logout: (): void => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
  },

  getCurrentUser: async (): Promise<Usuario> => {
    const response = await authFetch(`${API_BASE_URL}/auth/me`);
    return handleResponse<Usuario>(response);
  },

  // Gerenciamento de usuários
  getUsers: async (): Promise<Usuario[]> => {
    const response = await authFetch(`${API_BASE_URL}/auth/users`);
    return handleResponse<Usuario[]>(response);
  },

  createUser: async (data: CreateUserData): Promise<Usuario> => {
    const response = await authFetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return handleResponse<Usuario>(response);
  },

  updateUser: async (id: number, data: Partial<CreateUserData>): Promise<Usuario> => {
    const response = await authFetch(`${API_BASE_URL}/auth/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return handleResponse<Usuario>(response);
  },

  deleteUser: async (id: number): Promise<void> => {
    const response = await authFetch(`${API_BASE_URL}/auth/users/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Falha ao excluir usuário');
    }
  }
};

export default api;

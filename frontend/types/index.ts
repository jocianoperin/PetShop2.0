export interface User {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface CreateUserData extends LoginCredentials {
  email: string;
  is_staff?: boolean;
}

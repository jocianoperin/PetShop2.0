export interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  schema_name: string;
  is_active: boolean;
  plan_type: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  tenant?: Tenant;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
  tenant?: Tenant;
}

export interface LoginCredentials {
  username: string;
  password: string;
  tenant_id?: string;
}

export interface CreateUserData extends LoginCredentials {
  email: string;
  is_staff?: boolean;
}

export interface TenantRegistrationData {
  company_name: string;
  subdomain: string;
  admin_username: string;
  admin_email: string;
  admin_password: string;
}

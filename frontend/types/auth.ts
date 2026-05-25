export interface AuthUser {
  id: number;
  username: string;
  email: string;
  role: "user" | "admin" | "super_admin";
  status: "active" | "disabled";
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface MessageResponse {
  message: string;
}

export interface SendCodePayload {
  email: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  confirm_password: string;
  email: string;
  code: string;
}

export interface LoginPayload {
  username_or_email: string;
  password: string;
}

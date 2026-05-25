export type UserRole = "user" | "admin" | "super_admin";
export type UserStatus = "active" | "disabled";

export interface AdminUserListItem {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  last_login_at?: string | null;
}

export interface AdminUserDetail extends AdminUserListItem {
  updated_at: string;
}

export interface AdminUserListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AdminUserListItem[];
}

export interface AdminUserUpdatePayload {
  username?: string;
  email?: string;
  status?: UserStatus;
  role?: UserRole;
}

export interface AdminUserResetPasswordPayload {
  new_password: string;
}

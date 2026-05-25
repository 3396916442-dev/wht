import axios, { AxiosError } from "axios";

import { getAccessToken } from "@/lib/auth";
import type {
  AuthUser,
  LoginPayload,
  LoginResponse,
  MessageResponse,
  RegisterPayload,
  SendCodePayload,
} from "@/types/auth";

const AUTH_BASE_URL =
  process.env.NEXT_PUBLIC_AUTH_API_BASE_URL ?? "http://localhost:8000/api/auth";

export class AuthApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "AuthApiError";
  }
}

function toAuthError(error: unknown): AuthApiError {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
        ? detail.map((item) => item?.msg ?? JSON.stringify(item)).join("; ")
        : error.message;
    return new AuthApiError(error.response?.status ?? 500, message);
  }
  return new AuthApiError(500, String(error));
}

export const authClient = axios.create({
  baseURL: AUTH_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  timeout: 30000,
});

authClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  sendCode: async (payload: SendCodePayload): Promise<MessageResponse> => {
    try {
      const { data } = await authClient.post<MessageResponse>("/send-code", payload);
      return data;
    } catch (error) {
      throw toAuthError(error);
    }
  },

  register: async (payload: RegisterPayload): Promise<AuthUser> => {
    try {
      const { data } = await authClient.post<AuthUser>("/register", payload);
      return data;
    } catch (error) {
      throw toAuthError(error);
    }
  },

  login: async (payload: LoginPayload): Promise<LoginResponse> => {
    try {
      const { data } = await authClient.post<LoginResponse>("/login", payload);
      return data;
    } catch (error) {
      throw toAuthError(error);
    }
  },

  me: async (): Promise<AuthUser> => {
    try {
      const { data } = await authClient.get<AuthUser>("/me");
      return data;
    } catch (error) {
      throw toAuthError(error);
    }
  },
};

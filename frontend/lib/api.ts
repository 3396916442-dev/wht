// =====================================================================
// 类型化 API 客户端。
// 所有页面/组件统一从 `import { api } from "@/lib/api"` 调用，
// 不要在组件里手写 fetch / 拼字符串。
// =====================================================================

import type {
  ApiHealth,
  ApiRoot,
  BacktestDetailResponse,
  BacktestReport,
  BacktestTaskListResponse,
  DailyResponse,
  MaCrossRequest,
  SyncDailyRequest,
  SyncDailyResponse,
} from "@/types";
import type {
  AdminUserDetail,
  AdminUserListResponse,
  AdminUserResetPasswordPayload,
  AdminUserUpdatePayload,
} from "@/types/admin";
import { getAccessToken } from "@/lib/auth";

const RAW_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const ROOT_BASE_URL = RAW_BASE_URL.replace(/\/api\/v\d+\/?$/, "");
const API_BASE_URL = `${ROOT_BASE_URL}/api/v1`;

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public path: string,
  ) {
    super(`[${status}] ${path} → ${detail}`);
  }
}

async function http<T>(
  baseUrl: string,
  path: string,
  init?: RequestInit & { params?: Record<string, string | number | boolean | undefined | null> },
): Promise<T> {
  const url = new URL(baseUrl + path);
  if (init?.params) {
    for (const [k, v] of Object.entries(init.params)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
  }
  const { params, headers, ...rest } = init ?? {};
  const res = await fetch(url.toString(), {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(headers ?? {}),
    },
    cache: "no-store",
    ...rest,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail, path);
  }
  return (await res.json()) as T;
}

const apiHttp = <T>(path: string, init?: Parameters<typeof http>[2]) =>
  http<T>(API_BASE_URL, path, init);
const rootHttp = <T>(path: string, init?: Parameters<typeof http>[2]) =>
  http<T>(ROOT_BASE_URL, path, init);
const adminHttp = <T>(path: string, init?: Parameters<typeof http>[2]) => {
  const token = getAccessToken();
  return http<T>(ROOT_BASE_URL, path, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
};

// ---- 端点封装 --------------------------------------------------------

export const api = {
  // 元信息
  root: () => rootHttp<ApiRoot>("/"),
  health: () => rootHttp<ApiHealth>("/health"),

  // 股票 / 日线
  getDaily: (
    code: string,
    params: {
      start_date?: string;
      end_date?: string;
      limit?: number;
      indicators?: boolean;
    } = {},
  ) => apiHttp<DailyResponse>(`/stocks/${encodeURIComponent(code)}/daily`, { params }),

  // 数据同步
  syncDaily: (body: SyncDailyRequest) =>
    apiHttp<SyncDailyResponse>("/data/sync/daily", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // 回测
  runMaCross: (body: MaCrossRequest) =>
    apiHttp<BacktestDetailResponse>("/backtest/ma-cross", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getBacktest: (taskId: number | string) =>
    apiHttp<BacktestDetailResponse>(`/backtest/${taskId}`),

  getBacktestReport: (taskId: number | string) =>
    apiHttp<BacktestReport>(`/backtest/${taskId}/report`),

  listBacktestTasks: (limit = 50) =>
    apiHttp<BacktestTaskListResponse>("/backtest/tasks", { params: { limit } }),

  // 管理员后台
  getAdminUsers: (params: {
    page?: number;
    page_size?: number;
    search?: string;
    role?: string;
    status?: string;
  }) =>
    adminHttp<AdminUserListResponse>("/api/admin/users", {
      params,
    }),

  getAdminUserDetail: (id: number) =>
    adminHttp<AdminUserDetail>(`/api/admin/users/${id}`),

  updateAdminUser: (id: number, payload: AdminUserUpdatePayload) =>
    adminHttp<AdminUserDetail>(`/api/admin/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  deleteAdminUser: (id: number) =>
    adminHttp<{ message: string }>(`/api/admin/users/${id}`, {
      method: "DELETE",
    }),

  resetAdminUserPassword: (id: number, payload: AdminUserResetPasswordPayload) =>
    adminHttp<{ message: string }>(`/api/admin/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

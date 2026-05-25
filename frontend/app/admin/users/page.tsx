"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { getStoredUser, isAuthenticated } from "@/lib/auth";
import type { AuthUser } from "@/types/auth";
import type { AdminUserListItem, UserRole, UserStatus } from "@/types/admin";

const ROLE_OPTIONS: Array<UserRole | ""> = ["", "user", "admin", "super_admin"];
const STATUS_OPTIONS: Array<UserStatus | ""> = ["", "active", "disabled"];

export default function AdminUsersPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [items, setItems] = useState<AdminUserListItem[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<UserRole | "">("");
  const [status, setStatus] = useState<UserStatus | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    setUser(getStoredUser());
  }, [router]);

  const hasAccess = useMemo(
    () => user && (user.role === "admin" || user.role === "super_admin"),
    [user],
  );

  useEffect(() => {
    if (!hasAccess) return;
    let active = true;
    setLoading(true);
    setError(null);
    api
      .getAdminUsers({
        page,
        page_size: pageSize,
        search: search || undefined,
        role: role || undefined,
        status: status || undefined,
      })
      .then((res) => {
        if (!active) return;
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [hasAccess, page, pageSize, search, role, status]);

  if (!user) return null;
  if (!hasAccess) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-neutral-900">无权限访问</h1>
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  async function toggleStatus(target: AdminUserListItem) {
    const next = target.status === "active" ? "disabled" : "active";
    try {
      await api.updateAdminUser(target.id, { status: next });
      setItems((prev) =>
        prev.map((item) => (item.id === target.id ? { ...item, status: next } : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function onDelete(target: AdminUserListItem) {
    if (!confirm(`确认删除用户 ${target.username}？`)) return;
    try {
      await api.deleteAdminUser(target.id);
      setItems((prev) => prev.filter((item) => item.id !== target.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">用户管理</h1>
          <p className="mt-2 text-neutral-600">查询、编辑、禁用和删除用户。</p>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索用户名/邮箱"
          className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as UserRole | "")}
          className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
        >
          {ROLE_OPTIONS.map((item) => (
            <option key={item || "all"} value={item}>
              {item ? `角色: ${item}` : "全部角色"}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as UserStatus | "")}
          className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
        >
          {STATUS_OPTIONS.map((item) => (
            <option key={item || "all"} value={item}>
              {item ? `状态: ${item}` : "全部状态"}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => setPage(1)}
          className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500"
        >
          查询
        </button>
      </div>

      {error ? (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">
          {error}
        </div>
      ) : null}

      <div className="mt-6 overflow-x-auto rounded-lg border border-neutral-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-neutral-50 text-left text-xs font-semibold text-neutral-600">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">用户名</th>
              <th className="px-4 py-3">邮箱</th>
              <th className="px-4 py-3">角色</th>
              <th className="px-4 py-3">状态</th>
              <th className="px-4 py-3">注册时间</th>
              <th className="px-4 py-3">最后登录</th>
              <th className="px-4 py-3">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {loading ? (
              <tr>
                <td colSpan={8} className="px-4 py-6 text-center text-neutral-500">
                  加载中...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-6 text-center text-neutral-500">
                  暂无数据
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="text-neutral-700">
                  <td className="px-4 py-3">{item.id}</td>
                  <td className="px-4 py-3 font-medium text-neutral-900">{item.username}</td>
                  <td className="px-4 py-3">{item.email}</td>
                  <td className="px-4 py-3">{item.role}</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        item.status === "active"
                          ? "rounded-full bg-emerald-50 px-2 py-1 text-xs text-emerald-700"
                          : "rounded-full bg-amber-50 px-2 py-1 text-xs text-amber-700"
                      }
                    >
                      {item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{new Date(item.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    {item.last_login_at ? new Date(item.last_login_at).toLocaleString() : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      <Link
                        href={`/admin/users/${item.id}`}
                        className="rounded-md border border-neutral-200 px-2 py-1 text-xs hover:border-blue-300"
                      >
                        查看/编辑
                      </Link>
                      <button
                        type="button"
                        onClick={() => toggleStatus(item)}
                        className="rounded-md border border-neutral-200 px-2 py-1 text-xs hover:border-blue-300"
                      >
                        {item.status === "active" ? "禁用" : "启用"}
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(item)}
                        className="rounded-md border border-neutral-200 px-2 py-1 text-xs text-red-600 hover:border-red-300"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-neutral-600">
        <span>
          共 {total} 条，当前第 {page} / {totalPages} 页
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="rounded-md border border-neutral-200 px-3 py-1 disabled:cursor-not-allowed disabled:opacity-50"
          >
            上一页
          </button>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="rounded-md border border-neutral-200 px-3 py-1 disabled:cursor-not-allowed disabled:opacity-50"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
}

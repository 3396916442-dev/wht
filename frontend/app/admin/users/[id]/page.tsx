"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { getStoredUser, isAuthenticated } from "@/lib/auth";
import type { AuthUser } from "@/types/auth";
import type { AdminUserDetail, UserRole, UserStatus } from "@/types/admin";

const ROLE_OPTIONS: UserRole[] = ["user", "admin", "super_admin"];
const STATUS_OPTIONS: UserStatus[] = ["active", "disabled"];

export default function AdminUserDetailPage() {
  const router = useRouter();
  const params = useParams();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    username: "",
    email: "",
    status: "active" as UserStatus,
    role: "user" as UserRole,
  });
  const [newPassword, setNewPassword] = useState("");

  const userId = Number(params?.id);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    setCurrentUser(getStoredUser());
  }, [router]);

  const hasAccess = useMemo(
    () => currentUser && (currentUser.role === "admin" || currentUser.role === "super_admin"),
    [currentUser],
  );

  useEffect(() => {
    if (!hasAccess || !userId) return;
    setLoading(true);
    setError(null);
    api
      .getAdminUserDetail(userId)
      .then((res) => {
        setUser(res);
        setForm({
          username: res.username,
          email: res.email,
          status: res.status,
          role: res.role,
        });
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [hasAccess, userId]);

  if (!currentUser) return null;
  if (!hasAccess) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-neutral-900">无权限访问</h1>
      </div>
    );
  }

  async function onSave() {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await api.updateAdminUser(user.id, {
        username: form.username,
        email: form.email,
        status: form.status,
        role: currentUser.role === "super_admin" ? form.role : undefined,
      });
      setUser(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function onResetPassword() {
    if (!user || newPassword.length < 8) {
      setError("密码至少 8 位");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.resetAdminUserPassword(user.id, { new_password: newPassword });
      setNewPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function onDelete() {
    if (!user) return;
    if (!confirm(`确认删除用户 ${user.username}？`)) return;
    setLoading(true);
    setError(null);
    try {
      await api.deleteAdminUser(user.id);
      router.push("/admin/users");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">用户详情</h1>
          <p className="mt-2 text-neutral-600">查看和编辑用户资料。</p>
        </div>
      </div>

      {loading ? (
        <div className="mt-6 rounded-md border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-500">
          加载中...
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">
          {error}
        </div>
      ) : null}

      {user ? (
        <div className="mt-6 grid gap-6">
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="text-sm text-neutral-600">
                用户名
                <input
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  className="mt-1 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                />
              </label>
              <label className="text-sm text-neutral-600">
                邮箱
                <input
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="mt-1 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                />
              </label>
              <label className="text-sm text-neutral-600">
                状态
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value as UserStatus })}
                  className="mt-1 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                >
                  {STATUS_OPTIONS.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm text-neutral-600">
                角色
                <select
                  value={form.role}
                  disabled={currentUser.role !== "super_admin"}
                  onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
                  className="mt-1 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm disabled:bg-neutral-100"
                >
                  {ROLE_OPTIONS.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button
              type="button"
              onClick={onSave}
              className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
            >
              保存修改
            </button>
          </div>

          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-neutral-900">重置密码</h2>
            <p className="mt-1 text-sm text-neutral-600">新密码至少 8 位</p>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={onResetPassword}
                className="rounded-md border border-neutral-200 px-4 py-2 text-sm hover:border-blue-300"
              >
                重置密码
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-red-200 bg-red-50 p-5">
            <h2 className="text-lg font-semibold text-red-700">危险操作</h2>
            <p className="mt-1 text-sm text-red-600">删除用户不可恢复，请谨慎操作。</p>
            <button
              type="button"
              onClick={onDelete}
              className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500"
            >
              删除用户
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getStoredUser, isAuthenticated } from "@/lib/auth";
import type { AuthUser } from "@/types/auth";

export default function AdminHomePage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

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

  if (!user) return null;
  if (!hasAccess) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-neutral-900">无权限访问</h1>
        <p className="mt-2 text-neutral-600">请联系管理员授予权限。</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-neutral-900">后台管理</h1>
      <p className="mt-2 text-neutral-600">管理注册用户与权限设置。</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Link
          href="/admin/users"
          className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition hover:border-blue-300"
        >
          <div className="text-lg font-semibold text-neutral-900">用户管理</div>
          <div className="mt-1 text-sm text-neutral-600">查看、编辑、禁用与删除用户</div>
        </Link>
      </div>
    </div>
  );
}

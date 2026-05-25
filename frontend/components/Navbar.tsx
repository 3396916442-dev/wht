"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { classNames } from "@/lib/format";
import { clearAuthSession, getStoredUser, isAuthenticated } from "@/lib/auth";
import type { AuthUser } from "@/types/auth";

const NAV_ITEMS: Array<{ href: string; label: string; matchPrefix?: string }> = [
  { href: "/", label: "Dashboard" },
  { href: "/stocks/600519", label: "股票详情", matchPrefix: "/stocks" },
  { href: "/backtest", label: "策略回测", matchPrefix: "/backtest" },
  { href: "/data", label: "数据管理", matchPrefix: "/data" },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, [pathname]);

  function onLogout() {
    clearAuthSession();
    setUser(null);
    router.push("/login");
  }

  return (
    <nav className="border-b border-neutral-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-center gap-2 text-base font-semibold text-neutral-900">
          <span className="inline-block h-2 w-2 rounded-full bg-blue-600" aria-hidden />
          A 股量化分析平台
        </Link>
        <div className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const active =
              item.matchPrefix
                ? pathname === item.matchPrefix || pathname.startsWith(`${item.matchPrefix}/`)
                : pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={classNames(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition",
                  active
                    ? "bg-blue-50 text-blue-700"
                    : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
                )}
              >
                {item.label}
              </Link>
            );
          })}
          {user && (user.role === "admin" || user.role === "super_admin") ? (
            <Link
              href="/admin"
              className={classNames(
                "rounded-md px-3 py-1.5 text-sm font-medium transition",
                pathname === "/admin" || pathname.startsWith("/admin/")
                  ? "bg-blue-50 text-blue-700"
                  : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
              )}
            >
              后台管理
            </Link>
          ) : null}
          {isAuthenticated() && user ? (
            <>
              <span className="ml-2 rounded-md bg-neutral-100 px-3 py-1.5 text-sm text-neutral-700">
                {user.username}
              </span>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-md px-3 py-1.5 text-sm font-medium text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
              >
                退出
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="ml-2 rounded-md px-3 py-1.5 text-sm font-medium text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-500"
              >
                注册
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

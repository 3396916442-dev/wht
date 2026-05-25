"use client";

import { usePathname } from "next/navigation";

import { Navbar } from "@/components/Navbar";

const AUTH_PATHS = new Set(["/login", "/register"]);

export function MainShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = AUTH_PATHS.has(pathname);

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </>
  );
}

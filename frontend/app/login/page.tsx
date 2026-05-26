"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthAlert } from "@/components/auth/AuthAlert";
import { AuthButton } from "@/components/auth/AuthButton";
import { AuthInput } from "@/components/auth/AuthInput";
import { AuthShell } from "@/components/auth/AuthShell";
import { authApi } from "@/lib/auth-api";
import { setAuthSession } from "@/lib/auth";
import { loginSchema, type LoginFormValues } from "@/lib/validations/auth";

export default function LoginPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username_or_email: "",
      password: "",
    },
  });

  async function onSubmit(values: LoginFormValues) {
    setServerError(null);
    try {
      const resp = await authApi.login(values);
      setAuthSession(resp.access_token, resp.user);
      router.push("/");
      router.refresh();
    } catch (error) {
      // 打印详细错误信息以便排查 Network Error
      // 包括 axios 的 response / config（在浏览器控制台可见）
      // 不改动 UI，仅增加控制台日志
      console.error("login error", {
        message: error instanceof Error ? error.message : String(error),
        status: (error as any)?.response?.status,
        data: (error as any)?.response?.data,
        baseURL: (error as any)?.config?.baseURL,
        url: (error as any)?.config?.url,
      });
      setServerError(error instanceof Error ? error.message : "登录失败");
    }
  }

  return (
    <AuthShell
      title="欢迎回来"
      subtitle="使用用户名或 QQ 邮箱登录你的量化研究账户"
      footer={
        <>
          还没有账户？{" "}
          <Link href="/register" className="font-medium text-blue-400 hover:text-blue-300">
            立即注册
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {serverError ? <AuthAlert message={serverError} /> : null}

        <AuthInput
          label="用户名 / 邮箱"
          placeholder="quant_user 或 123456789@qq.com"
          autoComplete="username"
          error={errors.username_or_email?.message}
          {...register("username_or_email")}
        />

        <AuthInput
          label="密码"
          type="password"
          placeholder="请输入密码"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password")}
        />

        <AuthButton type="submit" loading={isSubmitting}>
          登录
        </AuthButton>
      </form>
    </AuthShell>
  );
}

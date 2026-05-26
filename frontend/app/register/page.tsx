"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthAlert } from "@/components/auth/AuthAlert";
import { AuthButton } from "@/components/auth/AuthButton";
import { AuthInput } from "@/components/auth/AuthInput";
import { AuthShell } from "@/components/auth/AuthShell";
import { authApi } from "@/lib/auth-api";
import { registerSchema, sendCodeSchema, type RegisterFormValues } from "@/lib/validations/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);
  const [sendingCode, setSendingCode] = useState(false);

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: "",
      email: "",
      password: "",
      confirm_password: "",
      code: "",
    },
  });

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = window.setTimeout(() => setCountdown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [countdown]);

  async function onSendCode() {
    setServerError(null);
    setSuccessMessage(null);
    const email = getValues("email");
    const parsed = sendCodeSchema.safeParse({ email });
    if (!parsed.success) {
      setServerError(parsed.error.issues[0]?.message ?? "请输入有效 QQ 邮箱");
      return;
    }

    setSendingCode(true);
    try {
      const resp = await authApi.sendCode({ email: parsed.data.email });
      setSuccessMessage(resp.message);
      setCountdown(60);
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "验证码发送失败");
    } finally {
      setSendingCode(false);
    }
  }

  async function onSubmit(values: RegisterFormValues) {
    setServerError(null);
    setSuccessMessage(null);
    try {
      await authApi.register(values);
      router.push("/login");
    } catch (error) {
      // 打印详细错误信息以便排查 Network Error
      console.error("register error", {
        message: error instanceof Error ? error.message : String(error),
        status: (error as any)?.response?.status,
        data: (error as any)?.response?.data,
        baseURL: (error as any)?.config?.baseURL,
        url: (error as any)?.config?.url,
      });
      setServerError(error instanceof Error ? error.message : "注册失败");
    }
  }

  return (
    <AuthShell
      title="创建账户"
      subtitle="使用 QQ 邮箱验证后即可开始你的量化研究之旅"
      footer={
        <>
          已有账户？{" "}
          <Link href="/login" className="font-medium text-blue-400 hover:text-blue-300">
            去登录
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {serverError ? <AuthAlert message={serverError} /> : null}
        {successMessage ? <AuthAlert type="success" message={successMessage} /> : null}

        <AuthInput
          label="用户名"
          placeholder="3-32 位字母、数字或下划线"
          autoComplete="username"
          error={errors.username?.message}
          {...register("username")}
        />

        <AuthInput
          label="QQ 邮箱"
          placeholder="123456789@qq.com"
          autoComplete="email"
          error={errors.email?.message}
          {...register("email")}
        />

        <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
          <AuthInput
            label="邮箱验证码"
            placeholder="6 位数字"
            inputMode="numeric"
            maxLength={6}
            error={errors.code?.message}
            {...register("code")}
          />
          <AuthButton
            type="button"
            variant="secondary"
            className="sm:w-36"
            loading={sendingCode}
            disabled={countdown > 0}
            onClick={onSendCode}
          >
            {countdown > 0 ? `${countdown}s 后重试` : "获取验证码"}
          </AuthButton>
        </div>

        <AuthInput
          label="密码"
          type="password"
          placeholder="至少 8 位"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register("password")}
        />

        <AuthInput
          label="确认密码"
          type="password"
          placeholder="再次输入密码"
          autoComplete="new-password"
          error={errors.confirm_password?.message}
          {...register("confirm_password")}
        />

        <AuthButton type="submit" loading={isSubmitting}>
          注册
        </AuthButton>
      </form>
    </AuthShell>
  );
}

import { z } from "zod";

const qqEmail = z
  .string()
  .trim()
  .email("请输入有效邮箱")
  .refine((value) => /^[1-9]\d{4,10}@qq\.com$/i.test(value), {
    message: "仅支持 QQ 邮箱，如 123456789@qq.com",
  });

export const loginSchema = z.object({
  username_or_email: z.string().trim().min(3, "用户名或邮箱至少 3 个字符"),
  password: z.string().min(8, "密码至少 8 位"),
});

export const registerSchema = z
  .object({
    username: z
      .string()
      .trim()
      .min(3, "用户名至少 3 个字符")
      .max(32, "用户名最多 32 个字符")
      .regex(/^[a-zA-Z0-9_]+$/, "用户名只能包含字母、数字和下划线"),
    email: qqEmail,
    password: z
      .string()
      .min(8, "密码至少 8 位")
      .max(128, "密码最多 128 位"),
    confirm_password: z.string().min(8, "请再次输入密码"),
    code: z.string().regex(/^\d{6}$/, "验证码为 6 位数字"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "两次输入的密码不一致",
    path: ["confirm_password"],
  });

export const sendCodeSchema = z.object({
  email: qqEmail,
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;

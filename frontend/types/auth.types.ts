import { z } from "zod";

/* ─────────────────────────────────────────────
   Zod Schemas
   ───────────────────────────────────────────── */

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
  password: z
    .string()
    .min(1, "Password is required")
    .min(8, "Password must be at least 8 characters"),
  rememberMe: z.boolean().optional().default(false),
});

export const registerSchema = z
  .object({
    fullName: z
      .string()
      .min(1, "Full name is required")
      .min(2, "Name must be at least 2 characters")
      .max(100, "Name must be less than 100 characters"),
    email: z
      .string()
      .min(1, "Email is required")
      .email("Please enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .max(100, "Password must be less than 100 characters")
      .regex(/[A-Z]/, "Must contain at least one uppercase letter")
      .regex(/[0-9]/, "Must contain at least one number"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
    acceptTerms: z
      .boolean()
      .refine((val) => val === true, "You must accept the terms of service"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
});

/* ─────────────────────────────────────────────
   Inferred TypeScript Types
   ───────────────────────────────────────────── */

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;
export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

/* ─────────────────────────────────────────────
   API Response Types (matching backend)
   ───────────────────────────────────────────── */

export interface UserResponse {
  id: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
  created_at: string;
}

export interface AuthResponse {
  user: UserResponse;
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface ApiError {
  detail: string;
}

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  login,
  register,
  logout,
  forgotPassword,
} from "@/features/auth/api/auth-api";
import type {
  LoginFormValues,
  RegisterFormValues,
} from "@/types/auth.types";
import { ApiRequestError, getAccessToken } from "@/lib/api-client";

export function useLogin() {
  const router = useRouter();

  return useMutation({
    mutationFn: (credentials: Pick<LoginFormValues, "email" | "password">) =>
      login(credentials),
    onSuccess: () => {
      toast.success("Welcome back!", {
        description: "Successfully logged in.",
      });
      router.push("/dashboard"); // Phase 2 stub
    },
    onError: (error) => {
      const message =
        error instanceof ApiRequestError ? error.detail : "Login failed";
      toast.error("Authentication failed", {
        description: message,
      });
    },
  });
}

export function useRegister() {
  const router = useRouter();

  return useMutation({
    mutationFn: (data: Pick<RegisterFormValues, "email" | "password">) =>
      register(data),
    onSuccess: () => {
      toast.success("Account created successfully", {
        description: "Welcome to EquityIQ.",
      });
      router.push("/dashboard"); // Phase 2 stub
    },
    onError: (error) => {
      const message =
        error instanceof ApiRequestError ? error.detail : "Registration failed";
      toast.error("Account creation failed", {
        description: message,
      });
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = localStorage.getItem("equityiq_refresh_token");
      if (refreshToken) {
        await logout(refreshToken);
      }
    },
    onSuccess: () => {
      queryClient.clear();
      router.push("/login");
    },
    onError: () => {
      // Force logout client-side even if API fails
      queryClient.clear();
      localStorage.removeItem("equityiq_access_token");
      localStorage.removeItem("equityiq_refresh_token");
      router.push("/login");
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => forgotPassword(email),
    // onSuccess/onError handling is done locally in the form to switch states
  });
}

export function useIsAuthenticated() {
  // Simple check for phase 1. Phase 2 will involve proper auth context.
  if (typeof window === "undefined") return false;
  return !!getAccessToken();
}

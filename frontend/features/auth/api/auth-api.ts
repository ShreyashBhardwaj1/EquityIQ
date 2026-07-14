import { apiRequest, setTokens, clearTokens } from "@/lib/api-client";
import type {
  AuthResponse,
  RefreshResponse,
  LoginFormValues,
  RegisterFormValues,
} from "@/types/auth.types";

const AUTH_PREFIX = "/api/v1/auth";

/**
 * Authenticate with email + password.
 * Stores tokens on success.
 */
export async function login(
  credentials: Pick<LoginFormValues, "email" | "password">
): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>(`${AUTH_PREFIX}/login`, {
    method: "POST",
    body: JSON.stringify({
      email: credentials.email,
      password: credentials.password,
    }),
  });
  setTokens(response.access_token, response.refresh_token);
  return response;
}

/**
 * Register a new account.
 * Stores tokens on success (auto-login after registration).
 */
export async function register(
  data: Pick<RegisterFormValues, "email" | "password">
): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>(`${AUTH_PREFIX}/register`, {
    method: "POST",
    body: JSON.stringify({
      email: data.email,
      password: data.password,
      role: "viewer",
    }),
  });
  setTokens(response.access_token, response.refresh_token);
  return response;
}

/**
 * Rotate the refresh token.
 */
export async function refreshSession(
  refreshToken: string
): Promise<RefreshResponse> {
  const response = await apiRequest<RefreshResponse>(
    `${AUTH_PREFIX}/refresh`,
    {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }
  );
  setTokens(response.access_token, response.refresh_token);
  return response;
}

/**
 * Revoke the refresh token and clear local storage.
 */
export async function logout(refreshToken: string): Promise<void> {
  try {
    await apiRequest<{ detail: string }>(`${AUTH_PREFIX}/logout`, {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } finally {
    clearTokens();
  }
}

/**
 * NOTE: The backend does not yet expose a forgot-password endpoint.
 * This stub is prepared for Phase 2 integration.
 * Returns a resolved promise so the UI can show a success state.
 */
export async function forgotPassword(email: string): Promise<void> {
  // Placeholder: replace with real endpoint when backend adds /auth/forgot-password
  await new Promise((resolve) => setTimeout(resolve, 800));
  console.info("[auth-api] forgotPassword called for:", email);
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface AuthStatus {
  authenticated: boolean;
  username?: string;
}

/**
 * Logout the user by calling the logout endpoint.
 *
 * @returns Promise<boolean> - true if logout was successful, false otherwise
 */
export async function logout(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });

    if (response.ok) {
      console.log("Logout successful");
      return true;
    } else {
      // Log detailed error information for diagnostics
      const errorText = await response.text().catch(() => "Unknown error");
      console.error(
        `Logout failed: ${response.status} ${response.statusText}`,
        errorText
      );
      return false;
    }
  } catch (error) {
    // Network error or other exception
    console.error("Logout failed:", error);
    return false;
  }
}

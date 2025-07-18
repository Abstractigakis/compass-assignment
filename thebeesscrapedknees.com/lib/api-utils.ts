import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

/**
 * Utility function to authenticate user and return user data
 */
export async function authenticateUser() {
  const supabase = await createClient();
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return {
      user: null,
      supabase,
      response: NextResponse.json({ error: "Unauthorized" }, { status: 401 }),
    };
  }

  return { user, supabase, response: null };
}

/**
 * Utility function to handle common error responses
 */
export function handleError(error: unknown, context: string) {
  console.error(`${context} error:`, error);
  return NextResponse.json({ error: "Internal server error" }, { status: 500 });
}

/**
 * Utility function to validate pagination parameters
 */
export function validatePagination(searchParams: URLSearchParams) {
  const limit = searchParams.get("limit");
  const offset = searchParams.get("offset");

  return {
    limit: limit ? Math.min(parseInt(limit), 100) : 10, // Max 100 items per page
    offset: offset ? parseInt(offset) : 0,
  };
}

/**
 * API response types
 */
export type ApiResponse<T> = {
  data?: T;
  count?: number;
  error?: string;
  message?: string;
};

/**
 * Standard success response
 */
export function successResponse<T>(data: T, status = 200): NextResponse {
  return NextResponse.json({ data }, { status });
}

/**
 * Standard error response
 */
export function errorResponse(message: string, status = 400): NextResponse {
  return NextResponse.json({ error: message }, { status });
}

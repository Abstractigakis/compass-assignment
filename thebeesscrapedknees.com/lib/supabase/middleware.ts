import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";
import { Database } from "./db.types";

export const updateSession = async (request: NextRequest) => {
  // This `try/catch` block is only here for the interactive tutorial.
  // Feel free to remove once you have Supabase connected.
  try {
    // Create an unmodified response
    let response = NextResponse.next({
      request: {
        headers: request.headers,
      },
    });

    const supabase = createServerClient<Database>(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return request.cookies.getAll();
          },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value }) =>
              request.cookies.set(name, value)
            );
            response = NextResponse.next({
              request,
            });
            cookiesToSet.forEach(({ name, value, options }) =>
              response.cookies.set(name, value, options)
            );
          },
        },
      }
    );

    // This will refresh session if expired - required for Server Components
    // https://supabase.com/docs/guides/auth/server-side/nextjs
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser();

    // More precise authentication check
    const isAuthenticated = !error && user !== null;
    const currentPath = request.nextUrl.pathname;
    const isPublicPage =
      currentPath === "/" ||
      currentPath === "/sign-in" ||
      currentPath === "/sign-up" ||
      currentPath === "/forgot-password" ||
      currentPath.startsWith("/auth/");

    // If user is authenticated and on any public page (including home), redirect to /app
    if (isAuthenticated && isPublicPage) {
      const redirectUrl = new URL("/app", request.url);
      return NextResponse.redirect(redirectUrl);
    }

    // If user is not authenticated and trying to access protected routes, redirect to sign-in
    if (!isAuthenticated && !isPublicPage) {
      const redirectUrl = new URL("/sign-in", request.url);
      return NextResponse.redirect(redirectUrl);
    }

    return response;
  } catch (e) {
    console.error("Middleware error:", e);
    // If you are here, a Supabase client could not be created!
    // This is likely because you have not set up environment variables.
    // Check out http://localhost:3000 for Next Steps.
    return NextResponse.next({
      request: {
        headers: request.headers,
      },
    });
  }
};

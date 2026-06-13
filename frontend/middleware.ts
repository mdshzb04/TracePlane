import { NextRequest, NextResponse } from "next/server"

const PUBLIC_PATHS = ["/", "/login", "/auth/callback"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname === "/dashboard") {
    return NextResponse.next()
  }

  const isPublic = PUBLIC_PATHS.includes(pathname)
  const hasSession = request.cookies.get("has_session")?.value === "1"

  if (hasSession && (pathname === "/" || pathname === "/login")) {
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  if (!hasSession && !isPublic) {
    return NextResponse.redirect(new URL("/login", request.url))
  }

  return NextResponse.next()
}

export const config = {
  // Exclude static assets and /api (proxied to FastAPI)
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api|traceplane-|providers/).*)"],
}

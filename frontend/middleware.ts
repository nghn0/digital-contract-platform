import { type NextRequest, NextResponse } from 'next/server'
import { updateSession } from '@/utils/supabase/middleware'

export async function middleware(request: NextRequest) {
  // update user's auth session
  const { supabaseResponse, user } = await updateSession(request)

  const protectedRoutes = ['/dashboard', '/contracts', '/intelligence', '/upload', '/receiver', '/sender', '/verifier']
  const isProtected = protectedRoutes.some(route => request.nextUrl.pathname.startsWith(route))


  if (isProtected && !user) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('next', request.nextUrl.pathname)
    const redirectResponse = NextResponse.redirect(loginUrl)
    // IMPORTANT: copy cookies to the redirect response to ensure dead cookies are cleared
    supabaseResponse.cookies.getAll().forEach(cookie => {
      redirectResponse.cookies.set(cookie.name, cookie.value)
    })
    return redirectResponse
  }

  // Prevent authenticated users from visiting login/signup
  const authRoutes = ['/login', '/signup']
  const isAuthRoute = authRoutes.some(route => request.nextUrl.pathname.startsWith(route))
  
  if (isAuthRoute && user) {
    // Check if there is a valid internal 'next' redirect
    const nextPath = request.nextUrl.searchParams.get('next')
    let redirectResponse;
    
    if (nextPath && nextPath.startsWith('/') && !nextPath.startsWith('//') && !nextPath.startsWith('/\\')) {
      redirectResponse = NextResponse.redirect(new URL(nextPath, request.url))
    } else {
      redirectResponse = NextResponse.redirect(new URL('/dashboard', request.url))
    }
    
    // IMPORTANT: copy cookies to the redirect response to ensure session refreshes are saved
    supabaseResponse.cookies.getAll().forEach(cookie => {
      redirectResponse.cookies.set(cookie.name, cookie.value)
    })
    return redirectResponse
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}

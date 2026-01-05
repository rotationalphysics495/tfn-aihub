# Story 1.2: Supabase Auth Integration

Status: ready-for-dev

## Story

As a **Plant Manager or Line Supervisor**,
I want **to securely log in and log out of the Manufacturing Performance Assistant using Supabase Auth**,
so that **my session is authenticated and my access to sensitive manufacturing data is protected**.

## Acceptance Criteria

1. **User can log in with email/password** via Supabase Auth from the Next.js frontend
2. **User can log out** and their session is properly terminated
3. **JWT tokens are validated** in FastAPI backend for all protected API endpoints
4. **Unauthenticated requests are rejected** with appropriate 401 response
5. **Session state persists** across browser refreshes using Supabase session management
6. **Auth UI components** are styled consistent with "Industrial Clarity" design system
7. **Error handling** provides clear feedback for invalid credentials, network errors, etc.

## Tasks / Subtasks

- [ ] Task 1: Configure Supabase Auth in Supabase Dashboard (AC: #1, #2)
  - [ ] 1.1 Enable Email/Password authentication provider
  - [ ] 1.2 Configure auth settings (session duration, password requirements)
  - [ ] 1.3 Document Supabase project URL and anon key for environment variables

- [ ] Task 2: Implement Supabase Auth in Next.js Frontend (AC: #1, #2, #5, #6)
  - [ ] 2.1 Install `@supabase/supabase-js` and `@supabase/ssr` packages
  - [ ] 2.2 Create Supabase client utility in `apps/web/src/lib/supabase/client.ts`
  - [ ] 2.3 Create server-side Supabase client for SSR in `apps/web/src/lib/supabase/server.ts`
  - [ ] 2.4 Implement middleware for session refresh in `apps/web/src/middleware.ts`
  - [ ] 2.5 Create Login page component at `apps/web/src/app/(auth)/login/page.tsx`
  - [ ] 2.6 Create auth callback route at `apps/web/src/app/auth/callback/route.ts`
  - [ ] 2.7 Implement logout functionality with session cleanup
  - [ ] 2.8 Style auth components with Tailwind CSS matching "Industrial Clarity" theme

- [ ] Task 3: Implement JWT Validation in FastAPI Backend (AC: #3, #4)
  - [ ] 3.1 Install `python-jose[cryptography]` and `httpx` packages
  - [ ] 3.2 Create auth dependency in `apps/api/app/core/security.py`
  - [ ] 3.3 Fetch Supabase JWT public key (JWKS) for token verification
  - [ ] 3.4 Implement `get_current_user` dependency that validates JWT from Authorization header
  - [ ] 3.5 Create `CurrentUser` Pydantic model for typed user data
  - [ ] 3.6 Apply auth dependency to protected routes

- [ ] Task 4: Implement Error Handling (AC: #7)
  - [ ] 4.1 Create auth error types and user-friendly messages in frontend
  - [ ] 4.2 Implement proper HTTP exception handling in FastAPI for auth failures
  - [ ] 4.3 Add loading states and error display in Login UI

- [ ] Task 5: Integration Testing (AC: #1-7)
  - [ ] 5.1 Test login flow end-to-end
  - [ ] 5.2 Test logout and session termination
  - [ ] 5.3 Test protected API endpoint access with valid/invalid tokens
  - [ ] 5.4 Test session persistence across page refreshes

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document:**
- Frontend: Next.js 14+ with App Router
- Backend: Python FastAPI 0.109+
- Auth Provider: Supabase Auth with JWT validation in FastAPI
- All API endpoints MUST be protected via Supabase Auth (JWT validation in FastAPI dependency)
- Environment variables managed via Railway Secrets (Production) and `.env` (Local)

**Authentication Flow:**
```
User -> Next.js Login Page -> Supabase Auth -> JWT Token
                                                   |
                                                   v
Next.js (stores session) -> API Request + JWT Header -> FastAPI
                                                           |
                                                           v
                                        JWT Validation Dependency -> Protected Route
```

### Technical Implementation Details

**Next.js Supabase Client Setup:**
- Use `@supabase/ssr` for proper SSR/SSG support with App Router
- Client-side: `createBrowserClient()` for client components
- Server-side: `createServerClient()` for server components and route handlers
- Middleware handles session refresh on each request

**FastAPI JWT Validation:**
- Supabase uses RS256 algorithm for JWT signing
- Fetch JWKS from `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`
- Cache JWKS with TTL to avoid repeated fetches
- Extract user info from JWT claims: `sub` (user ID), `email`, `role`

**Environment Variables Required:**
```
# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>

# Backend (.env)
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_JWT_SECRET=<jwt-secret>  # For HS256 verification (alternative)
# OR use JWKS endpoint for RS256 verification (recommended)
```

### Project Structure Notes

**Frontend Files to Create/Modify:**
```
apps/web/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── login/
│   │   │       └── page.tsx          # Login page component
│   │   └── auth/
│   │       └── callback/
│   │           └── route.ts          # OAuth callback handler
│   ├── lib/
│   │   └── supabase/
│   │       ├── client.ts             # Browser client
│   │       └── server.ts             # Server client
│   └── middleware.ts                  # Session refresh middleware
├── package.json                       # Add Supabase dependencies
└── .env.local                         # Environment variables
```

**Backend Files to Create/Modify:**
```
apps/api/
├── app/
│   ├── core/
│   │   ├── config.py                 # Add Supabase config
│   │   └── security.py               # JWT validation logic (NEW)
│   ├── api/
│   │   └── deps.py                   # Auth dependencies (NEW)
│   └── models/
│       └── user.py                   # CurrentUser model (NEW)
├── requirements.txt                   # Add jose, httpx
└── .env                              # Environment variables
```

### Code Examples

**FastAPI JWT Dependency Pattern:**
```python
# apps/api/app/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    try:
        # Verify JWT with Supabase JWKS
        payload = verify_supabase_jwt(token)
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**Next.js Middleware Pattern:**
```typescript
// apps/web/src/middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value))
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options))
        },
      },
    }
  )

  await supabase.auth.getUser()
  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

### Testing Requirements

- Unit tests for JWT validation logic in FastAPI
- Integration tests for login/logout flow
- Test invalid token rejection (expired, malformed, wrong signature)
- Test session persistence across browser refresh
- Manual verification of UI styling matches "Industrial Clarity" design

### Dependencies on Previous Stories

- **Story 1.1 (TurboRepo Monorepo Scaffold)** MUST be completed first
  - Requires `apps/web` Next.js project structure
  - Requires `apps/api` FastAPI project structure
  - Requires TurboRepo configuration

### References

- [Source: _bmad/bmm/data/architecture.md#8-security-constraints] - JWT validation requirement
- [Source: _bmad/bmm/data/architecture.md#3-tech-stack] - Supabase Auth specification
- [Source: _bmad/bmm/data/ux-design.md#2-overall-ux-goals] - Industrial Clarity design principle
- [Source: _bmad-output/planning-artifacts/epic-1.md#story-12] - Story definition
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Supabase SSR Package](https://supabase.com/docs/guides/auth/server-side/nextjs)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List


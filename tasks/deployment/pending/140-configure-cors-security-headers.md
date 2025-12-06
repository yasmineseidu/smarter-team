# Task 239: Set Up CORS and Security Headers

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure CORS policies for frontend-backend communication and implement comprehensive security headers (CSP, X-Frame-Options, etc.) for production deployment.

## Prerequisites

- [ ] Task 238 completed (Domain and SSL configured)
- [ ] Frontend and backend services deployed
- [ ] Domains accessible via HTTPS

## Implementation Checklist

- [ ] Configure CORS in FastAPI backend
- [ ] Add security headers to backend
- [ ] Configure Next.js security headers
- [ ] Set up Content Security Policy (CSP)
- [ ] Test CORS from frontend
- [ ] Verify security headers with tools

## Configuration Details

### Backend CORS Configuration

**Update `app/backend/src/main.py`:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.config import settings

app = FastAPI(
    title="Smarter Team API",
    description="Multi-agent AI agency automation",
    version="1.0.0",
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "api.smarter-team.com",
        "smarter-team.com",
        "www.smarter-team.com",
        "staging-api.smarter-team.com" if settings.environment == "staging" else None,
        "localhost" if settings.environment == "development" else None,
    ],
)

# CORS
origins = [
    "https://smarter-team.com",
    "https://www.smarter-team.com",
]

if settings.environment == "staging":
    origins.extend([
        "https://staging.smarter-team.com",
    ])

if settings.environment == "development":
    origins.extend([
        "http://localhost:3000",
        "http://localhost:8000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Type",
        "Authorization",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID"],
    max_age=3600,  # Cache preflight requests for 1 hour
)
```

### Backend Security Headers

**Add security headers middleware:**

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS (already set by Nginx, but add for redundancy)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # CSP for API (restrictive)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### Frontend Security Headers

**Update `app/frontend/next.config.mjs`:**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,

  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          // Security headers
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
          // Content Security Policy
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // Next.js requires unsafe-inline/eval
              "style-src 'self' 'unsafe-inline'", // Tailwind requires unsafe-inline
              "img-src 'self' data: https:",
              "font-src 'self' data:",
              "connect-src 'self' https://api.smarter-team.com",
              "frame-ancestors 'self'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join('; '),
          },
        ],
      },
    ]
  },
}

export default nextConfig
```

### Environment-Specific CORS

**Production:**

```python
CORS_ORIGINS=https://smarter-team.com,https://www.smarter-team.com
ALLOWED_HOSTS=api.smarter-team.com,smarter-team.com
```

**Staging:**

```python
CORS_ORIGINS=https://staging.smarter-team.com
ALLOWED_HOSTS=staging-api.smarter-team.com,staging.smarter-team.com
```

**Development:**

```python
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Verification

### Test CORS

```bash
# Test OPTIONS preflight request
curl -X OPTIONS https://api.smarter-team.com/api/leads \
  -H "Origin: https://smarter-team.com" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Expected headers:
# Access-Control-Allow-Origin: https://smarter-team.com
# Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
# Access-Control-Allow-Credentials: true
# Access-Control-Max-Age: 3600

# Test actual request
curl https://api.smarter-team.com/api/leads \
  -H "Origin: https://smarter-team.com" \
  -v

# Should include:
# Access-Control-Allow-Origin: https://smarter-team.com
```

### Test Security Headers

```bash
# Check all security headers
curl -I https://api.smarter-team.com/health

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
# Referrer-Policy: strict-origin-when-cross-origin

# Check frontend headers
curl -I https://smarter-team.com

# Should include similar security headers
```

### Use Security Scanners

```bash
# Test with Mozilla Observatory
curl https://observatory.mozilla.org/api/v1/analyze?host=api.smarter-team.com

# Test with SecurityHeaders.com
open "https://securityheaders.com/?q=https://api.smarter-team.com"
# Target: A or A+ rating

# Test with SSL Labs
open "https://www.ssllabs.com/ssltest/analyze.html?d=api.smarter-team.com"
# Target: A or A+ rating
```

### Test from Frontend

**Create test page `app/frontend/app/test-cors/page.tsx`:**

```typescript
'use client'

import { useState } from 'react'

export default function TestCORS() {
  const [result, setResult] = useState('')

  const testAPI = async () => {
    try {
      const response = await fetch('https://api.smarter-team.com/health', {
        credentials: 'include',
      })
      const data = await response.json()
      setResult('SUCCESS: ' + JSON.stringify(data))
    } catch (error) {
      setResult('ERROR: ' + (error as Error).message)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl mb-4">CORS Test</h1>
      <button onClick={testAPI} className="bg-blue-500 text-white px-4 py-2 rounded">
        Test API Call
      </button>
      <pre className="mt-4 p-4 bg-gray-100">{result}</pre>
    </div>
  )
}
```

Visit `https://smarter-team.com/test-cors` and click button. Should succeed.

## Security Header Checklist

- [x] **HSTS**: Force HTTPS for 1 year
- [x] **X-Frame-Options**: Prevent clickjacking
- [x] **X-Content-Type-Options**: Prevent MIME sniffing
- [x] **X-XSS-Protection**: Enable XSS filter
- [x] **CSP**: Restrict resource loading
- [x] **Referrer-Policy**: Control referrer information
- [x] **Permissions-Policy**: Disable unnecessary features
- [x] **CORS**: Allow only trusted origins

## Security Best Practices

1. **Whitelist origins**: Never use `*` in production
2. **Credentials**: Only enable if needed (cookies/auth)
3. **CSP**: Start strict, loosen as needed
4. **HSTS**: Include subdomains and preload
5. **Regular audits**: Use security scanning tools monthly

## Troubleshooting

**CORS errors in browser:**
- Verify origin is in allowed list
- Check credentials setting matches frontend
- Ensure preflight request succeeds
- Clear browser cache

**CSP violations:**
- Check browser console for CSP errors
- Adjust CSP policy to allow necessary resources
- Use CSP report-uri for monitoring
- Balance security vs functionality

**Headers not appearing:**
- Check middleware order (security first)
- Verify Nginx not stripping headers
- Test with curl vs browser
- Check Coolify reverse proxy config

## Notes

- **CORS**: Required for browser security
- **CSP**: Prevents XSS attacks
- **HSTS**: Prevents protocol downgrade attacks
- **Security headers**: Defense in depth strategy

## Next Steps

After configuring CORS and security:
1. Run security scan (Observatory, SecurityHeaders)
2. Test frontend-backend communication
3. Monitor for CSP violations
4. Document security configuration
5. **DEPLOYMENT COMPLETE** - All 19 tasks done!

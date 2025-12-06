# Task 222: Create Dockerfile for Next.js Frontend

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Create a multi-stage Dockerfile for the Next.js 15 frontend that builds a production-optimized image with React 19, implements static asset caching, and enables standalone output mode for minimal image size.

## Prerequisites

- [ ] Coolify instance running and accessible
- [ ] Docker installed locally for testing
- [ ] Next.js configured with standalone output mode
- [ ] Environment variables documented in .env.example

## Files to Create/Modify

- [ ] `app/frontend/Dockerfile`
- [ ] `app/frontend/.dockerignore`
- [ ] `app/frontend/next.config.mjs` (update for standalone mode)

## Implementation Checklist

### Phase 1: Configure Next.js for Standalone Output
- [ ] Update `next.config.mjs` with `output: 'standalone'`
- [ ] Verify build creates `.next/standalone` directory
- [ ] Test standalone build locally

### Phase 2: Create .dockerignore
- [ ] Exclude `node_modules`, `.next`, `out`
- [ ] Exclude `.git`, `.env`, `.env.*` (except .env.example)
- [ ] Exclude development files and documentation

### Phase 3: Create Multi-Stage Dockerfile
- [ ] Stage 1: Dependencies (install all deps)
- [ ] Stage 2: Builder (build Next.js app)
- [ ] Stage 3: Runner (minimal runtime image)
- [ ] Use `node:20-alpine` for smallest image
- [ ] Create non-root user
- [ ] Set up health check

## Configuration Details

### Update next.config.mjs

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,

  // Environment variables available to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Image optimization
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
  },
}

export default nextConfig
```

### Dockerfile Content

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps

# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Set environment for build
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

# Build Next.js app
RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner

WORKDIR /app

# Set environment
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start Next.js
CMD ["node", "server.js"]
```

### .dockerignore Content

```
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Next.js
.next/
out/
build/

# Testing
coverage/
.nyc_output/
__tests__/

# Environment
.env
.env.*
!.env.example

# Git
.git/
.gitignore

# Documentation
*.md
docs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Misc
.DS_Store
Thumbs.db
```

## Verification

```bash
# Build the Docker image locally
cd app/frontend
docker build -t smarter-team-frontend:test .

# Check image size (should be ~200-300MB)
docker images smarter-team-frontend:test

# Run container locally
docker run -d \
    -p 3000:3000 \
    --env-file .env.local \
    --name frontend-test \
    smarter-team-frontend:test

# Test home page
curl http://localhost:3000

# Test health endpoint
curl http://localhost:3000/api/health

# Check logs
docker logs frontend-test

# Test in browser
open http://localhost:3000

# Cleanup
docker stop frontend-test
docker rm frontend-test
```

## Notes

- **Standalone mode** reduces image size by ~40% (only includes necessary files)
- **Multi-stage builds** keep final image minimal (~200-300MB vs 1GB+ without)
- **Alpine Linux** base image is smallest Node.js option
- **Non-root user** improves security (Coolify requirement)
- **Health check** monitors Next.js server availability
- **Static assets** are copied separately for proper caching
- **Telemetry disabled** for privacy and performance
- **Node 20** is LTS version (supported until 2026-04-30)

## Performance Optimizations

1. **Build Time**: ~2-5 minutes depending on app size
2. **Image Size**: ~200-300MB (vs 1GB+ unoptimized)
3. **Startup Time**: ~2-5 seconds
4. **Memory Usage**: ~150-300MB (vs 500MB+ unoptimized)

## Coolify Integration

Once deployed to Coolify:
1. Coolify builds on each git push to main/develop
2. Health check monitored automatically
3. Auto-restart on failures
4. Logs in Coolify dashboard
5. Can enable CDN caching for static assets
6. SSL termination handled by Coolify

## Environment Variables for Production

Set in Coolify dashboard:
```bash
NEXT_PUBLIC_API_URL=https://api.smarter-team.com
NODE_ENV=production
PORT=3000
```

## Troubleshooting

**Build fails with "Cannot find module":**
- Ensure all dependencies in package.json
- Run `npm ci` locally to verify

**Health check fails:**
- Verify `/api/health` route exists
- Check server.js is running on port 3000

**Static assets not loading:**
- Verify `.next/static` is copied correctly
- Check public folder is copied

**Image too large:**
- Verify standalone mode is enabled
- Check .dockerignore excludes unnecessary files

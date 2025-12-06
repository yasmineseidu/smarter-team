# Frontend - Claude Instructions

<!-- AUTO-MANAGED: overview -->

## Overview

Next.js 15 frontend for Smarter Team dashboard. React 19 with TypeScript.

**Stack**: Next.js 15.0.0, React 19, TypeScript 5.6, Tailwind CSS 3.4, Vitest 3.0

<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: commands -->

## Commands

```bash
# Development
npm run dev               # Next.js dev server
npm run build             # Production build
npm start                 # Production server

# Quality
npm run lint              # ESLint
npm run typecheck         # TypeScript check
npm test                  # Vitest
npm run test:ui           # Vitest UI
npm run test:coverage     # Coverage report

# Setup
npm install               # Install dependencies
```

<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: structure -->

## Structure

```
app/                      # Next.js App Router
├── layout.tsx            # Root layout
├── page.tsx              # Home page
└── [routes]/             # Route segments

components/               # React components (to be created)
├── ui/                   # Base UI components
└── features/             # Feature-specific components

__tests__/
├── setup.ts              # Vitest global setup
└── unit/                 # Unit tests
```

<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: conventions -->

## Conventions

- TypeScript strict mode
- React 19 JSX transform (no React import needed)
- Tailwind CSS for styling
- Vitest + @testing-library/react for testing
- happy-dom as test environment
- ESLint with Next.js config
- Prettier for formatting
- Components: PascalCase files and names
- Hooks: `use` prefix, camelCase
<!-- END AUTO-MANAGED -->

<!-- MANUAL -->

## Notes

- See root CLAUDE.md for full project context
- E2E tests run in CI only (Playwright)
- No components created yet - use Tailwind + shadcn patterns when building
<!-- END MANUAL -->

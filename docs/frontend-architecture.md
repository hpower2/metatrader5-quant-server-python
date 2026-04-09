# Frontend Architecture

## Overview

The frontend lives in [apps/web](/home/irvine/metatrader5-quant-server-python/apps/web) as a standalone Next.js application using the App Router. It is structured for long-term maintainability around feature boundaries, shared design primitives, typed API contracts, and testable UI modules.

## Stack

- Next.js
- TypeScript with strict mode
- Tailwind CSS
- shadcn/ui-style primitives
- TanStack Query for server state
- Zustand for local UI-only state
- React Hook Form + Zod
- lightweight-charts and Recharts
- ESLint + Prettier
- Vitest + React Testing Library
- Playwright

## Folder Layout

- `app/`
  Route composition and the internal proxy endpoint at `app/api/control/[...path]`.
- `components/ui/`
  Generic reusable primitives.
- `components/shared/`
  Reusable dashboard-specific primitives like tables, selectors, badges, shells, and log viewers.
- `components/charts/`
  Domain-aware chart wrappers.
- `components/layouts/`
  App shell and layout chrome.
- `features/`
  Feature-owned modules for dashboard, market data, features explorer, datasets, backtests, paper trading, and admin. Each feature exposes a small public API through `features/<feature>/index.ts`.
- `lib/api/`
  Typed fetch layer and schemas.
- `lib/query/`
  Query client and keys.
- `lib/utils/`, `lib/formatters/`, `lib/constants/`, `lib/permissions/`
  Shared infra and presentation helpers.
- `hooks/`
  Cross-feature hooks.
- `stores/`
  Small client UI store.
- `schemas/`
  Shared runtime validation schemas.
- `types/`
  Shared TS interfaces.
- `styles/`
  Global tokens and theme CSS.
- `tests/`, `e2e/`
  Unit, component, and end-to-end test layers.

## Data Access

The browser never talks directly to `quant-api`. Instead, client-side requests go to the same-origin Next route:

- `/api/control/*`

That route proxies requests to:

- `QUANT_API_URL`

This keeps the browser-side API surface stable, avoids cross-origin problems, and works cleanly behind Traefik.

## State Management

- TanStack Query owns server state.
- Feature modules expose their own query or mutation hooks.
- Zustand is limited to sidebar and chart preference state.
- Form state is local and validated with Zod.
- URL query params own sharable instrument filters for exploration pages.

## Contracts and Mappers

- Feature forms map into typed request contracts through feature-local mapper utilities.
- Backtest responses now include structured equity-curve and trade-log data so charts and tables can render from real payloads instead of placeholder state.
- Shared form shells keep validation, labels, and feedback presentation consistent without pushing business logic into UI primitives.

## Developer Experience

- `apps/web/package.json` uses `next typegen && tsc --noEmit` for `typecheck` so route types stay in sync with App Router changes.
- A repo-level [.nvmrc](/home/irvine/metatrader5-quant-server-python/.nvmrc) pins the Node major version for local development.

## UI Principles

- Shared primitives are generic and reusable.
- Feature components own domain behavior.
- Pages mostly compose feature entrypoints.
- Chart transformation logic lives outside page components.
- Loading, empty, and error states are explicit.

## Runtime

The web app is containerized via [infra/docker/web.Dockerfile](/home/irvine/metatrader5-quant-server-python/infra/docker/web.Dockerfile) and served by the `web` service in [docker-compose.yml](/home/irvine/metatrader5-quant-server-python/docker-compose.yml).

Traefik routes the app using:

- `WEB_DOMAIN`

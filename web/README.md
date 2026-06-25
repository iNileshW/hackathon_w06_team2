# FOI Automation UI

React + Vite single-page app for visualising the FOI pipeline. Built with the
[GOV.UK Design System](https://design-system.service.gov.uk/) components and
[TanStack Query](https://tanstack.com/query/latest) for API calls.

## Run

Start the API first (see `../api/README.md`), then:

```bash
npm install        # also copies GOV.UK fonts/images into public/assets
npm run dev        # http://localhost:5173 (proxies /api -> :8000)
```

`npm run build` type-checks and produces a production bundle in `dist/`.

## What it does

- **Dashboard** (`/`) — table of FOI requests with a GOV.UK status tag
  (Not processed / Awaiting decision / Approved / Rejected / Modified).
- **Request detail** (`/requests/:id`) —
  - *Process request* runs the multi-agent pipeline.
  - Shows triage classification, compliance exemptions + RAG policy citations,
    the draft response letter, and the per-request cost breakdown.
  - **Approval gate**: approve / reject / modify with notes — the in-browser
    equivalent of the CLI's human-in-the-loop checkpoint.

## Structure

| Path | Role |
|------|------|
| `src/api/client.ts` | typed `fetch` wrappers |
| `src/api/queries.ts` | TanStack Query hooks (`useRequests`, `useProcess`, `useDecide`) |
| `src/pages/Dashboard.tsx` | request list |
| `src/pages/RequestDetail.tsx` | pipeline output + approval gate |
| `src/components/StatusTag.tsx` | status → GOV.UK tag |
| `src/types.ts` | shared types mirroring the API record |

GOV.UK styling is the compiled `govuk-frontend` CSS imported in `main.tsx`;
components use the design system's markup classes directly.

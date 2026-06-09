# MOXI Web Platform

This directory will contain the MOXI commercial web application:

- public website;
- customer console;
- admin console;
- deployment wizard;
- license management;
- server registry;
- support tickets;
- release and upgrade views.

Recommended stack:

- Next.js;
- TypeScript;
- Tailwind CSS;
- shadcn/ui;
- PostgreSQL;
- Prisma or Drizzle;
- Playwright.

This app must not contain Hermes runtime internals. It integrates with Hermes
through license files, server registration, release metadata, health summaries,
and support bundle workflows.

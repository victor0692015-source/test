# Deployment Guide

## Prerequisites
- Docker Desktop (for containerized run), or
- Node.js 20+ + npm + local PostgreSQL + local Redis (for non-Docker run)

## Option A — Run with Docker (recommended)
From the **project root** (`CRMTEST`, not `backend/`):

1. Create env files:
   - `cp backend/.env.example backend/.env`
   - `cp frontend/.env.example frontend/.env`
2. Start services:
   - `docker compose -f infra/docker/docker-compose.yml up -d --build`
3. Open apps:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:4000/api`

> If you are currently in `backend/`, go up one level first: `cd ..`.

## Option B — Run locally without Docker

1. Ensure Postgres and Redis are running on localhost:
   - Postgres: `localhost:5432`
   - Redis: `localhost:6379`
2. In backend:
   - `cd backend`
   - `cp .env.local.example .env`
   - `npm install`
   - `npm run prisma:generate`
   - `npm run prisma:migrate`
   - `npm run start:dev`
3. In a second terminal (from project root):
   - `cd frontend`
   - `cp .env.example .env`
   - `npm install`
   - `npm run dev`

## Common Issues
- `docker compose ... no such file`: you ran the command from `backend/` instead of project root.
- `P1001 Can't reach database at postgres:5432`: this host works only in Docker network; use `.env.local.example` for local run.
- `Could not find TypeScript configuration file tsconfig.json`: backend config files are required in Nest workspace.

## Production Notes
1. Rotate `JWT_SECRET` and `FIELD_ENCRYPTION_KEY` via secret manager.
2. Run migrations on deploy: `npm run prisma:migrate`.
3. Daily backups example:
   - `0 2 * * * pg_dump $DATABASE_URL > /backups/crm_$(date +\%F).sql`
4. Scale API/workers horizontally behind a load balancer.

# Deployment Guide

1. Create `.env` values:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `FIELD_ENCRYPTION_KEY`
   - `REDIS_URL`
2. Run migrations: `npm run prisma:migrate` in `backend`.
3. Start platform with Docker Compose:
   - `docker compose -f infra/docker/docker-compose.yml up -d --build`
4. Configure webhook URLs in Telegram/WhatsApp/Viber providers.
5. Enable daily backups using cron + pg_dump:
   - `0 2 * * * pg_dump $DATABASE_URL > /backups/crm_$(date +\%F).sql`
6. Scale API/workers horizontally by increasing service replicas.

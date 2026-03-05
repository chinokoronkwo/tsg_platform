# Snob Group Platform - Deployment Guide

## Prerequisites

- **Docker** and **Docker Compose** (v2+)
- **Domain name** with DNS access
- **Stripe** account (payments)
- **Twilio** account (SMS)
- **SendGrid** or Resend (email)
- **S3-compatible storage** (e.g. Cloudflare R2, AWS S3) for media
- **Meilisearch** (included in Docker Compose)

## Environment Variables Reference

Create a `.env.prod` file with the following variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_USER` | PostgreSQL username | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `POSTGRES_DB` | PostgreSQL database name | Yes |
| `DATABASE_URL` | Full asyncpg URL: `postgresql+asyncpg://user:pass@db:5432/dbname` | Yes |
| `REDIS_URL` | Redis URL: `redis://redis:6379/0` | Yes |
| `SECRET_KEY` | JWT signing key (use strong random string) | Yes |
| `CORS_ORIGINS` | Comma-separated allowed origins | Yes |
| `STRIPE_SECRET_KEY` | Stripe API secret key | For payments |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | For payments |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | For SMS |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | For SMS |
| `TWILIO_PHONE_NUMBER` | Twilio sending number | For SMS |
| `SENDGRID_API_KEY` | SendGrid API key | For email |
| `FROM_EMAIL` | Default sender email | Optional |
| `S3_ENDPOINT_URL` | S3 endpoint (e.g. R2) | For media |
| `S3_ACCESS_KEY_ID` | S3 access key | For media |
| `S3_SECRET_ACCESS_KEY` | S3 secret key | For media |
| `S3_BUCKET_NAME` | S3 bucket name | For media |
| `S3_PUBLIC_URL` | Public URL for media | Optional |
| `MEILISEARCH_MASTER_KEY` | Meilisearch master key | Yes (production) |
| `NEXT_PUBLIC_API_URL` | API URL for frontend (e.g. `https://api.yourdomain.com/api/v1`) | Yes |

## Docker Compose Deployment

### 1. Clone and configure

```bash
git clone <repo-url> sg_platform
cd sg_platform
cp .env.example .env.prod
# Edit .env.prod with production values
```

### 2. Build and start

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### 3. Run database migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Set `DATABASE_URL` for the exec context if needed:

```bash
docker-compose -f docker-compose.prod.yml exec -e DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dbname backend alembic upgrade head
```

### 4. Run data migration scripts (if migrating from WordPress)

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.migrate_data
# Or run individual scripts: migrate_users, migrate_products, etc.
```

## DNS Configuration

Point your domain to the server IP:

| Record | Type | Value |
|--------|------|-------|
| `yourdomain.com` | A | Server IP |
| `api.yourdomain.com` | A or CNAME | Server IP or load balancer |
| `admin.yourdomain.com` | A or CNAME | Server IP (if using subdomain for admin) |

Update `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` to match your domains.

## SSL Setup

### Option A: Let's Encrypt with Certbot

```bash
# Install certbot
apt install certbot

# Obtain certificate (standalone mode - stop nginx first)
certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Copy certs to nginx/ssl/
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/

# Uncomment SSL server block in nginx/nginx.prod.conf
# Restart nginx
```

### Option B: Cloudflare

Use Cloudflare as a proxy; SSL terminates at Cloudflare. Set SSL mode to "Full" or "Full (strict)" and use origin certificates if desired.

## Monitoring Setup

### Sentry (Error tracking)

Add to backend environment:

```
SENTRY_DSN=https://xxx@sentry.io/xxx
```

Install `sentry-sdk` and configure in `app/main.py`.

### Uptime monitoring

Use UptimeRobot, Pingdom, or similar to monitor:

- `https://yourdomain.com/api/health` (backend health)
- `https://yourdomain.com` (frontend)

## Backup Strategy

### Database

```bash
# Daily backup (add to cron)
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U snobgroup snobgroup | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Redis

Redis data is ephemeral for sessions/cache. For Celery task state, consider persistence; backups are optional.

### Media (S3)

Enable versioning and lifecycle policies on your S3 bucket. Use cross-region replication for critical assets.

## Production Checklist

- [ ] Set strong `SECRET_KEY` and `POSTGRES_PASSWORD`
- [ ] Configure `CORS_ORIGINS` with exact production URLs
- [ ] Set `DEBUG=false`
- [ ] Configure SSL/TLS
- [ ] Run `alembic upgrade head`
- [ ] Run data migration scripts if applicable
- [ ] Set up monitoring (Sentry, uptime)
- [ ] Configure backup cron jobs
- [ ] Test Stripe webhooks (use ngrok for local testing)
- [ ] Verify Twilio/SendGrid credentials

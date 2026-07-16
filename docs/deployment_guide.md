# EquityIQ Deployment Guide

## Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- PostgreSQL 15+
- Redis 7+

## Environment Setup
Create a `.env.production` file based on `.env.example`:
```bash
cp .env.example .env.production
```
Configure your secure `SECRET_KEY`, database URLs, and API keys.

## Backend Deployment
1. Build the production Docker image:
   ```bash
   docker build -t equityiq-backend ./backend
   ```
2. Run database migrations:
   ```bash
   docker run --env-file .env.production equityiq-backend alembic upgrade head
   ```
3. Start the backend service and celery workers:
   ```bash
   docker-compose -f infra/docker-compose.prod.yml up -d
   ```

## Frontend Deployment
1. Install dependencies:
   ```bash
   cd frontend
   npm ci
   ```
2. Build the Next.js application:
   ```bash
   npm run build
   ```
3. Start the production server:
   ```bash
   npm start
   ```

## Nginx / Reverse Proxy Configuration
Route traffic to:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api`

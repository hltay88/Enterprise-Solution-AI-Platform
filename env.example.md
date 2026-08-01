# Copy to .env for local Docker Compose (do not commit .env)

# Database
DATABASE_URL=postgresql://atlas:atlas@db:5432/atlas
POSTGRES_USER=atlas
POSTGRES_PASSWORD=atlas
POSTGRES_DB=atlas

# Auth (ATLAS-011)
SECRET_KEY=change-me-in-local-dev
JWT_EXPIRE_MINUTES=60
DEMO_USER_EMAIL=demo@atlas.local
DEMO_USER_PASSWORD=changeme
DEMO_USER_NAME=Atlas Demo

# AI — default OpenAI (ATLAS-012)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Optional future providers
ANTHROPIC_API_KEY=

# File storage (ATLAS-013)
STORAGE_PATH=/app/storage/uploads
MAX_UPLOAD_MB=10

# Backend
CORS_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY --from=frontend /build/dist frontend/dist
WORKDIR /app/backend
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

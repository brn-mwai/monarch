# Monarch web frontend -- build for linux/amd64 (hackathon container gate):
#   docker build --platform linux/amd64 -t monarch-web apps/web
# The app runs in synthetic-demo mode with no env vars; set
# NEXT_PUBLIC_INFERENCE_URL to point at the FastAPI service for live TRIBE.
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:20-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Clerk/Convex keys are optional at build time; the app degrades to keyless
# dev + synthetic data when they are absent.
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS run
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/public ./public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]

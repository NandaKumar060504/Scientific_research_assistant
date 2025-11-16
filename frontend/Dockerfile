FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Final stage - just holds the built files
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/dist ./dist
# Keep container running with a simple sleep command
CMD ["sleep", "infinity"]
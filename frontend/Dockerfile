# ============================================================================
# Multi-stage build for Agent Foundry Frontend
# ============================================================================

FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# ============================================================================
# Dependencies stage
# ============================================================================
FROM base as deps

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# ============================================================================
# Development stage
# ============================================================================
FROM base as development

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Set environment
ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1

# Run development server
CMD ["npm", "run", "dev"]

# ============================================================================
# Build stage
# ============================================================================
FROM base as builder

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Set environment
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Build application
RUN npm run build

# ============================================================================
# Production stage
# ============================================================================
FROM base as production

# Set to production
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

USER nextjs

# Expose port
EXPOSE 3000

# Run production server
CMD ["npm", "start"]

# ============================================================================
# Default to development
# ============================================================================
FROM development

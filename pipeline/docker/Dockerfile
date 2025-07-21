FROM node:18.19-alpine

ARG APP_NAME
RUN corepack enable

# Install any extra packages needed for debugging or runtime
RUN apk add --no-cache \
    g++ \
    make \
    py3-pip \
    libc6-compat \
    bash \
    curl \
    wget \
    netcat-openbsd \
    iputils \
    bind-tools \
    musl-dev \
    openssl-dev \
    gcc \
    cargo \
    ca-certificates

WORKDIR /app

RUN mkdir /app/scripts

# Create application user (already exists in base, but safe)
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Set permissions
RUN chmod -R 755 /app && chown -R nextjs:nodejs /app
RUN update-ca-certificates

COPY  ./app /app
RUN chown -R nextjs:nodejs /app/.next
USER nextjs



# Fail the build early if the Next.js binary is missing
RUN test -x /app/node_modules/.bin/next


RUN echo ${APP_NAME}

ENV APP_NAME=${APP_NAME}
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

EXPOSE 3000

# Start app
CMD ["npm", "start"]

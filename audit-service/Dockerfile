FROM node:22-alpine AS build

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY audit-service/package.json ./audit-service/package.json
RUN pnpm install --frozen-lockfile --filter @e-commerce-shop-v2/audit-service...
COPY audit-service ./audit-service
RUN pnpm --filter @e-commerce-shop-v2/audit-service run build

FROM node:22-alpine AS runtime

ENV NODE_ENV=production
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY audit-service/package.json ./audit-service/package.json
RUN pnpm install --frozen-lockfile --prod --filter @e-commerce-shop-v2/audit-service...
COPY --from=build /workspace/audit-service/dist ./audit-service/dist
WORKDIR /workspace/audit-service
USER node
CMD ["node", "dist/main.js"]
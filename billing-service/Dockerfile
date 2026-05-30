FROM node:22-alpine AS build

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY billing-service/package.json ./billing-service/package.json
RUN pnpm install --frozen-lockfile --filter @e-commerce-shop-v2/billing-service...
COPY billing-service ./billing-service
RUN pnpm --filter @e-commerce-shop-v2/billing-service run build

FROM node:22-alpine AS runtime

ENV NODE_ENV=production
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY billing-service/package.json ./billing-service/package.json
RUN pnpm install --frozen-lockfile --prod --filter @e-commerce-shop-v2/billing-service...
COPY --from=build /workspace/billing-service/dist ./billing-service/dist
WORKDIR /workspace/billing-service
USER node
CMD ["node", "dist/main.js"]
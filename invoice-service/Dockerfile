FROM node:22-alpine AS build

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY invoice-service/package.json ./invoice-service/package.json
RUN pnpm install --frozen-lockfile --filter @e-commerce-shop-v2/invoice-service...
COPY invoice-service ./invoice-service
RUN pnpm --filter @e-commerce-shop-v2/invoice-service run build

FROM node:22-alpine AS runtime

ENV NODE_ENV=production
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY invoice-service/package.json ./invoice-service/package.json
RUN pnpm install --frozen-lockfile --prod --filter @e-commerce-shop-v2/invoice-service...
COPY --from=build /workspace/invoice-service/dist ./invoice-service/dist
WORKDIR /workspace/invoice-service
USER node
CMD ["node", "dist/main.js"]
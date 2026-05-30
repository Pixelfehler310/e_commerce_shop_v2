FROM node:22-alpine AS build

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontends/simulation-panel/package.json ./frontends/simulation-panel/package.json
RUN pnpm install --frozen-lockfile --filter @e-commerce-shop-v2/simulation-panel...
COPY frontends/simulation-panel ./frontends/simulation-panel
ARG VITE_SHOP_API_BASE_URL=http://localhost:3000
ENV VITE_SHOP_API_BASE_URL=$VITE_SHOP_API_BASE_URL
RUN pnpm --filter @e-commerce-shop-v2/simulation-panel run build

FROM nginx:1.27-alpine AS runtime

COPY frontends/simulation-panel/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/frontends/simulation-panel/dist /usr/share/nginx/html
EXPOSE 80
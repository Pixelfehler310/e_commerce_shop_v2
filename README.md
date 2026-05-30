# E-Commerce Shop V2

Scaffold nach dem Konzept in `konzept/`. Das Repository ist als pnpm-Monorepo organisiert. Die Service-Ordner enthalten aktuell nur NestJS-Endpunktvertraege und Docker-Build-Dateien. Fachlogik, Persistenz, Guards, Clients, Migrationen und Frontends sind bewusst noch nicht implementiert.

## Struktur

```text
/
├── docker-compose.yml
├── .env.example
├── shop-service/
├── warehouse-service/
├── billing-service/
├── invoice-service/
├── audit-service/
├── frontends/
└── konzept/
```

## Lokaler Start

```bash
pnpm install
pnpm build
cp .env.example .env
docker compose build
docker compose up
```

Gezielte Service-Builds laufen ueber Filter, zum Beispiel:

```bash
pnpm build:shop
pnpm --filter @e-commerce-shop-v2/billing-service run build
```

Alle fachlichen Endpunkte antworten als Contract-Stubs mit `501 Not Implemented`. Nur `/health` ist minimal umgesetzt, damit Docker-Healthchecks funktionieren.
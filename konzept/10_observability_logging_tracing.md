# Observability, Logging und Tracing

## Ziel

Observability macht das Verhalten des verteilten Systems nachvollziehbar. Für dieses Projekt ist sie besonders wichtig, weil Fehlerpfade und Nebenläufigkeit live demonstriert werden sollen. Logs, Audit-Snapshots und Dashboards müssen dieselbe `correlationId` verwenden, damit ein Bestellvorgang vollständig rekonstruiert werden kann.

## Grundelemente

| Element | Zweck |
| --- | --- |
| Strukturierte JSON-Logs | Maschinenlesbare Diagnose pro Service. |
| `correlationId` | Verbindung aller Logs, Events und Requests einer Bestellung. |
| Audit-Snapshots | Fachlich-technische Zustandsübergänge. |
| Loki | Zentraler Log-Speicher. |
| Grafana | Dashboards für Bestellungen, Fehler und Payment-Ergebnisse. |
| Optional OpenTelemetry | Verteilte Traces und Spans. |

## JSON-Logformat

Jeder Logeintrag enthält mindestens:

```json
{
  "timestamp": "2026-05-29T12:00:00.000Z",
  "level": "info",
  "service": "shop-service",
  "message": "Order status changed",
  "correlationId": "ord-2026-0001",
  "context": {
    "from": "RESERVED",
    "to": "BOOKING_PENDING",
    "orderId": "ord-internal-123"
  }
}
```

## Pflichtfelder

| Feld | Pflicht | Beschreibung |
| --- | --- | --- |
| `timestamp` | Ja | ISO-Zeitstempel. |
| `level` | Ja | `debug`, `info`, `warn`, `error`. |
| `service` | Ja | Service-Name. |
| `message` | Ja | Kurze menschenlesbare Aussage. |
| `correlationId` | Für Prozesslogs ja | Verbindet Bestellfluss. |
| `requestId` | Optional | Einzelner HTTP-Request. |
| `context` | Ja | Strukturierte Zusatzdaten. |
| `error` | Bei Fehlern | Code, Message, Stack nur intern. |

## Correlation-ID-Fluss

1. Externer Request bringt `X-Correlation-Id` mit oder Shop-Service erzeugt eine neue.
2. Shop-Service schreibt sie in Request Context und Logs.
3. Shop-Service sendet sie in HTTP-Headern an Warehouse und Billing.
4. Services übernehmen sie in Logs, Audit-Events und Folgeaufrufen.
5. RabbitMQ-Messages enthalten sie als Property und im Payload.
6. Invoice und Audit übernehmen sie aus Eventdaten.

## Log-Level-Konvention

| Level | Verwendung |
| --- | --- |
| `debug` | Detaildaten für lokale Entwicklung, z. B. Provider-Stub-Entscheidung. |
| `info` | Normale Zustandswechsel, erfolgreiche Service-Aufrufe. |
| `warn` | Fachlich erwartbare Probleme, z. B. Payment abgelehnt oder Out of Stock. |
| `error` | Technische Fehler, unerwartete Exceptions, endgültige Retry-Fehler. |

## Was nicht geloggt wird

Nicht in Logs gehören:

- Passwörter.
- JWTs.
- Authorization Header.
- Vollständige Zahlungsdaten.
- Datenbankpasswörter.
- Provider-Secrets.

## Loki-Anbindung

Für Docker Compose bietet sich Promtail oder ein Loki-kompatibler Logging Driver an. Jeder Container schreibt JSON auf stdout. Loki sammelt die Logs und Grafana visualisiert sie.

Empfohlene Labels:

- `service`.
- `environment`.
- `level`.
- `container`.

`correlationId` sollte im Loginhalt filterbar sein, aber nicht unbedingt als Label verwendet werden, weil hohe Kardinalität in Loki problematisch ist.

## Grafana-Dashboard

Das zentrale Dashboard sollte mindestens vier Bereiche besitzen.

### Bestellvolumen

- Bestellungen pro Minute oder Intervall.
- Erfolgreiche vs. fehlgeschlagene Bestellungen.
- Anzahl offener `PAYMENT_PENDING`-Bestellungen.

### Fehlerrate nach Service

- Fehlerlogs nach `service` gruppiert.
- Warnungen getrennt von echten technischen Fehlern.
- Top-Fehlercodes aus Problem Details.

### Payment-Ergebnisse

- `SUCCEEDED`, `FAILED`, `PENDING`, `REFUNDED`.
- Provider-Aufteilung.
- Webhook-Latenz, wenn gemessen.

### Saga-Timeline-Suche

- Textfeld für `correlationId`.
- Logliste über alle Services.
- Link zur Admin-Audit-Timeline.

## Beispiel-LogQL-Abfragen

Alle Logs zu einer Bestellung:

```logql
{environment="local"} |= "ord-2026-0001"
```

Fehler pro Service:

```logql
sum by (service) (count_over_time({environment="local"} | json | level="error" [5m]))
```

Payment-Ablehnungen:

```logql
{service="billing-service"} | json | context_status="FAILED"
```

## Metriken

Auch wenn das PDF vor allem Logging nennt, sind einfache Metriken hilfreich.

Empfohlene Metriken:

| Metrik | Typ | Bedeutung |
| --- | --- | --- |
| `orders_created_total` | Counter | Anzahl gestarteter Bestellungen. |
| `orders_completed_total` | Counter | Erfolgreiche Bestellungen. |
| `orders_failed_total` | Counter | Fehlgeschlagene Bestellungen nach Grund. |
| `payment_attempts_total` | Counter | Zahlungsversuche nach Provider und Ergebnis. |
| `warehouse_reservations_total` | Counter | Reservierungen nach Ergebnis. |
| `invoice_generation_failures_total` | Counter | Fehler der Rechnungserstellung. |
| `saga_duration_seconds` | Histogram | Dauer des Bestellprozesses. |

## Tracing optional

OpenTelemetry kann den Zusammenhang der synchronen HTTP-Aufrufe noch klarer zeigen.

Span-Idee:

```text
POST /v1/orders
  -> warehouse.reserve
  -> billing.charge
  -> warehouse.book
  -> audit.publish
```

Für das Projekt ist Tracing optional, aber ein kleiner Trace-Auszug in der Demo wäre ein starker Bonus.

## Zusammenspiel mit Audit

Logs und Audit haben unterschiedliche Aufgaben:

| Audit | Logs |
| --- | --- |
| Fachlich relevante Zustandsübergänge. | Technische Diagnose. |
| Append-only und langfristig nachvollziehbar. | Detailliert, filterbar, volatil. |
| Wird im Admin Dashboard gezeigt. | Wird in Grafana analysiert. |
| Eher grob, dafür stabil. | Eher detailliert, dafür technisch. |

## Demo-Nutzung

Für jede Live-Demo sollte direkt nach Start die `correlationId` sichtbar sein. Diese ID wird dann in drei Ansichten verwendet:

- Admin Dashboard für Audit-Timeline.
- Grafana für Logs.
- Frontend-Statusseite für Nutzersicht.

## Abnahmekriterien

- Jeder Service schreibt JSON-Logs.
- Jeder Bestellprozess ist über eine `correlationId` in allen beteiligten Services auffindbar.
- Grafana zeigt Bestellungen pro Intervall, Fehlerrate nach Service und Payment-Ergebnisse.
- Fehlerpfade erzeugen sowohl Audit-Snapshots als auch aussagekräftige Logs.
- Logs enthalten keine Secrets oder vollständigen Zahlungsdaten.
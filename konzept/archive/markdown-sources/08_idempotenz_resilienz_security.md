# Idempotenz, Resilienz und Security

## Ziel dieses Kapitels

Dieses Kapitel bündelt die technischen Querschnittsthemen, die den verteilten Bestellprozess stabil machen: Idempotenz gegen Doppelverarbeitung, Resilienz gegen Ausfälle und Security für Rollen, Tokens und interne Grenzen.

## Idempotenz bei `POST /v1/orders`

Der kritischste externe Endpunkt ist `POST /v1/orders`. Nutzer können doppelt klicken, Browser können Requests wiederholen und Netzwerke können Antworten verlieren. Trotzdem darf dieselbe Bestellung nicht doppelt ausgeführt werden.

## Idempotenz-Key

Der Client sendet:

```http
X-Idempotency-Key: 7f4a2d12-f3c3-42f1-a1c2-4bd0e90f6f1b
```

Regeln:

- Der Header ist verpflichtend.
- Die Eindeutigkeit gilt pro Nutzer, nicht global.
- Der Key wird für eine begrenzte Zeit gespeichert, z. B. 24 Stunden.
- Der Request-Body-Hash wird mitgespeichert, damit derselbe Key nicht für andere Inhalte verwendet wird.

## Redis-basierter Ablauf

Empfohlene Schlüssel:

```text
idempotency:{userId}:{key}:lock
idempotency:{userId}:{key}:response
idempotency:{userId}:{key}:requestHash
```

Ablauf:

1. Body normalisieren und Hash berechnen.
2. Prüfen, ob eine gespeicherte Antwort existiert.
3. Falls ja: Hash vergleichen und gespeicherte Antwort zurückgeben.
4. Falls nein: Lock per `SET NX PX` setzen.
5. Bei Lock-Erfolg: Saga starten.
6. Bei Lock-Konflikt: Statuslink oder `409` mit `PROCESSING` zurückgeben.
7. Nach Abschluss: Response und Request-Hash speichern.
8. Lock entfernen oder bis TTL auslaufen lassen.

## Gespeicherte Idempotenzantwort

Die gespeicherte Antwort sollte enthalten:

- HTTP-Status.
- Response-Body.
- `correlationId`.
- finaler oder aktueller Order-Status.
- Zeitpunkt.
- Request-Hash.

Dadurch kann der zweite Request wirklich dasselbe Ergebnis liefern, ohne die Saga erneut zu starten.

## Idempotenz interner Endpunkte

Auch interne Kommandos müssen wiederholbar sein, da Timeouts und Retries auftreten können.

| Endpunkt | Idempotenzregel |
| --- | --- |
| Warehouse Reservation | Bestehende Reservierung zu `correlationId` zurückgeben. |
| Warehouse Cancel | Bereits stornierte Reservierung als Erfolg melden. |
| Warehouse Booking | Bereits gebuchte Reservierung als Erfolg melden. |
| Billing Charge | Bestehenden Payment-Datensatz zu `correlationId` zurückgeben. |
| Billing Refund | Bestehenden Refund zu `correlationId` zurückgeben. |
| Invoice Consumer | Bereits erzeugte Rechnung nicht erneut schreiben. |

## Retry-Strategien

Retries dürfen keine fachlichen Doppelwirkungen erzeugen. Deshalb gilt: erst Idempotenz, dann Retry.

Empfohlene Policies:

| Operation | Retry | Backoff | Besonderheit |
| --- | --- | --- | --- |
| Warehouse Reservation | 1 bis 2 | kurz, z. B. 100/300 ms | Nur bei technischen Fehlern, nicht bei `OUT_OF_STOCK`. |
| Billing Charge | 1 bis 2 | 300/800 ms | Danach Statusabfrage, kein Blind-Double-Charge. |
| Billing Refund | 3 | 500/1500/3000 ms | Bei endgültigem Fehler manuelle Prüfung. |
| Invoice Generation | 3 | 1/5/15 s | Circuit Breaker schützt vor Dauerausfall. |
| Audit Publish | mehrere | exponentiell | Business-Prozess nicht dauerhaft blockieren. |

## Circuit Breaker am Invoice-Service

Der Invoice-Service kann ausfallen, ohne dass die Zahlung rückgängig gemacht wird. Ein Circuit Breaker verhindert, dass das System in schneller Folge weiter fehlerhafte Aufrufe versucht.

Empfohlene Parameter:

| Parameter | Wert |
| --- | --- |
| Fehlergrenze | 3 aufeinanderfolgende Fehler. |
| Open-Dauer | 30 Sekunden. |
| Half-Open-Test | 1 Testverarbeitung. |
| Retry pro Event | mindestens 3 Versuche. |
| Audit | Jeder Zustandswechsel wird als Snapshot gespeichert. |

Zustände:

- `CLOSED`: Verarbeitung läuft normal.
- `OPEN`: Neue Verarbeitungen werden abgewiesen oder verzögert.
- `HALF_OPEN`: Einzelner Test entscheidet über Rückkehr zu `CLOSED`.

## Resilienz bei RabbitMQ

Für RabbitMQ sollten genutzt werden:

- Durable Exchanges und Queues.
- Persistent Messages für kritische Events.
- Dead-Letter-Queues für nicht verarbeitbare Nachrichten.
- Consumer-Acks erst nach erfolgreicher Verarbeitung.
- Reconnect-Logik bei Broker-Ausfall.

Empfohlene Queues:

| Queue | Consumer | Zweck |
| --- | --- | --- |
| `invoice.payment-succeeded` | Invoice-Service | Rechnungserstellung. |
| `audit.domain-events` | Audit-Service | Snapshot-Persistierung. |
| `shop.payment-updates` | Shop-Service | Fortsetzung asynchroner Payment-Sagas. |
| `*.dlq` | Admin/Debug | Fehlerhafte Nachrichten untersuchen. |

## Authentifizierung

Der Shop-Service stellt JWTs aus. Der Token enthält mindestens:

```json
{
  "sub": "usr-123",
  "email": "kunde@example.local",
  "roles": ["CUSTOMER"],
  "iat": 1780000000,
  "exp": 1780003600
}
```

Sicherheitsregeln:

- Passwörter werden mit einem sicheren Hashverfahren gespeichert.
- JWT Secret kommt aus Umgebungsvariablen.
- Token-Laufzeit ist begrenzt.
- Rollen werden serverseitig geprüft, nicht nur im Frontend versteckt.
- Admin- und Simulation-Endpunkte sind besonders restriktiv geschützt.

## Autorisierung

| Bereich | Rolle |
| --- | --- |
| Bestellung auslösen | `CUSTOMER` |
| Eigene Bestellung ansehen | `CUSTOMER` |
| Alle Bestellungen ansehen | `ADMIN` |
| Produkt erstellen | `ADMIN` |
| Bestand ändern | `LOGISTICS`, optional `ADMIN` |
| Simulation starten | `ADMIN` |
| Audit-Timeline ansehen | `ADMIN` |

## Guards in NestJS

Empfohlene Struktur:

- `JwtAuthGuard` validiert Token.
- `RolesGuard` prüft Rollenmetadaten.
- `CorrelationIdInterceptor` stellt `X-Correlation-Id` sicher.
- `ProblemDetailsExceptionFilter` normalisiert Fehlerantworten.
- `IdempotencyInterceptor` oder Middleware schützt Order-Endpoint.

## Interne Service-Security

Für das Uni-Projekt reicht meist Docker-Netzwerkisolation plus klare Portfreigaben. Trotzdem sollte das Konzept zeigen, dass interne Endpunkte nicht beliebig offen sind.

Mögliche Maßnahmen:

- Interne Services veröffentlichen keine Ports auf den Host, wenn nicht nötig.
- Shop-Service nutzt interne Docker-DNS-Namen.
- Interne Requests tragen ein Service-Token.
- Webhook-Endpunkte prüfen simulierte Provider-Signaturen.
- RabbitMQ-Zugangsdaten kommen aus `.env`.

## Validierung und Sanitizing

- DTOs validieren Typen, Pflichtfelder, Minimal- und Maximalwerte.
- Mengen sind Integer und positiv.
- Geldbeträge werden als Decimal/Numeric behandelt.
- IDs werden als UUID oder definierte Stringform validiert.
- Fehlerdetails enthalten keine Secrets.
- Logs maskieren Tokens, Zahlungsdaten und Passworthashes.

## Problem Details

Alle Services geben Fehler in einheitlicher Form zurück. Typische Codes:

| Code | HTTP | Bedeutung |
| --- | --- | --- |
| `VALIDATION_FAILED` | 400 | Request ungültig. |
| `UNAUTHORIZED` | 401 | Kein gültiger Token. |
| `FORBIDDEN` | 403 | Rolle reicht nicht. |
| `OUT_OF_STOCK` | 409 | Lagerbestand nicht ausreichend. |
| `IDEMPOTENCY_CONFLICT` | 409 | Gleicher Key, anderer Request-Body. |
| `PAYMENT_DECLINED` | 402 oder 409 | Zahlung abgelehnt. |
| `DEPENDENCY_UNAVAILABLE` | 503 | Interner Zielservice nicht erreichbar. |
| `MANUAL_REVIEW_REQUIRED` | 500/409 | Kompensation unklar. |

## Secrets und Konfiguration

Niemals hartcodieren:

- JWT Secret.
- Datenbankpasswörter.
- RabbitMQ-Zugangsdaten.
- Redis-URL mit Passwort.
- simulierte Provider-Signatur-Secrets.

Konfiguration gehört in `.env` und Docker-Compose-Environment. Für die Abgabe sollte eine `.env.example` ohne echte Secrets vorhanden sein.

## Resilienz-Abnahmekriterien

- Doppelter Order-Request erzeugt keine zweite Order.
- Doppelte Webhooks erzeugen keine zweite Zahlung oder Rechnung.
- Invoice-Ausfall öffnet den Circuit Breaker nach drei Fehlern.
- Circuit-Breaker-Zustandswechsel erscheinen in Audit und Logs.
- Technische Timeouts führen nicht zu Blind-Doppelbuchungen.
- Simulation-Endpunkte sind nur mit Admin-Rolle erreichbar.
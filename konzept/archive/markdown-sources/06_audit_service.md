# Audit-Service

## Rolle im Gesamtsystem

Der Audit-Service ist der neutrale, append-only Speicher für technische und fachliche Zustandsübergänge. Er besitzt kein Business-Wissen und entscheidet nicht, ob ein Vorgang korrekt ist. Seine Aufgabe ist die unveränderliche Dokumentation dessen, was die Services melden.

## Grundprinzipien

- Snapshots werden nur eingefügt, niemals verändert oder gelöscht.
- Jeder Snapshot gehört zu einer `correlationId`.
- Jeder Snapshot enthält ein `eventType` und einen JSON-Payload.
- Snapshots können über `previousEventId` verkettet werden.
- Der Service bietet Lesemodelle für Admin Dashboard und Debugging.
- Echtzeit-Aktualisierung erfolgt über SSE oder WebSocket.

## API

| Methode | Pfad | Rolle/Aufrufer | Beschreibung |
| --- | --- | --- | --- |
| `POST` | `/v1/audit/snapshots` | Interne Services | Fügt einen neuen Snapshot hinzu. |
| `GET` | `/v1/audit/orders/{correlationId}` | `ADMIN` | Liefert die chronologische Historie einer Bestellung. |
| `GET` | `/v1/audit/stream` | `ADMIN` | Streamt neue Snapshots für das Dashboard. |
| `GET` | `/v1/audit/search` | `ADMIN` | Filtert Snapshots nach Typ, Service, Zeitraum oder Status. |

## Snapshot-Schema

```json
{
  "id": "evt-123",
  "correlationId": "ord-2026-0001",
  "eventType": "PaymentSucceeded",
  "sourceService": "billing-service",
  "timestamp": "2026-05-29T12:00:00.000Z",
  "previousEventId": "evt-122",
  "payload": {
    "paymentId": "pay-123",
    "provider": "stripe-sim",
    "amountGross": 259.98,
    "currency": "EUR"
  },
  "metadata": {
    "schemaVersion": 1,
    "traceId": "trace-abc",
    "spanId": "span-def"
  }
}
```

## Datenmodell

### `audit_snapshots`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Snapshot-ID. |
| `correlation_id` | Text | Prozess-ID. |
| `event_type` | Text | Fachlicher oder technischer Eventtyp. |
| `source_service` | Text | Meldender Service. |
| `timestamp` | Timestamp | Zeitpunkt des Ereignisses. |
| `payload` | JSONB | Eventdaten. |
| `previous_event_id` | UUID nullable | Verkettung innerhalb derselben `correlationId`. |
| `metadata` | JSONB | Trace, Schema, technische Zusatzdaten. |
| `inserted_at` | Timestamp | Zeitpunkt der Persistierung. |

## Indizes

Empfohlene Datenbankindizes:

```sql
CREATE INDEX idx_audit_correlation_time
ON audit_snapshots (correlation_id, timestamp);

CREATE INDEX idx_audit_event_type
ON audit_snapshots (event_type);

CREATE INDEX idx_audit_source_service
ON audit_snapshots (source_service);

CREATE INDEX idx_audit_payload_gin
ON audit_snapshots USING gin (payload);
```

## Append-only-Schutz

Der Append-only-Charakter sollte nicht nur in der Applikation, sondern zusätzlich in der Datenbank abgesichert werden.

Empfohlene Maßnahmen:

- Keine Repository-Methoden für Update oder Delete anbieten.
- Datenbankrolle der Anwendung erhält nur `INSERT` und `SELECT`.
- Optional Trigger definieren, die `UPDATE` und `DELETE` blockieren.
- Migrationen für Audit-Tabellen besonders restriktiv behandeln.

## Snapshot-Verkettung

`previousEventId` macht die Timeline nachvollziehbarer. Beim Einfügen eines neuen Snapshots kann der Audit-Service den letzten Snapshot zur `correlationId` suchen und die neue Zeile darauf verweisen lassen.

Wichtig:

- Die Verkettung ist hilfreich, aber nicht die einzige Sortierung.
- Chronologische Anzeige sortiert primär nach `timestamp`, sekundär nach `inserted_at`.
- Bei parallelen Events können zwei Snapshots denselben Vorgänger haben. Das ist zulässig und wird in der UI als Verzweigung oder zeitgleiche Ereignisse sichtbar.

## Event-Annahme

Interne Services können Snapshots synchron per HTTP oder asynchron über RabbitMQ liefern. Für das Projekt ist eine Kombination sinnvoll:

- Kritische Prozess-Snapshots können direkt vom Service an RabbitMQ publiziert werden.
- Der Audit-Service konsumiert diese Events und persistiert sie.
- Ein HTTP-Endpunkt bleibt für einfache Integration, Tests und Simulation nutzbar.

## Validierung

Der Audit-Service validiert nur technische Mindestanforderungen:

- `correlationId` vorhanden.
- `eventType` vorhanden.
- `sourceService` bekannt oder als Text gesetzt.
- `timestamp` parsebar.
- `payload` ist valides JSON.
- Payload-Größe bleibt unter definierter Grenze.

Er validiert bewusst nicht, ob zum Beispiel `PaymentSucceeded` fachlich nach `ReservationCreated` kommen muss. Diese Interpretation gehört in Admin-Auswertung oder Tests, nicht in den Audit-Service.

## Stream für Admin Dashboard

`GET /v1/audit/stream` liefert neue Snapshots in Echtzeit.

SSE-Beispiel:

```text
event: audit.snapshot
id: evt-123
data: {"correlationId":"ord-2026-0001","eventType":"PaymentSucceeded"}
```

Empfohlenes Verhalten:

- Client kann über `Last-Event-ID` reconnecten.
- Stream kann nach `correlationId` gefiltert werden.
- Heartbeats verhindern, dass Proxies die Verbindung schließen.
- Admin Dashboard aktualisiert Timeline und Statuschips live.

## Lesemodelle

Der Audit-Service kann einfache Read-Model-Aufbereitung anbieten, ohne Business-Entscheidungen zu treffen.

### Timeline pro Bestellung

Antwort:

```json
{
  "correlationId": "ord-2026-0001",
  "snapshots": [
    {
      "eventType": "OrderCreated",
      "sourceService": "shop-service",
      "timestamp": "2026-05-29T12:00:00.000Z",
      "payload": {}
    }
  ]
}
```

### Aggregierte Übersicht

Mögliche Filter:

- Zeitraum.
- Eventtyp.
- Service.
- Endstatus.
- Fehlercode im Payload.
- `correlationId`.

## Relevante Eventtypen

| Service | Eventtypen |
| --- | --- |
| Shop | `OrderCreated`, `OrderCompleted`, `OrderFailedOutOfStock`, `OrderRollbackCompleted`. |
| Warehouse | `ReservationCreated`, `ReservationRejected`, `ReservationCancelled`, `StockBooked`. |
| Billing | `PaymentInitiated`, `PaymentPending`, `PaymentSucceeded`, `PaymentFailed`, `PaymentRefunded`. |
| Invoice | `InvoiceGenerated`, `InvoiceGenerationFailed`, `CircuitBreakerStateChanged`. |
| Simulation | `FailureModeEnabled`, `ConcurrencyTestStarted`, `WebhookDelayChanged`. |

## Datenschutz und Maskierung

Auch in einem Simulationsprojekt sollten Audit-Payloads keine sensiblen Rohdaten enthalten.

Maskiert oder ausgelassen werden:

- Passwörter.
- Tokens.
- Vollständige Zahlungsdaten.
- Authorization Header.
- Interne Secrets.

## Betriebliches Verhalten bei Ausfall

Der Audit-Service darf den Bestellprozess nicht dauerhaft blockieren. Wenn Audit temporär nicht erreichbar ist, sollen Services Events retrybar puffern oder über RabbitMQ zustellen. Für die Demo ist wichtig, diesen Kompromiss zu erklären: Audit ist für Nachvollziehbarkeit kritisch, aber es darf nicht zu inkonsistenten fachlichen Rollbacks führen.

## Abnahmekriterien

- Jeder Happy-Path-Schritt erzeugt mindestens einen Snapshot.
- Jeder Kompensationsschritt erzeugt einen eigenen Snapshot.
- `GET /v1/audit/orders/{correlationId}` zeigt die Timeline vollständig und sortiert.
- Der Stream aktualisiert das Admin Dashboard ohne Reload.
- Es existieren keine Update- oder Delete-Pfade für Snapshots.
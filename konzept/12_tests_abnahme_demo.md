# Tests, Abnahme und Demo-Szenarien

## Testziel

Die Tests sollen nicht nur einzelne Funktionen prüfen, sondern die Architekturversprechen absichern: keine Doppelbestellungen, keine Überverkäufe, klare Kompensation, vollständige Audit-Historie und reproduzierbare Fehlerpfade.

## Testpyramide

| Ebene | Zweck | Beispiele |
| --- | --- | --- |
| Unit Tests | Domänenlogik isoliert prüfen | Statusübergänge, Provider-Fassade, Validierung. |
| Integration Tests | Service plus Datenbank/Broker prüfen | Warehouse-Locking, Billing-Webhooks, Audit-Persistenz. |
| Contract Tests | Schnittstellen zwischen Services absichern | Shop zu Warehouse, Shop zu Billing. |
| E2E Tests | Vollständige Prozesse prüfen | Happy Path, Payment-Fehler, Booking-Fehler. |
| Demo Tests | Präsentationszustände vorbereiten | Seed, Simulation Panel, Grafana-Links. |

## Unit-Test-Schwerpunkte

### Shop-Service

- Order-Statusübergänge.
- Idempotency-Key-Konflikte.
- Warenkorbvalidierung.
- Rollenprüfung.
- Saga-Entscheidungsmatrix.

### Warehouse-Service

- Bestandsinvarianten.
- Reservierung bei ausreichendem Bestand.
- Ablehnung bei unzureichendem Bestand.
- Storno idempotent.
- Booking idempotent.

### Billing-Service

- Provider-Auswahl per Konfiguration.
- Mapping provider-spezifischer Fehler.
- Refund nur nach erfolgreicher Zahlung.
- Webhook-Deduplizierung.

### Invoice-Service

- Rechnung wird nur einmal pro `correlationId` erzeugt.
- Retry-Zähler.
- Circuit-Breaker-Zustände.

### Audit-Service

- Snapshot-Validierung.
- Append-only Repository.
- Sortierung nach Zeit.
- Stream-Event-Format.

## Integrationstests

## Warehouse-Concurrency-Test

Ziel: Überverkauf verhindern.

Setup:

- Produkt `P1` mit `available_quantity = 1`.
- Zwei parallele Reservierungsrequests mit unterschiedlicher `correlationId`.

Erwartung:

- Genau eine Reservierung ist `ACTIVE`.
- Eine Anfrage erhält `OUT_OF_STOCK`.
- `available_quantity = 0`.
- `reserved_quantity = 1`.
- Keine negativen Mengen.

## Billing-Webhook-Test

Ziel: asynchronen Provider korrekt verarbeiten.

Setup:

- Provider `async-webhook-sim`.
- Webhook Delay kurz setzen.

Erwartung:

- Initiale Charge liefert `PENDING`.
- Webhook setzt Payment auf `SUCCEEDED`.
- Event `PaymentSucceeded` wird publiziert.
- Doppelter Webhook verändert den Payment-Status nicht erneut.

## Audit-Persistenztest

Ziel: Snapshots unveränderlich und vollständig speichern.

Setup:

- Mehrere Events mit derselben `correlationId` einfügen.

Erwartung:

- Timeline ist chronologisch sortiert.
- `previousEventId` ist gesetzt, soweit möglich.
- Update/Delete-Pfade existieren nicht oder werden blockiert.

## E2E-Szenarien

## Szenario 1: Happy Path

Schritte:

1. Customer registrieren oder einloggen.
2. Produkt mit Bestand in Warenkorb legen.
3. Checkout mit neuem Idempotency-Key auslösen.
4. Warehouse reserviert.
5. Billing bestätigt Zahlung.
6. Invoice erzeugt Rechnung.
7. Warehouse bucht final aus.
8. Order endet in `COMPLETED`.

Abnahmekriterien:

- Order-Status `COMPLETED`.
- Payment-Status `SUCCEEDED`.
- Reservierung `BOOKED`.
- Rechnung existiert im Volume.
- Audit-Timeline enthält alle Hauptschritte.
- Logs sind per `correlationId` auffindbar.

## Szenario 2: Payment abgelehnt

Schritte:

1. Simulation Panel setzt `FAIL_NEXT_PAYMENT`.
2. Customer startet Bestellung.
3. Warehouse reserviert erfolgreich.
4. Billing lehnt Zahlung ab.
5. Shop-Service storniert Reservierung.
6. Order endet in `PAYMENT_FAILED`.

Abnahmekriterien:

- Keine aktive Reservierung bleibt übrig.
- Bestand ist wieder frei.
- Payment-Status `FAILED`.
- Audit enthält `PaymentFailed` und `ReservationCancelled`.

## Szenario 3: Lager nicht ausreichend

Schritte:

1. Produktbestand auf `0` setzen oder Menge größer als Bestand wählen.
2. Bestellung auslösen.
3. Warehouse lehnt Reservierung ab.
4. Order endet in `OUT_OF_STOCK`.

Abnahmekriterien:

- Billing wurde nicht aufgerufen.
- Keine Payment-Daten wurden erzeugt.
- Audit zeigt Ablehnung.

## Szenario 4: Warehouse-Booking schlägt fehl

Schritte:

1. Simulation Panel setzt `FAIL_NEXT_BOOKING`.
2. Bestellung starten.
3. Reservierung und Zahlung erfolgreich.
4. Finale Ausbuchung schlägt fehl.
5. Shop-Service löst Refund aus.
6. Order endet in `ROLLBACK_COMPLETED`.

Abnahmekriterien:

- Payment wurde refunded.
- Audit zeigt Booking-Fehler und Refund.
- Order ist nicht `COMPLETED`.

## Szenario 5: Invoice-Service fällt aus

Schritte:

1. Simulation Panel aktiviert Invoice-Fehler.
2. Bestellung erfolgreich bezahlen.
3. Invoice-Service schlägt dreimal fehl.
4. Circuit Breaker öffnet.
5. Order bleibt fachlich abgeschlossen.

Abnahmekriterien:

- Payment wird nicht refunded.
- Order bleibt `COMPLETED` oder abgeschlossen mit Invoice-Warnung.
- Circuit-Breaker-Zustandswechsel ist auditierbar.
- Retry-Versuche sind geloggt.

## Szenario 6: Idempotenz

Schritte:

1. Zwei identische `POST /v1/orders` mit gleichem `X-Idempotency-Key` senden.
2. Optional zweiten Request während des ersten laufenden Prozesses senden.

Abnahmekriterien:

- Nur eine Order wird erzeugt.
- Nur eine Reservierung wird erzeugt.
- Nur eine Zahlung wird ausgeführt.
- Zweiter Request erhält gespeicherte Antwort oder `PROCESSING`-Status.

## Szenario 7: Concurrency

Schritte:

1. Produktbestand auf `1` setzen.
2. Simulation Panel startet zwei parallele Bestellungen.
3. Admin Dashboard zeigt beide Timelines.

Abnahmekriterien:

- Eine Bestellung wird fortgesetzt.
- Eine Bestellung endet in `OUT_OF_STOCK`.
- Bestand wird nicht negativ.
- Logs zeigen Locking oder Warteverhalten.

## Contract Tests

Wichtige Contracts:

- Shop zu Warehouse: Reservation Request und Response.
- Shop zu Billing: Charge und Refund.
- Billing zu Shop oder Queue: Payment Update Event.
- Billing zu Invoice: `PaymentSucceeded` Event.
- Services zu Audit: Snapshot Payload.

Die zentrale lesbare Uebersicht und die kanonischen Payload-Beispiele stehen im Kapitel [Contracts und Schnittstellenkatalog](02a_contracts_und_schnittstellen.md).

Fuer jedes Contract-Payload sollte zusaetzlich ein Beispiel in `docs/api.md` oder OpenAPI/AsyncAPI abgelegt werden.

## Demo-Skript

Eine gute Präsentation sollte in dieser Reihenfolge laufen:

1. Architekturübersicht zeigen.
2. Docker Compose und laufende Services zeigen.
3. Happy Path in Customer View auslösen.
4. Admin Timeline und Grafana zur `correlationId` öffnen.
5. Payment-Fehler auslösen und Kompensation erklären.
6. Booking-Fehler auslösen und Refund zeigen.
7. Concurrency-Test starten und Warehouse-Locking erklären.
8. Invoice-Ausfall starten und Circuit Breaker zeigen.
9. Kurzes Fazit: Warum keine verteilte ACID-Transaktion nötig ist.

## Abnahme-Checkliste

- Alle Services starten reproduzierbar.
- Alle Muss-Endpunkte existieren.
- Fehlerantworten folgen RFC 7807.
- Audit-Timelines sind vollständig.
- Logs enthalten `correlationId`.
- Idempotenztest besteht.
- Concurrency-Test besteht.
- Demo-Daten können zurückgesetzt werden.
- README und `.env.example` sind aktuell.
- Präsentationsszenarien sind dokumentiert.

## Rest-Risiken für die Abgabe

| Risiko | Frühwarnsignal | Gegenmaßnahme |
| --- | --- | --- |
| Zu viele Frontends, zu wenig Zeit | Backend noch instabil, UI wächst | Simulation und Admin zuerst priorisieren. |
| Webhook-Fortsetzung zu komplex | Pending-Sagas bleiben hängen | Klare Queue und Statusabfrage implementieren. |
| Concurrency-Test flaky | Ergebnis nicht deterministisch | DB-Locking-Test isoliert und wiederholbar bauen. |
| Audit überfrachtet | Payloads werden riesig | Payload-Schemas klein und versioniert halten. |
| Docker Compose instabil | Startreihenfolge bricht | Healthchecks und Retry beim Boot. |
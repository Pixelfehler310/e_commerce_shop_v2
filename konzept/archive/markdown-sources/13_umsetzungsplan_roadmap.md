# Umsetzungsplan und Roadmap

## Priorisierungslogik

Das Projekt sollte zuerst den prüfbaren Kern liefern und danach Visualisierung und Bonusfunktionen ausbauen. Die zentrale Reihenfolge lautet:

1. Service-Schnittstellen und Datenmodelle stabilisieren.
2. Happy Path Ende-zu-Ende lauffähig machen.
3. Fehlerpfade und Kompensation implementieren.
4. Audit und Observability sichtbar machen.
5. Frontends und Simulation Panel für die Präsentation abrunden.

## Phase 0: Projektgrundlage

Ziel: Repository, Tooling und lokale Infrastruktur stehen.

Aufgaben:

- Monorepo-Struktur anlegen.
- Docker Compose mit PostgreSQL, Redis und RabbitMQ erstellen.
- NestJS-Service-Grundgerüste erzeugen.
- React-Frontend-Grundgerüste erzeugen.
- Gemeinsame Lint-, Format- und Testkonvention definieren.
- `.env.example` erstellen.
- Healthcheck-Endpunkte je Service anlegen.

Ergebnis:

- Alle Services starten leer.
- Infrastruktur ist erreichbar.
- CI oder lokales Testkommando ist vorbereitet.

## Phase 1: Shop-Grundfunktionen

Ziel: Nutzer, Produkte und Warenkorb funktionieren.

Aufgaben:

- Auth und JWT implementieren.
- Rollenmodell einführen.
- Produkt-CRUD für Admins.
- Produktliste für Kunden.
- Warenkorbmodell und Endpunkte.
- Customer Storefront minimal anschließen.

Ergebnis:

- Kunde kann Produkte sehen und Warenkorb befüllen.
- Admin kann Produkt anlegen.
- Rollen-Guards greifen.

## Phase 2: Warehouse-Service

Ziel: Bestand, Reservierung und Concurrency sind korrekt.

Aufgaben:

- Warehouse-Datenmodell und Migrationen.
- Produktbestand initialisieren.
- Wareneingang-Endpunkt.
- Reservierungsendpunkt mit `SELECT ... FOR UPDATE`.
- Reservierungsstorno.
- Finale Buchung.
- Concurrency-Integrationstest.

Ergebnis:

- Bestand kann nicht überverkauft werden.
- Reservierung, Storno und Booking sind idempotent.

## Phase 3: Billing und Payment-Fassade

Ziel: Zahlungsfluss ist über Provider-Fassade austauschbar.

Aufgaben:

- Payment-Datenmodell.
- PaymentProvider-Interface.
- Mindestens zwei Provider-Stubs.
- Provider-Auswahl per Env.
- Charge-Endpunkt.
- Refund-Endpunkt.
- MSW/Faker-Simulation.
- Webhook-Endpunkt und asynchroner Provider.

Ergebnis:

- Synchrone Zahlung funktioniert.
- Payment-Ablehnung ist simulierbar.
- Asynchroner Pending-Pfad funktioniert.

## Phase 4: Saga-Ende-zu-Ende

Ziel: Shop-Service orchestriert Bestellung vollständig.

Aufgaben:

- Order-Datenmodell.
- Saga-Orchestrator.
- Idempotency-Middleware mit Redis.
- Happy Path: Reserve, Charge, Book, Complete.
- Fehlerpfad Payment abgelehnt.
- Fehlerpfad Out of Stock.
- Fehlerpfad Booking fehlgeschlagen mit Refund.
- E2E-Tests.

Ergebnis:

- Alle Kernprozesse laufen ohne Frontend manuell per API.
- Statusmodell ist stabil.

## Phase 5: Audit-Service

Ziel: Alle Zustandswechsel sind nachvollziehbar.

Aufgaben:

- Snapshot-Datenmodell.
- Event-Ingestion per RabbitMQ oder HTTP.
- Timeline-Endpunkt.
- SSE-Stream.
- Append-only-Schutz.
- Services an Audit-Publishing anbinden.

Ergebnis:

- Jede Demo-Bestellung hat eine vollständige Timeline.
- Admin Dashboard kann Live-Daten anzeigen.

## Phase 6: Invoice-Service und Resilienz

Ziel: Rechnungserstellung läuft asynchron und robust.

Aufgaben:

- `PaymentSucceeded` Consumer.
- PDF-Generierung.
- Invoice-Volume.
- Idempotente Verarbeitung.
- Retry-Mechanismus.
- Circuit Breaker.
- Fehler- und Retry-Audit.

Ergebnis:

- Rechnung entsteht nach Payment-Erfolg.
- Invoice-Ausfall führt nicht zu Payment-Rollback.
- Circuit Breaker ist demonstrierbar.

## Phase 7: Frontends

Ziel: System wird bedienbar und präsentierbar.

Priorität:

1. Admin Dashboard mit Timeline.
2. Simulation Panel.
3. Customer Storefront.
4. Warehouse WMS.

Begründung: Für die Bewertung sind Transparenz und Demo-Kontrolle oft wichtiger als ein vollständig polierter Storefront-Flow.

Aufgaben:

- Login und Rollennavigation.
- Customer Produktliste, Warenkorb und Checkout.
- Admin Order-Tabelle und Timeline.
- WMS Bestand und Wareneingang.
- Simulation Panel mit Fehler-Schaltern und Concurrency-Test.
- Live-Updates über SSE.

Ergebnis:

- Präsentationsszenarien sind ohne manuelle API-Tools ausführbar.

## Phase 8: Observability und Demo-Finish

Ziel: Logs, Grafana und Demo-Skript sind rund.

Aufgaben:

- JSON-Logging in allen Services.
- `correlationId` konsequent weiterreichen.
- Loki und Grafana in Compose integrieren.
- Dashboard importieren.
- Demo-Daten resetten können.
- Demo-Skript finalisieren.
- Abnahme-Checkliste durchlaufen.

Ergebnis:

- Live-Demo zeigt Systemverhalten aus Nutzer-, Admin-, Lager- und Log-Sicht.

## Minimal Viable Architecture

Falls die Zeit knapp wird, muss diese Minimalversion stehen:

- Shop-, Warehouse-, Billing-, Audit-Service.
- PostgreSQL pro Service.
- Redis für Idempotenz.
- RabbitMQ mindestens für Audit oder Invoice-Event.
- Happy Path.
- Payment-Fehler mit Reservierungsstorno.
- Warehouse-Concurrency-Test.
- Admin Timeline.
- Docker Compose.

Invoice, WMS, Grafana und asynchrone Webhooks sind wichtig, aber nach dem Kern zu priorisieren.

## Meilensteine

| Meilenstein | Kriterium |
| --- | --- |
| M1 Infrastruktur | Alle leeren Services starten über Compose. |
| M2 Shop + Warehouse | Produkt, Bestand und Reservierung funktionieren. |
| M3 Billing | Charge und Refund über Fassade funktionieren. |
| M4 Saga | Happy Path und zwei Fehlerpfade bestehen als E2E-Test. |
| M5 Audit | Admin Timeline zeigt alle Events. |
| M6 Simulation | Fehler und Concurrency per UI auslösbar. |
| M7 Observability | Grafana zeigt Logs und Kennzahlen. |
| M8 Abgabe | Demo-Skript, Dokumentation und Tests vollständig. |

## Verantwortlichkeitsschnitt

Bei Teamarbeit bietet sich folgende Aufteilung an:

| Rolle | Schwerpunkt |
| --- | --- |
| Backend 1 | Shop-Service, Auth, Saga. |
| Backend 2 | Warehouse, Concurrency, Tests. |
| Backend 3 | Billing, Payment-Fassade, Invoice. |
| Backend 4 oder Shared | Audit, RabbitMQ, Observability. |
| Frontend | Customer, Admin, WMS, Simulation. |
| DevOps/Integration | Docker Compose, Seeds, Demo-Skript. |

## Kritische Pfade

Die riskantesten Abhängigkeiten sind:

- Saga hängt von Warehouse und Billing ab.
- Admin Dashboard hängt von Audit-Service ab.
- Demo hängt von stabilen Seed-Daten ab.
- Concurrency-Test hängt von echter Datenbanktransaktion ab.
- Asynchroner Payment-Pfad hängt von Queue oder Fortsetzungsmechanismus ab.

Diese Pfade sollten früh vertikal getestet werden.

## Risiko- und Gegenmaßnahmenplan

| Risiko | Auswirkung | Gegenmaßnahme |
| --- | --- | --- |
| Zu großer Scope | Kern bleibt unfertig | Minimal Viable Architecture priorisieren. |
| Fehlerpfade werden spät gebaut | Demo wirkt instabil | Payment- und Booking-Fehler ab Phase 4 integrieren. |
| Frontends blockieren Backend | Zeitverlust | Erst API und Admin Timeline, dann Storefront-Politur. |
| Queue-Komplexität steigt | Async-Pfade hängen | Klare Eventtypen, DLQ und kleine Payloads. |
| Docker-Probleme kurz vor Abgabe | Demo gefährdet | Compose ab Phase 0 pflegen und regelmäßig neu starten. |

## Definition of Done

Ein Feature gilt erst als fertig, wenn:

- API implementiert und dokumentiert ist.
- Validierung und Fehlerformat vorhanden sind.
- Audit-Event geschrieben wird, falls zustandsrelevant.
- Logs `correlationId` enthalten.
- Mindestens ein sinnvoller Test existiert.
- Docker-Compose-Ausführung weiterhin funktioniert.
- Demo-Relevanz geprüft wurde.

## Empfohlene nächste konkrete Schritte

1. Repository-Grundstruktur erzeugen.
2. Docker Compose für Infrastruktur schreiben.
3. Shop-, Warehouse- und Billing-Service als leere NestJS-Apps starten.
4. Datenmodelle für Produkt, Bestand, Order und Payment festlegen.
5. Happy Path als API-only E2E-Test implementieren.
6. Danach erst Frontend-Views anbinden.
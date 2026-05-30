# Anforderungen, Ziele und Scope

## Fachliche Hauptziele

Das Projekt bildet einen verteilten E-Commerce-Kern ab. Der fachliche Fokus liegt auf einem vollständigen Bestellprozess von der Produktauswahl bis zur Rechnungserstellung. Dabei soll nicht nur der Happy Path funktionieren, sondern vor allem gezeigt werden, wie das System mit Fehlern, Wiederholungen, Nebenläufigkeit und asynchronen Ereignissen umgeht.

Kernziele:

- Kunden können Produkte sehen, einen Warenkorb pflegen und eine Bestellung auslösen.
- Der Warenbestand wird reserviert, bezahlt und anschließend endgültig ausgebucht.
- Zahlungen können erfolgreich sein, abgelehnt werden oder asynchron per Webhook bestätigt werden.
- Rechnungen entstehen nach erfolgreicher Zahlung asynchron.
- Administratoren können Bestellungen und Audit-Timelines einsehen.
- Logistik-Mitarbeiter können Bestände verwalten und Wareneingänge buchen.
- Präsentierende können Fehler- und Lastszenarien gezielt provozieren.

## Technische Hauptziele

Das System soll die zentralen Konzepte verteilter Systeme sichtbar und prüfbar machen:

- Microservice-Aufteilung mit klaren Ownership-Grenzen.
- Eigene Persistenz pro Service.
- Keine transaktionale Kopplung über Service-Grenzen hinweg.
- Orchestrierte Saga für Bestellprozesse.
- Kompensationslogik für fehlgeschlagene Teilprozesse.
- Idempotente Bestellauslösung.
- Pessimistic Locking im Warehouse-Service.
- Asynchrone Kommunikation über RabbitMQ.
- Strukturierte Logs mit `correlationId`.
- Zentrale Visualisierung über Loki/Grafana.
- Docker Compose als reproduzierbare Laufzeitumgebung.

## Muss-Anforderungen

| Bereich | Muss-Anforderung |
| --- | --- |
| Architektur | Mindestens Shop-, Warehouse-, Billing-, Invoice- und Audit-Service. |
| Kommunikation | REST für synchrone Kernaufrufe, RabbitMQ für Events. |
| Datenhaltung | Eigene Datenbank oder eigenes Volume je Service. |
| Bestellprozess | Vollständiger Happy Path von Warenkorb bis Rechnung. |
| Fehlerbehandlung | Zahlung abgelehnt, Lager nicht ausreichend, Warehouse-Booking schlägt fehl. |
| Audit | Jeder Zustandsübergang wird unveränderlich gespeichert. |
| Idempotenz | `POST /v1/orders` verarbeitet denselben Key nur einmal. |
| Concurrency | Warehouse verhindert Überverkauf bei parallelen Reservierungen. |
| Deployment | Start aller Komponenten über `docker-compose up`. |
| Dokumentation | Architektur, Schnittstellen, Entscheidungen und Demo-Abläufe sind nachvollziehbar dokumentiert. |

## Soll-Anforderungen

| Bereich | Soll-Anforderung |
| --- | --- |
| Frontend | Customer-, Admin-, Warehouse- und Simulation-View. |
| Payment | Anbieterwechsel per Umgebungsvariable. |
| Webhook | Mindestens ein Payment-Stub bestätigt asynchron. |
| Resilienz | Circuit Breaker und Retry für die Rechnungserstellung. |
| Observability | Grafana-Dashboard für Bestellzahlen, Fehler und Payment-Ergebnisse. |
| API-Qualität | Fehlerantworten nach RFC 7807. |
| Rollen | `CUSTOMER`, `ADMIN`, `LOGISTICS`. |

## Bonus- und Präsentationsziele

Die Präsentation soll nicht nur behaupten, dass die Architektur robust ist. Sie soll das Verhalten live sichtbar machen:

- Happy-Path-Bestellung mit Echtzeit-Audit-Timeline.
- Payment-Ablehnung mit automatischer Stornierung der Reservierung.
- Warehouse-Booking-Fehler mit Refund.
- Invoice-Ausfall mit Circuit-Breaker-Zustandswechsel.
- Concurrency-Test mit zwei parallelen Kaufversuchen auf knappen Bestand.
- Webhook-Latenz-Simulation mit sichtbarem Zwischenstatus `PAYMENT_PENDING`.
- Log-Dashboard mit Filterung nach `correlationId`.

## Rollen und Rechte

| Rolle | Darf |
| --- | --- |
| `CUSTOMER` | Produkte ansehen, Warenkorb verwalten, Bestellung auslösen, Bestellstatus abrufen. |
| `ADMIN` | Produkte erstellen, Bestellungen einsehen, Audit-Timelines analysieren, Simulationen starten. |
| `LOGISTICS` | Lagerbestände sehen, Wareneingänge buchen, Bestand korrigieren. |

## Nicht-Ziele

Das Projekt soll bewusst nicht in Richtung einer vollständigen Produktionsplattform ausufern. Nicht-Ziele sind:

- Keine echte Zahlungsabwicklung mit produktiven API-Schlüsseln.
- Keine vollständige Mandantenfähigkeit.
- Keine komplexe Versandlogistik mit Tracking, Retouren und Lieferdienstintegration.
- Keine produktionsreife Finanzbuchhaltung.
- Keine verteilte ACID-Transaktion über mehrere Datenbanken.
- Keine direkte Datenbankintegration zwischen Services.

## Qualitätsattribute

| Attribut | Konkrete Erwartung |
| --- | --- |
| Nachvollziehbarkeit | Jede Bestellung ist über `correlationId`, Audit-Snapshots und Logs rekonstruierbar. |
| Erweiterbarkeit | Neue Payment-Anbieter und Frontend-Views lassen sich ohne Kernumbau ergänzen. |
| Robustheit | Fehler führen zu definierten Status und Kompensationen. |
| Konsistenz | Bestand wird nie negativ und nicht doppelt verkauft. |
| Bedienbarkeit | Demo- und Admin-Views machen technische Zustände verständlich sichtbar. |
| Reproduzierbarkeit | Lokaler Start und Tests sind über dokumentierte Kommandos möglich. |

## Abnahmekriterien auf Systemebene

Ein Durchlauf gilt als erfolgreich abgenommen, wenn folgende Punkte erfüllt sind:

- Alle Services starten über Docker Compose.
- Eine Bestellung erzeugt konsistente Daten in Shop, Warehouse, Billing, Invoice und Audit.
- Die Audit-Historie zeigt die Schritte in korrekter Reihenfolge.
- Wiederholung desselben Order-Requests mit identischem Idempotency-Key erzeugt keine zweite Bestellung.
- Zwei parallele Reservierungen bei Bestand `1` führen zu genau einer erfolgreichen Reservierung.
- Fehlerpfade landen in klar definierten Endzuständen.
- Grafana oder ein vergleichbares Dashboard zeigt nutzbare Metriken und Logs.
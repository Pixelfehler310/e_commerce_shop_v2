from __future__ import annotations

import html
import os
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHAPTERS = [
    {
        "number": "00",
        "source": "00_quickstart_und_leseweg.md",
        "folder": "grundlagen",
        "group": "Grundlagen",
        "title": "Quickstart und Leseweg",
        "summary": "Orientierung, Zielbild, Grundprinzipien und empfohlene Lesereihenfolge für das gesamte Konzept.",
    },
    {
        "number": "01",
        "source": "01_anforderungen_ziele_scope.md",
        "folder": "grundlagen",
        "group": "Grundlagen",
        "title": "Anforderungen, Ziele und Scope",
        "summary": "Fachliche und technische Ziele, Muss- und Soll-Anforderungen, Rollen, Nicht-Ziele und Abnahmekriterien.",
    },
    {
        "number": "REQ",
        "source": "01a_anforderungsdokument.md",
        "folder": "grundlagen",
        "group": "Grundlagen",
        "title": "Anforderungsdokument",
        "summary": "Vollständiges, prüfbares Anforderungsdokument für Systemziele, Rollen, Subsysteme, Qualität, Schnittstellen, Betrieb und Abnahme.",
    },
    {
        "number": "02",
        "source": "02_systemarchitektur_kommunikation.md",
        "folder": "architektur",
        "group": "Architektur",
        "title": "Systemarchitektur und Kommunikation",
        "summary": "Service-Landkarte, Datenhoheit, REST- und Event-Kommunikation, Header-Konventionen und Sicherheitsgrenzen.",
    },
    {
        "number": "02a",
        "source": "02a_contracts_und_schnittstellen.md",
        "folder": "architektur",
        "group": "Architektur",
        "title": "Contracts und Schnittstellenkatalog",
        "summary": "Zentrale Uebersicht ueber REST-, Event-, Audit- und Betriebs-Contracts mit technischen Ankern fuer spaetere Nachschaerfung.",
    },
    {
        "number": "03",
        "source": "03_service_shop.md",
        "folder": "services",
        "group": "Services",
        "title": "Shop-Service",
        "summary": "Gateway, Auth, Produktkatalog, Warenkorb, Order-Statusmodell und Saga-Orchestrierung im Shop-Service.",
    },
    {
        "number": "04",
        "source": "04_service_warehouse.md",
        "folder": "services",
        "group": "Services",
        "title": "Warehouse-Service",
        "summary": "Bestandsverwaltung, Reservierungen, finale Buchungen, Wareneingang, Locking und Concurrency-Tests.",
    },
    {
        "number": "05",
        "source": "05_service_billing_invoice.md",
        "folder": "services",
        "group": "Services",
        "title": "Billing und Invoice",
        "summary": "Payment-Fassade, Provider-Stubs, Webhooks, Refunds und asynchrone Rechnungserstellung.",
    },
    {
        "number": "06",
        "source": "06_audit_service.md",
        "folder": "services",
        "group": "Services",
        "title": "Audit-Service",
        "summary": "Append-only Snapshots, Timeline-Endpunkte, SSE-Streams, Admin-Lesemodelle und Payload-Maskierung.",
    },
    {
        "number": "07",
        "source": "07_saga_transaktionen_konsistenz.md",
        "folder": "architektur",
        "group": "Architektur",
        "title": "Saga, Transaktionen und Konsistenz",
        "summary": "Orchestrierte Saga, Happy Path, Fehlerpfade, Kompensationsmatrix, Zustandsmaschine und Invarianten.",
    },
    {
        "number": "08",
        "source": "08_idempotenz_resilienz_security.md",
        "folder": "qualitaet",
        "group": "Qualität",
        "title": "Idempotenz, Resilienz und Security",
        "summary": "Redis-basierte Idempotenz, Retry-Strategien, Circuit Breaker, JWT, Guards, Secrets und Problem Details.",
    },
    {
        "number": "09",
        "source": "09_frontends_simulationssuite.md",
        "folder": "frontends",
        "group": "Frontends",
        "title": "Frontends und Simulationssuite",
        "summary": "Customer Storefront, Admin Dashboard, Warehouse WMS, Simulation Panel und demo-taugliche UI-Flows.",
    },
    {
        "number": "10",
        "source": "10_observability_logging_tracing.md",
        "folder": "qualitaet",
        "group": "Qualität",
        "title": "Observability, Logging und Tracing",
        "summary": "JSON-Logs, correlationId-Fluss, Loki, Grafana-Dashboards, Metriken und Audit-Zusammenspiel.",
    },
    {
        "number": "11",
        "source": "11_infrastruktur_deployment_repo.md",
        "folder": "betrieb",
        "group": "Betrieb",
        "title": "Infrastruktur, Deployment und Repository",
        "summary": "Docker Compose, Netzwerke, Ports, Umgebungsvariablen, Migrationen, Repository-Struktur und Startablauf.",
    },
    {
        "number": "12",
        "source": "12_tests_abnahme_demo.md",
        "folder": "qualitaet",
        "group": "Qualität",
        "title": "Tests, Abnahme und Demo",
        "summary": "Testpyramide, E2E-Szenarien, Contract Tests, Demo-Skript, Checkliste und Rest-Risiken.",
    },
    {
        "number": "13",
        "source": "13_umsetzungsplan_roadmap.md",
        "folder": "planung",
        "group": "Planung",
        "title": "Umsetzungsplan und Roadmap",
        "summary": "Phasenplan, Meilensteine, kritische Pfade, Risiken, Definition of Done und konkrete nächste Schritte.",
    },
]

for chapter in CHAPTERS:
    chapter["output"] = f"pages/{chapter['folder']}/{Path(chapter['source']).stem}.html"

SOURCE_TO_OUTPUT = {chapter["source"]: chapter["output"] for chapter in CHAPTERS}
SOURCE_TO_TITLE = {chapter["source"]: chapter["title"] for chapter in CHAPTERS}

UMLAUTS = str.maketrans({
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
    "ß": "ss",
})


def slugify(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = html.unescape(value).translate(UMLAUTS)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "abschnitt"


def unique_slug(title: str, used: dict[str, int]) -> str:
    base = slugify(title)
    count = used.get(base, 0)
    used[base] = count + 1
    if count == 0:
        return base
    return f"{base}-{count + 1}"


def rel_url(from_file: Path, target: Path) -> str:
    relative = os.path.relpath(target, from_file.parent)
    return relative.replace(os.sep, "/")


def rewrite_href(href: str, current_output: Path) -> str:
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href

    if "#" in href:
        base, fragment = href.split("#", 1)
    else:
        base, fragment = href, ""

    source_name = Path(base).name
    if source_name in SOURCE_TO_OUTPUT:
        target = ROOT / SOURCE_TO_OUTPUT[source_name]
        rewritten = rel_url(current_output, target)
        if fragment:
            rewritten += f"#{slugify(fragment)}"
        return rewritten

    return href


def inline_markdown(text: str, current_output: Path) -> str:
    token_pattern = re.compile(r"(`[^`]+`|\[([^\]]+)\]\(([^)]+)\))")
    result: list[str] = []
    position = 0

    for match in token_pattern.finditer(text):
        result.append(html.escape(text[position:match.start()]))
        token = match.group(1)
        if token.startswith("`"):
            result.append(f"<code>{html.escape(token[1:-1])}</code>")
        else:
            raw_label = match.group(2)
            raw_href = match.group(3)
            source_name = Path(raw_href.split("#", 1)[0]).name
            if source_name in SOURCE_TO_TITLE and raw_label == source_name:
                raw_label = SOURCE_TO_TITLE[source_name]
            label = inline_markdown(raw_label, current_output)
            href = html.escape(rewrite_href(raw_href, current_output), quote=True)
            result.append(f'<a href="{href}">{label}</a>')
        position = match.end()

    result.append(html.escape(text[position:]))
    rendered = "".join(result)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    return rendered


def is_table_divider(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped.startswith("|") and stripped.endswith("|") and re.fullmatch(r"[|:\-\s]+", stripped))


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def is_block_start(line: str, next_line: str = "") -> bool:
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith("```")
        or bool(re.match(r"#{1,6}\s+", stripped))
        or bool(re.match(r"\s*[-*]\s+", line))
        or bool(re.match(r"\s*\d+\.\s+", line))
        or (stripped.startswith("|") and is_table_divider(next_line))
    )


def render_table(lines: list[str], current_output: Path) -> str:
    header = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:]]
    thead = "".join(f"<th>{inline_markdown(cell, current_output)}</th>" for cell in header)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{inline_markdown(cell, current_output)}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    tbody = "".join(body_rows)
    return f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>'


def render_markdown(source: str, current_output: Path) -> tuple[str, list[dict[str, str]]]:
    lines = source.splitlines()
    parts: list[str] = []
    toc: list[dict[str, str]] = []
    used_slugs: dict[str, int] = {}
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        next_line = lines[index + 1] if index + 1 < len(lines) else ""

        if not stripped:
            index += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip() or "text"
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            code = html.escape("\n".join(code_lines))
            language_class = html.escape(f"language-{language}")
            parts.append(f'<pre class="code-block {language_class}"><code>{code}</code></pre>')
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2)
            anchor = unique_slug(title, used_slugs)
            if 2 <= level <= 3:
                toc.append({"level": str(level), "title": re.sub(r"`", "", title), "anchor": anchor})
            parts.append(
                f'<h{level} id="{anchor}"><a class="anchor-link" href="#{anchor}" aria-label="Abschnitt verlinken">#</a>{inline_markdown(title, current_output)}</h{level}>'
            )
            index += 1
            continue

        if stripped.startswith("|") and is_table_divider(next_line):
            table_lines = [line, next_line]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            parts.append(render_table(table_lines, current_output))
            continue

        unordered = re.match(r"^\s*[-*]\s+(.+)$", line)
        if unordered:
            items = []
            while index < len(lines):
                item = re.match(r"^\s*[-*]\s+(.+)$", lines[index])
                if not item:
                    break
                items.append(f"<li>{inline_markdown(item.group(1), current_output)}</li>")
                index += 1
            parts.append(f"<ul>{''.join(items)}</ul>")
            continue

        ordered = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if ordered:
            items = []
            while index < len(lines):
                item = re.match(r"^\s*\d+\.\s+(.+)$", lines[index])
                if not item:
                    break
                items.append(f"<li>{inline_markdown(item.group(1), current_output)}</li>")
                index += 1
            parts.append(f"<ol>{''.join(items)}</ol>")
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index]
            candidate_next = lines[index + 1] if index + 1 < len(lines) else ""
            if is_block_start(candidate, candidate_next):
                break
            paragraph_lines.append(candidate.strip())
            index += 1
        parts.append(f"<p>{inline_markdown(' '.join(paragraph_lines), current_output)}</p>")

    return "\n".join(parts), toc


def grouped_chapters() -> OrderedDict[str, list[dict[str, str]]]:
    groups: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for chapter in CHAPTERS:
        groups.setdefault(chapter["group"], []).append(chapter)
    return groups


def chapter_nav(current: dict[str, str], current_output: Path) -> str:
    groups = grouped_chapters()
    group_parts = []
    for group, chapters in groups.items():
        links = []
        for chapter in chapters:
            href = html.escape(rel_url(current_output, ROOT / chapter["output"]), quote=True)
            current_attr = ' aria-current="page"' if chapter["source"] == current["source"] else ""
            links.append(
                f'<a href="{href}"{current_attr}><span>{chapter["number"]}</span>{html.escape(chapter["title"])}</a>'
            )
        group_parts.append(f'<div class="chapter-nav-group"><p>{html.escape(group)}</p>{"".join(links)}</div>')
    return "".join(group_parts)


def toc_html(toc: list[dict[str, str]]) -> str:
    if not toc:
        return ""
    links = "".join(
        f'<a class="toc-level-{entry["level"]}" href="#{html.escape(entry["anchor"], quote=True)}">{html.escape(entry["title"])}</a>'
        for entry in toc
    )
    return f'<aside class="toc-card" aria-label="Inhaltsverzeichnis"><strong>Inhalt</strong>{links}</aside>'


def diagram_for(source: str) -> str:
    diagrams = {
                "01a_anforderungsdokument.md": """
<section class="diagram-section" aria-labelledby="diagram-req-context-title">
    <div class="section-heading compact-heading">
        <p class="eyebrow">Diagramm</p>
        <h2 id="diagram-req-context-title">Systemkontext und Service-Grenzen</h2>
        <p>Die Karte zeigt die fachlichen Zugriffspfade, die Datenhoheit der Services und die Trennung zwischen synchroner Bestellentscheidung und asynchronen Folgeprozessen.</p>
    </div>
    <figure class="diagram-card architecture-diagram">
        <svg viewBox="0 0 980 520" role="img" aria-label="Systemkontext mit Frontends, Shop, Warehouse, Billing, Invoice, Audit, RabbitMQ, Redis und PostgreSQL">
            <defs><marker id="arrow-req" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="currentColor" /></marker></defs>
            <g class="diagram-zone"><rect x="24" y="36" width="220" height="402" rx="8"/><text x="44" y="68">Frontend-Rollen</text></g>
            <g class="diagram-zone"><rect x="286" y="36" width="398" height="402" rx="8"/><text x="306" y="68">Synchroner Kernprozess</text></g>
            <g class="diagram-zone"><rect x="730" y="36" width="226" height="402" rx="8"/><text x="750" y="68">Asynchron &amp; Nachweis</text></g>
            <g class="diagram-node blue"><rect x="54" y="112" width="160" height="50" rx="8"/><text x="134" y="142">Customer</text></g>
            <g class="diagram-node blue"><rect x="54" y="184" width="160" height="50" rx="8"/><text x="134" y="214">Admin</text></g>
            <g class="diagram-node blue"><rect x="54" y="256" width="160" height="50" rx="8"/><text x="134" y="286">WMS</text></g>
            <g class="diagram-node blue"><rect x="54" y="328" width="160" height="50" rx="8"/><text x="134" y="358">Simulation</text></g>
            <g class="diagram-node teal strong"><rect x="390" y="116" width="190" height="70" rx="8"/><text x="485" y="146">Shop-Service</text><text x="485" y="168">Gateway, IAM, Saga</text></g>
            <g class="diagram-node amber"><rect x="318" y="258" width="162" height="58" rx="8"/><text x="399" y="292">Warehouse</text></g>
            <g class="diagram-node amber"><rect x="520" y="258" width="132" height="58" rx="8"/><text x="586" y="292">Billing</text></g>
            <g class="diagram-node dark"><rect x="390" y="352" width="190" height="50" rx="8"/><text x="485" y="382">PostgreSQL + Redis</text></g>
            <g class="diagram-node plum"><rect x="762" y="116" width="156" height="58" rx="8"/><text x="840" y="150">RabbitMQ</text></g>
            <g class="diagram-node plum"><rect x="762" y="218" width="156" height="58" rx="8"/><text x="840" y="252">Invoice</text></g>
            <g class="diagram-node dark"><rect x="762" y="320" width="156" height="58" rx="8"/><text x="840" y="354">Audit</text></g>
            <path class="diagram-line" d="M214 137 H390" marker-end="url(#arrow-req)"/><path class="diagram-line" d="M214 209 C286 209 304 151 390 151" marker-end="url(#arrow-req)"/><path class="diagram-line" d="M214 281 C286 281 300 170 390 170" marker-end="url(#arrow-req)"/><path class="diagram-line" d="M214 353 C300 353 304 184 390 184" marker-end="url(#arrow-req)"/>
            <path class="diagram-line sync" d="M440 186 V258" marker-end="url(#arrow-req)"/><path class="diagram-line sync" d="M540 186 L586 258" marker-end="url(#arrow-req)"/><path class="diagram-line" d="M485 186 V352" marker-end="url(#arrow-req)"/>
            <path class="diagram-line async" d="M652 287 C710 287 708 145 762 145" marker-end="url(#arrow-req)"/><path class="diagram-line async" d="M840 174 V218" marker-end="url(#arrow-req)"/><path class="diagram-line async" d="M485 186 C610 226 650 346 762 349" marker-end="url(#arrow-req)"/><path class="diagram-line async" d="M399 316 C506 410 648 376 762 354" marker-end="url(#arrow-req)"/>
            <text class="diagram-caption" x="322" y="238">REST</text><text class="diagram-caption" x="682" y="128">Events</text><text class="diagram-caption" x="616" y="404">Audit-Snapshots</text>
        </svg>
    </figure>
</section>

<section class="diagram-section" aria-labelledby="diagram-req-process-title">
    <div class="section-heading compact-heading">
        <p class="eyebrow">Diagramm</p>
        <h2 id="diagram-req-process-title">End-to-End-Bestellprozess</h2>
        <p>Der Prozess trennt Kundenantwort, lokale Transaktionen und nachgelagerte Eventverarbeitung. Jeder Schritt erzeugt einen prüfbaren Status.</p>
    </div>
    <div class="flow-diagram saga-flow" role="img" aria-label="Bestellprozess von Checkout bis Audit">
        <div class="flow-step success"><span>1</span><strong>Checkout</strong><small>Order CREATED und Idempotenz-Lock</small></div>
        <div class="flow-step success"><span>2</span><strong>Reservierung</strong><small>Warehouse ACTIVE oder OUT_OF_STOCK</small></div>
        <div class="flow-step success"><span>3</span><strong>Payment</strong><small>SUCCEEDED, FAILED oder PENDING</small></div>
        <div class="flow-step success"><span>4</span><strong>Booking</strong><small>StockBooked oder Refund-Pfad</small></div>
        <div class="flow-step end"><span>5</span><strong>Invoice &amp; Audit</strong><small>Asynchroner Nachweis</small></div>
        <div class="flow-branch warn"><strong>Payment negativ</strong><span>ReservationCancel -> PAYMENT_FAILED</span></div>
        <div class="flow-branch warn"><strong>Booking negativ</strong><span>Refund -> ROLLBACK_COMPLETED</span></div>
        <div class="flow-branch neutral"><strong>Payment pending</strong><span>Webhook setzt Saga fort</span></div>
    </div>
</section>

<section class="diagram-section" aria-labelledby="diagram-req-state-title">
    <div class="section-heading compact-heading">
        <p class="eyebrow">Diagramm</p>
        <h2 id="diagram-req-state-title">Statusmodell für Order, Payment und Reservation</h2>
        <p>Das Zustandsmodell definiert erlaubte fachliche Übergänge und verhindert nicht interpretierbare Zwischenstände.</p>
    </div>
    <pre class="code-block language-mermaid"><code>stateDiagram-v2
        [*] --&gt; CREATED
        CREATED --&gt; RESERVATION_PENDING
        RESERVATION_PENDING --&gt; RESERVED
        RESERVATION_PENDING --&gt; OUT_OF_STOCK
        RESERVED --&gt; PAYMENT_PENDING
        RESERVED --&gt; BOOKING_PENDING
        RESERVED --&gt; ROLLBACK_PENDING
        PAYMENT_PENDING --&gt; BOOKING_PENDING
        PAYMENT_PENDING --&gt; ROLLBACK_PENDING
        BOOKING_PENDING --&gt; COMPLETED
        BOOKING_PENDING --&gt; ROLLBACK_PENDING
        ROLLBACK_PENDING --&gt; PAYMENT_FAILED
        ROLLBACK_PENDING --&gt; ROLLBACK_COMPLETED
        ROLLBACK_PENDING --&gt; FAILED_REQUIRES_MANUAL_REVIEW
        OUT_OF_STOCK --&gt; [*]
        PAYMENT_FAILED --&gt; [*]
        ROLLBACK_COMPLETED --&gt; [*]
        COMPLETED --&gt; [*]</code></pre>
</section>

<section class="diagram-section" aria-labelledby="diagram-req-events-title">
    <div class="section-heading compact-heading">
        <p class="eyebrow">Diagramm</p>
        <h2 id="diagram-req-events-title">Kommunikations- und Eventfluss</h2>
        <p>Der Eventfluss macht sichtbar, welche fachlichen Zustände synchron entschieden und welche Folgeprozesse asynchron dokumentiert oder verarbeitet werden.</p>
    </div>
    <div class="layer-diagram" role="img" aria-label="Kommunikations- und Eventfluss">
        <div><strong>REST Checkout</strong><span>Frontend -> Shop mit X-Idempotency-Key</span></div>
        <div><strong>REST Reservation</strong><span>Shop -> Warehouse mit correlationId</span></div>
        <div><strong>REST Charge</strong><span>Shop -> Billing mit Payment-Fassade</span></div>
        <div><strong>RabbitMQ Events</strong><span>PaymentSucceeded, StockBooked, Statuswechsel</span></div>
        <div><strong>Audit &amp; Invoice</strong><span>Timeline, Rechnung, Circuit-Breaker-Nachweis</span></div>
    </div>
</section>
""",
        "02_systemarchitektur_kommunikation.md": """
<section class="diagram-section" aria-labelledby="diagram-architecture-title">
  <div class="section-heading compact-heading">
    <p class="eyebrow">Diagramm</p>
    <h2 id="diagram-architecture-title">Service-Landkarte und Kommunikationswege</h2>
    <p>Die Karte trennt Benutzerzugriff, synchrone Entscheidungsaufrufe und asynchrone Folgeprozesse.</p>
  </div>
  <figure class="diagram-card architecture-diagram">
    <svg viewBox="0 0 980 520" role="img" aria-label="Architekturdiagramm mit Frontends, Shop, Warehouse, Billing, RabbitMQ, Invoice, Audit und Datenbanken">
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="currentColor" /></marker>
      </defs>
      <g class="diagram-zone"><rect x="24" y="32" width="222" height="420" rx="8"/><text x="44" y="64">Frontend-Zone</text></g>
      <g class="diagram-zone"><rect x="292" y="32" width="398" height="420" rx="8"/><text x="312" y="64">Service-Zone</text></g>
      <g class="diagram-zone"><rect x="736" y="32" width="220" height="420" rx="8"/><text x="756" y="64">Async &amp; Audit</text></g>
      <g class="diagram-node blue"><rect x="54" y="112" width="162" height="56" rx="8"/><text x="135" y="146">Customer UI</text></g>
      <g class="diagram-node blue"><rect x="54" y="190" width="162" height="56" rx="8"/><text x="135" y="224">Admin Dashboard</text></g>
      <g class="diagram-node blue"><rect x="54" y="268" width="162" height="56" rx="8"/><text x="135" y="302">WMS</text></g>
      <g class="diagram-node blue"><rect x="54" y="346" width="162" height="56" rx="8"/><text x="135" y="380">Simulation</text></g>
      <g class="diagram-node teal strong"><rect x="398" y="128" width="188" height="72" rx="8"/><text x="492" y="158">Shop-Service</text><text x="492" y="180">Gateway + Saga</text></g>
      <g class="diagram-node amber"><rect x="322" y="272" width="164" height="62" rx="8"/><text x="404" y="308">Warehouse</text></g>
      <g class="diagram-node amber"><rect x="520" y="272" width="140" height="62" rx="8"/><text x="590" y="308">Billing</text></g>
      <g class="diagram-node plum"><rect x="766" y="144" width="154" height="62" rx="8"/><text x="843" y="180">RabbitMQ</text></g>
      <g class="diagram-node plum"><rect x="766" y="256" width="154" height="62" rx="8"/><text x="843" y="292">Invoice</text></g>
      <g class="diagram-node dark"><rect x="766" y="354" width="154" height="62" rx="8"/><text x="843" y="390">Audit</text></g>
      <path class="diagram-line" d="M216 140 H398" marker-end="url(#arrow)"/><path class="diagram-line" d="M216 218 C292 218 308 164 398 164" marker-end="url(#arrow)"/><path class="diagram-line" d="M216 296 C286 296 292 184 398 184" marker-end="url(#arrow)"/><path class="diagram-line" d="M216 374 C302 374 306 196 398 196" marker-end="url(#arrow)"/>
      <path class="diagram-line sync" d="M452 200 V272" marker-end="url(#arrow)"/><path class="diagram-line sync" d="M550 200 L590 272" marker-end="url(#arrow)"/><path class="diagram-line async" d="M660 303 C714 303 718 175 766 175" marker-end="url(#arrow)"/><path class="diagram-line async" d="M843 206 V256" marker-end="url(#arrow)"/><path class="diagram-line async" d="M492 200 C620 224 650 384 766 384" marker-end="url(#arrow)"/><path class="diagram-line async" d="M404 334 C502 412 650 404 766 394" marker-end="url(#arrow)"/>
      <text class="diagram-caption" x="318" y="252">REST synchron</text><text class="diagram-caption" x="664" y="144">Events</text><text class="diagram-caption" x="634" y="438">Snapshots</text>
    </svg>
  </figure>
</section>
""",
        "07_saga_transaktionen_konsistenz.md": """
<section class="diagram-section" aria-labelledby="diagram-saga-title">
  <div class="section-heading compact-heading">
    <p class="eyebrow">Diagramm</p>
    <h2 id="diagram-saga-title">Saga-Fluss mit Kompensation</h2>
    <p>Der Shop-Service entscheidet nach jedem lokalen Ergebnis, ob die Saga fortgesetzt, pausiert oder kompensiert wird.</p>
  </div>
    <div class="flow-diagram saga-flow" role="img" aria-label="Saga-Fluss von Order über Reservierung, Payment, Booking und Kompensation">
    <div class="flow-step success"><span>1</span><strong>Order anlegen</strong><small>CREATED</small></div>
    <div class="flow-step success"><span>2</span><strong>Bestand reservieren</strong><small>RESERVED oder OUT_OF_STOCK</small></div>
    <div class="flow-step success"><span>3</span><strong>Payment starten</strong><small>SUCCEEDED, FAILED oder PENDING</small></div>
    <div class="flow-step success"><span>4</span><strong>Final buchen</strong><small>BOOKED</small></div>
    <div class="flow-step end"><span>5</span><strong>Order abschließen</strong><small>COMPLETED</small></div>
    <div class="flow-branch warn"><strong>Payment fehlerhaft</strong><span>Reservierung stornieren -> PAYMENT_FAILED</span></div>
    <div class="flow-branch warn"><strong>Booking fehlerhaft</strong><span>Refund auslösen -> ROLLBACK_COMPLETED</span></div>
    <div class="flow-branch neutral"><strong>Provider pending</strong><span>Webhook setzt Saga später fort</span></div>
  </div>
</section>
""",
        "08_idempotenz_resilienz_security.md": """
<section class="diagram-section" aria-labelledby="diagram-resilience-title">
  <div class="section-heading compact-heading">
    <p class="eyebrow">Diagramm</p>
    <h2 id="diagram-resilience-title">Schutzschichten rund um die Saga</h2>
  </div>
  <div class="layer-diagram" role="img" aria-label="Schutzschichten Auth, Idempotenz, Retry, Circuit Breaker und Problem Details">
    <div><strong>Auth &amp; Rollen</strong><span>JWT, Guards, Service-Grenzen</span></div>
    <div><strong>Idempotenz</strong><span>Redis Lock, gespeicherte Antwort</span></div>
    <div><strong>Retry</strong><span>nur idempotente Kommandos</span></div>
    <div><strong>Circuit Breaker</strong><span>Invoice und externe Provider schützen</span></div>
    <div><strong>Problem Details</strong><span>einheitliche Fehler für UIs und Tests</span></div>
  </div>
</section>
""",
        "11_infrastruktur_deployment_repo.md": """
<section class="diagram-section" aria-labelledby="diagram-deployment-title">
  <div class="section-heading compact-heading">
    <p class="eyebrow">Diagramm</p>
    <h2 id="diagram-deployment-title">Lokale Deployment-Topologie</h2>
  </div>
  <figure class="diagram-card deployment-diagram">
    <svg viewBox="0 0 980 420" role="img" aria-label="Docker Compose Deployment mit Frontends, Services, Datenbanken, Redis, RabbitMQ, Loki und Grafana">
      <defs><marker id="arrow-deploy" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="currentColor" /></marker></defs>
      <g class="diagram-zone"><rect x="28" y="34" width="924" height="340" rx="8"/><text x="52" y="66">docker-compose Netzwerk</text></g>
      <g class="diagram-node blue"><rect x="72" y="112" width="168" height="64" rx="8"/><text x="156" y="148">React Frontends</text></g>
      <g class="diagram-node teal strong"><rect x="302" y="92" width="172" height="72" rx="8"/><text x="388" y="122">Shop API</text><text x="388" y="144">Public Port</text></g>
      <g class="diagram-node amber"><rect x="302" y="222" width="172" height="58" rx="8"/><text x="388" y="256">Shop DB + Redis</text></g>
      <g class="diagram-node amber"><rect x="536" y="92" width="152" height="58" rx="8"/><text x="612" y="126">Warehouse</text></g>
      <g class="diagram-node amber"><rect x="536" y="172" width="152" height="58" rx="8"/><text x="612" y="206">Billing</text></g>
      <g class="diagram-node plum"><rect x="536" y="252" width="152" height="58" rx="8"/><text x="612" y="286">Invoice</text></g>
      <g class="diagram-node plum"><rect x="754" y="92" width="150" height="58" rx="8"/><text x="829" y="126">RabbitMQ</text></g>
      <g class="diagram-node dark"><rect x="754" y="172" width="150" height="58" rx="8"/><text x="829" y="206">Audit DB/API</text></g>
      <g class="diagram-node dark"><rect x="754" y="252" width="150" height="58" rx="8"/><text x="829" y="286">Loki/Grafana</text></g>
      <path class="diagram-line" d="M240 144 H302" marker-end="url(#arrow-deploy)"/><path class="diagram-line sync" d="M474 128 H536" marker-end="url(#arrow-deploy)"/><path class="diagram-line sync" d="M474 146 C506 146 502 201 536 201" marker-end="url(#arrow-deploy)"/><path class="diagram-line" d="M388 164 V222" marker-end="url(#arrow-deploy)"/><path class="diagram-line async" d="M688 201 C724 201 720 121 754 121" marker-end="url(#arrow-deploy)"/><path class="diagram-line async" d="M688 281 C720 281 722 121 754 121" marker-end="url(#arrow-deploy)"/><path class="diagram-line async" d="M612 310 C648 352 804 352 829 310" marker-end="url(#arrow-deploy)"/>
    </svg>
  </figure>
</section>
""",
        "12_tests_abnahme_demo.md": """
<section class="diagram-section" aria-labelledby="diagram-tests-title">
  <div class="section-heading compact-heading">
    <p class="eyebrow">Diagramm</p>
    <h2 id="diagram-tests-title">Testpyramide und Demo-Fokus</h2>
  </div>
  <div class="pyramid-diagram" role="img" aria-label="Testpyramide mit Unit, Integration, Contract, E2E und Demo Tests">
    <div class="pyramid-level level-demo"><strong>Demo Tests</strong><span>Seeds, Simulation, Präsentationspfade</span></div>
    <div class="pyramid-level level-e2e"><strong>E2E</strong><span>Happy Path, Payment-Fehler, Booking-Fehler</span></div>
    <div class="pyramid-level level-contract"><strong>Contract</strong><span>Shop zu Warehouse, Billing, Events, Audit</span></div>
    <div class="pyramid-level level-integration"><strong>Integration</strong><span>DB-Locking, Webhooks, RabbitMQ, Persistenz</span></div>
    <div class="pyramid-level level-unit"><strong>Unit</strong><span>Statusmodelle, Validierung, Fassade</span></div>
  </div>
</section>
""",
    }
    return diagrams.get(source, "")


def render_page(chapter: dict[str, str], index: int) -> None:
    output_path = ROOT / chapter["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = (ROOT / chapter["source"]).read_text(encoding="utf-8")
    body_html, toc = render_markdown(markdown, output_path)

    previous_chapter = CHAPTERS[index - 1] if index > 0 else None
    next_chapter = CHAPTERS[index + 1] if index + 1 < len(CHAPTERS) else None

    overview_href = html.escape(rel_url(output_path, ROOT / "index.html"), quote=True)
    css_href = html.escape(rel_url(output_path, ROOT / "assets" / "styles.css"), quote=True)
    source_href = html.escape(rel_url(output_path, ROOT / chapter["source"]), quote=True)

    previous_link = ""
    if previous_chapter:
        previous_href = html.escape(rel_url(output_path, ROOT / previous_chapter["output"]), quote=True)
        previous_link = f'<a class="button ghost" href="{previous_href}">Vorheriges Kapitel</a>'

    next_link = ""
    if next_chapter:
        next_href = html.escape(rel_url(output_path, ROOT / next_chapter["output"]), quote=True)
        next_link = f'<a class="button primary" href="{next_href}">Nächstes Kapitel</a>'

    html_doc = f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(chapter['title'])} - Distributed E-Commerce Core</title>
    <link rel="stylesheet" href="{css_href}" />
  </head>
  <body class="doc-page">
    <a class="skip-link" href="#inhalt">Zum Inhalt springen</a>

    <aside class="sidebar doc-sidebar" aria-label="Konzeptnavigation">
      <a class="brand brand-link" href="{overview_href}">
        <span class="brand-mark">DEC</span>
        <span>
          <strong>Distributed E-Commerce Core</strong>
          <small>HTML-Konzept</small>
        </span>
      </a>
      <nav class="chapter-nav" aria-label="Kapitel">
        {chapter_nav(chapter, output_path)}
      </nav>
    <a class="sidebar-action" href="{overview_href}">Zur Gesamtübersicht</a>
    </aside>

    <main id="inhalt" class="page-shell doc-shell">
      <header class="doc-hero">
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <a href="{overview_href}">Übersicht</a>
          <span>{html.escape(chapter['group'])}</span>
          <span>Kapitel {chapter['number']}</span>
        </nav>
        <p class="eyebrow">Kapitel {chapter['number']}</p>
        <h1>{html.escape(chapter['title'])}</h1>
        <p class="lead">{html.escape(chapter['summary'])}</p>
        <div class="doc-actions">
          {previous_link}
          <a class="button" href="{source_href}">Markdown-Quelle</a>
          {next_link}
        </div>
      </header>

      {diagram_for(chapter['source'])}

      <div class="doc-layout">
        {toc_html(toc)}
        <article class="article-content">
          {body_html}
        </article>
      </div>

      <nav class="doc-pagination" aria-label="Kapitel wechseln">
        {previous_link}
        <a class="button" href="{overview_href}#kapitel">Alle Kapitel</a>
        {next_link}
      </nav>
    </main>
  </body>
</html>
"""
    output_path.write_text(html_doc, encoding="utf-8", newline="\n")


def main() -> None:
    for index, chapter in enumerate(CHAPTERS):
        render_page(chapter, index)
    print(f"Generated {len(CHAPTERS)} HTML pages under {ROOT / 'pages'}")


if __name__ == "__main__":
    main()

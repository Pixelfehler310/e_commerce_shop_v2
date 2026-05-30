---
name: concept-docs-maintenance
description: 'Use when: updating the Distributed E-Commerce Core Konzept documentation, HTML concept pages, architecture docs, contracts, service documentation, static multi-page concept site, or archived Markdown sources in this repo.'
argument-hint: 'Describe the concept documentation change, e.g. add contract details or update service chapter'
user-invocable: true
---

# Concept Docs Maintenance

## Purpose

Use this skill when changing the project concept documentation for the Distributed E-Commerce Core in this repository. The concept docs are maintained directly as static HTML pages. Do not recreate or rely on the removed Markdown-to-HTML generator.

The skill helps preserve project context, navigation consistency, and documentation quality while editing the multi-page HTML concept site.

## Project Context

The project is a distributed e-commerce core with:

- Backend services: `shop-service`, `warehouse-service`, `billing-service`, `invoice-service`, `audit-service`.
- Frontends: `storefront-ui`, `admin-dashboard`, `warehouse-wms`, `simulation-panel`.
- Core architecture: Shop-Service as external gateway and Saga orchestrator, Warehouse for stock and reservations, Billing for payment facade and refunds, Invoice for async invoice generation, Audit for append-only snapshots and timelines.
- Infrastructure: Docker Compose, PostgreSQL per stateful service, Redis for idempotency/session concerns, RabbitMQ for async events, Loki/Grafana for observability.
- Important cross-cutting concepts: `correlationId`, `X-Correlation-Id`, `X-Idempotency-Key`, Problem Details, Saga compensation, contract tests, audit snapshots.

## Documentation Layout

Active documentation source of truth:

- `konzept/index.html`: static overview and landing page.
- `konzept/pages/**/*.html`: individual concept pages.
- `konzept/assets/styles.css`: shared styling.

Archived historical sources:

- `konzept/archive/markdown-sources/*.md`: old Markdown sources, kept only as archive/reference.

Removed workflow:

- The old generator `konzept/tools/build_concept_html.py` was deleted.
- The active docs must not require `python .\konzept\tools\build_concept_html.py`.
- Do not add new generator scripts unless the user explicitly asks for a generated documentation workflow again.

## When To Use

Use this skill for requests such as:

- Update the concept documentation.
- Add, remove, or reorganize concept pages.
- Adjust contracts, interfaces, endpoint documentation, event documentation, service chapters, diagrams, or roadmap sections.
- Keep the HTML concept site consistent after project changes.
- Convert conceptual changes into directly editable HTML pages.

Do not use this skill for normal backend/frontend implementation unless the documentation also needs to be changed.

## Procedure

1. Identify the documentation scope.
   - For high-level overview changes, edit `konzept/index.html`.
   - For chapter content, edit the relevant file under `konzept/pages/`.
   - For visual styling shared across docs, edit `konzept/assets/styles.css`.
   - For old source comparison only, read files under `konzept/archive/markdown-sources/`.

2. Preserve the static HTML model.
   - Edit HTML files directly.
   - Remove or avoid references to active Markdown sources.
   - Do not add `Markdown-Quelle` buttons.
   - Do not instruct the user to run a generator.

3. Maintain navigation consistency.
   - If adding or renaming a chapter, update `konzept/index.html` chapter cards and hero/quick links if relevant.
   - Update sidebars in all affected `konzept/pages/**/*.html` files.
   - Update previous/next pagination links around the changed chapter.
   - Keep breadcrumb labels, chapter numbers, titles, and nav labels aligned.

4. Preserve project semantics.
   - Keep Shop-Service documented as gateway and Saga orchestrator.
   - Keep Warehouse documented as stock owner with reservation, booking, and pessimistic locking.
   - Keep Billing documented as payment facade owner with charge, refund, webhook, provider simulation.
   - Keep Invoice documented as async consumer of `PaymentSucceeded` and non-blocking invoice generator.
   - Keep Audit documented as append-only snapshot/timeline service without business decision authority.
   - Keep contracts aligned with implemented controller/event stubs where possible.

5. Update contracts carefully.
   - REST contracts should include method, path, owner, consumer/caller, required headers, request shape, response shape, and error behavior.
   - Event contracts should include channel/pattern, producer, consumer, event type, required fields, schema version expectations, and idempotency expectations.
   - Audit contracts should distinguish transport channel from business `eventType`.
   - Mark unsettled DTOs or payloads as open if controller code still uses `unknown`.

6. Keep HTML maintainable.
   - Follow the existing structure: sidebar, `doc-hero`, `doc-layout`, `toc-card`, `article-content`, pagination.
   - Prefer existing CSS classes before adding new styles.
   - Keep content in German unless the surrounding page is clearly English.
   - Use concise headings, tables, code blocks, and local links.
   - Avoid nested cards and avoid adding decorative clutter.

7. Validate after edits.
   - Search for stale active-source references: `Markdown-Quelle`, `build_concept_html`, `README.md`, `href="*.md"` in active HTML.
   - Run a local href check across `konzept/**/*.html` after link/navigation changes.
   - Verify key pages still link back to `../../index.html` or correct relative paths.
   - If CSS changed, inspect likely affected pages for layout regressions.

## Local Link Check

Use this PowerShell check after structural doc edits:

```powershell
$root = Resolve-Path .\konzept
$broken = @()
Get-ChildItem .\konzept -Recurse -Filter *.html | ForEach-Object {
  $file = $_.FullName
  $html = [System.IO.File]::ReadAllText($file)
  [regex]::Matches($html, 'href="([^"]+)"') | ForEach-Object {
    $href = $_.Groups[1].Value
    if ($href -match '^(https?:|mailto:|#)') { return }
    $path = ($href -split '#')[0]
    if ([string]::IsNullOrWhiteSpace($path)) { return }
    $target = Join-Path (Split-Path $file) $path
    $resolved = [System.IO.Path]::GetFullPath($target)
    if (-not (Test-Path $resolved)) {
      $broken += [pscustomobject]@{ File = $file.Substring($root.Path.Length + 1); Href = $href }
    }
  }
}
if ($broken.Count -eq 0) { 'No broken local hrefs found.' } else { $broken | Format-Table -AutoSize | Out-String }
```

## Completion Criteria

A concept documentation change is complete when:

- The requested content is present in the active HTML page or pages.
- Navigation, breadcrumbs, chapter cards, and pagination still make sense.
- No active HTML page points to archived Markdown as an editing source.
- No generator command or generator file is required.
- Local HTML links validate successfully after structural edits.
- The change respects the project architecture and service responsibilities.

## Common Pitfalls

- Editing archived Markdown and expecting the visible site to change.
- Reintroducing the deleted generator workflow.
- Updating one chapter page but forgetting sidebars or pagination elsewhere.
- Documenting a contract as final even though the controller still accepts `unknown`.
- Changing event names in one place without updating Audit, Invoice, tests, and contract docs.
- Linking to root-relative paths that will not work when opening the HTML files directly in a browser.

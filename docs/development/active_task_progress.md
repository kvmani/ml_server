# Active task: portal polish, privacy language, vendored MathJax help, deployment guide

Resumable ledger for the current goal. Update the checkboxes as work lands.

## Goal (verbatim intent)

1. Polish the ml_server home page: modern, office-appropriate, desktop-optimised, no
   functional regressions.
2. PDF Tools is a general-purpose PDF utility, not a "scientific PDF" tool. Say clearly that
   any PDF is accepted and that nothing leaves the office intranet or is stored.
3. Feedback privacy copy must stop advertising IP/browser logging; instead state that no
   personal information is collected or stored and that privacy/security are paramount.
4. Write an ml_server deployment guide for a typical intranet Ubuntu host using local
   Python/Node mirrors and CPU-only ML packages.
5. Fix help quality: equations must render to PyTex-grade typographic standard. Vendor MathJax
   into ml_server so in-app help renders professional mathematics offline.
6. Apply the same improvements across the integrated tools (HydrideSegmentation, PyTex,
   PDF Tools, Scientific Calculator, Unit Converter, Tabular ML).
7. Commit and push each touched repository once its work is verified.

## Repositories in scope

| Repo | Path | Status |
| --- | --- | --- |
| ml_server | `C:\Users\kvman\PycharmProjects\ml_server` | code done, docs + commit pending |
| HydrideSegmentation | `C:\Users\kvman\HydrideSegmentation` | pending |
| PyTex | `C:\Users\kvman\PycharmProjects\pytex` | pending |
| PDF Tools | `C:\Users\kvman\PycharmProjects\pdf_tools` | pending |
| Scientific Calculator | `C:\Users\kvman\PycharmProjects\scientific_calculator` | pending |
| Unit Converter | `C:\Users\kvman\PycharmProjects\unit_converter` | pending |
| Tabular ML | `C:\Users\kvman\PycharmProjects\tabular_ml` | pending |

## Findings so far

- Help equations are plain ASCII strings in `src/ml_server/tool_help.py`
  (e.g. `2 d_hkl sin(theta_B) = lambda`) rendered as raw text by
  `src/ml_server/templates/tool_help.html`. This is the root cause of the poor equation
  quality; they need LaTeX source plus a real math renderer.
- No MathJax/KaTeX is vendored in any repo today. PyTex's Sphinx site relies on the Sphinx
  MathJax extension (CDN), which will not work on a disconnected intranet either.
- `src/ml_server/static/vendor/` currently holds bootstrap, bootstrap-icons, fontawesome, js.
- Feedback privacy text lives in `src/ml_server/templates/home.html` (the modal) and needs to
  be checked in `help_faq.html`, `admin_feedback*.html`, and the feedback route.
- PDF Tools "research/scientific PDF" wording lives in `src/ml_server/catalog.py`,
  `src/ml_server/tool_help.py`, and the pdf_tools repo itself.

## Task checklist

### ml_server
- [x] Vendor MathJax (tex-chtml + fonts) under `static/vendor/mathjax/` with an offline loader.
- [x] Convert `tool_help.py` equations to LaTeX and render them through MathJax.
- [x] Upgrade `tool_help.html` + help CSS to a professional typographic standard.
- [x] Polish `home.html` hero/grid/trust strip for desktop office use.
- [x] Rewrite PDF Tools catalog + help copy as general-purpose and privacy-clear.
- [x] Rewrite feedback privacy copy (modal, help/FAQ, any admin-facing text).
- [ ] Add `docs/DEPLOYMENT_UBUNTU_INTRANET.md` (local mirrors, CPU-only wheels).
- [ ] Run the full test suite; add tests for the new help/MathJax assets.
- [ ] Commit and push.

### Companion repos
- [ ] HydrideSegmentation: help/math parity + privacy wording.
- [ ] PyTex: offline MathJax for its docs/app help.
- [ ] PDF Tools: general-purpose + privacy wording, help math.
- [ ] Scientific Calculator: help math.
- [ ] Unit Converter: help math.
- [ ] Tabular ML: help math.
- [ ] Commit and push each.

## Verification log

- MathJax 3.2.2 `tex-chtml-full.js` (1.3 MB) plus the 20-file `woff-v2` set (396 KB) and the
  Apache-2.0 LICENSE are vendored at `src/ml_server/static/vendor/mathjax/`. Nothing is fetched
  from a CDN; `static/js/mathjax-config.js` pins `fontURL` to the local path.
- Live browser check on all six help pages: every equation and every inline symbol is typeset
  (`mjx-container` present), zero `mjx-merror` nodes, zero horizontal overflow, and all font
  requests return 200 from `/static/vendor/mathjax/...`.
- Home page at 1425x900: 3-column tool grid, 4-column trust strip, no horizontal overflow, no
  clipped card summaries, first card row fully visible above the fold (bottom at 782 px).
- Search still filters correctly, including on the new PDF tags (`scan`, `any pdf`).
- Portal suite: `47 passed`.
- `src/ml_server/cli.py` had no `__main__` guard, so `python -m ml_server.cli` silently exited 0.
  Guard added.
- `static/css/style.css` was left syntactically invalid by a stray `}` and `/` at EOF and a
  malformed `..research-header` selector; both repaired. The competing `!important` "compact
  landing surface" layer was removed in favour of a single token-driven layout.

### Privacy implementation note

The requested copy ("no personal information is collected or stored") was not true of the code as
written: `analytics_sessions` and `feedback_submissions` both persisted the client IP address and
the full User-Agent string, and the developer notification email included the IP. Rather than
publish a claim the software contradicted, the storage was changed to match the promise:

- IP addresses are never written; the legacy columns remain but are always `NULL`.
- User agents are reduced to a coarse browser family (Chrome/Firefox/Edge/Safari/Opera/Other).
- `initialize_database` erases identifiers already present, so upgrading an existing deployment
  is what makes the guarantee true.
- The admin dashboard now shows browser families instead of an IP column, and the feedback table
  shows the originating page instead.
- Covered by `test_analytics_stores_no_identifying_information`,
  `test_existing_identifiers_are_erased_on_upgrade`, and
  `test_admin_dashboard_shows_anonymous_analytics`.

---

# Previous task: production release 1.0.0

## Release work (2026-08-23)

- [x] Add descriptive hover/focus content and separate scientific-help links to all six cards.
- [x] Add equation-, input-, algorithm-, limitation-, and workflow-rich help pages with six SVGs.
- [x] Coordinate companion versions and publish the deployment/rollback manifest.
- [x] Migrate portal/PDF integration from PyPDF2 to pypdf.
- [x] Build and smoke-test the portal, PDF Tools, Tabular ML, Calculator, and Converter wheels.
- [x] Complete the final PyTex scientific/browser gates and cross-repository audit.

The current portal suite is 28 passing tests with no PyPDF2 warning. The release wheel includes
all templates/static/help assets and starts from its packaged non-debug configuration when
`ML_SERVER_CONFIG` is not supplied.

Hydride's complete scientific suite is green (`333 passed, 1 skipped`), and its rebuilt 1.0.1
wheel starts successfully from a clean target. PDF Tools, Tabular ML, Scientific Calculator, and
Unit Converter also pass their complete repository gates and clean-wheel help/health smokes.

PyTex's full 6,762-case collection exits 0, all 47 isolated-port Chromium journeys pass, its
204-page Sphinx site builds with zero warnings, and its 0.2.0 wheel/sdist pass a clean-install
smoke. The release increment is pushed to `origin/main` at `d08f887`.

The final container audit used the checksum-verified official Docker Compose v5.5.0 standalone
validator: the merged base/override configuration passes `config --quiet`. Obsolete schema keys,
an invalid web command string, unsafe debug/host defaults, mutable source mounts, and the missing
secret-protecting `.dockerignore` were corrected before that pass.

# Previous task: mature scientific-tools portal

## Objective

Deliver a professional local portal for mature services only, including the
independently owned Tabular ML Workbench.

## Decisions

- The homepage is driven by `src/ml_server/catalog.py`; stub cards are not catalog entries.
- HydrideSegmentation remains the owner of segmentation functionality and is linked at `C:\Users\kvman\HydrideSegmentation` on port 5005.
- PyTex remains the owner of crystallographic functionality and is linked at its own local service.
- PDF Tools remains its own service and is linked through the integrated blueprint.
- Tabular ML remains CPU-only and independently deployable; the portal mounts
  its stable companion blueprint without owning ML implementation details.
- The general scientific calculator has a new owner repository at `C:\Users\kvman\PycharmProjects\scientific_calculator`.
- Experimental and placeholder utilities remain unavailable from the portal.

## Verification and next actions

- [x] Read platform governance and inspect existing routes.
- [x] Implement catalog-driven landing page and service links.
- [x] Add standalone calculator service and local launcher.
- [x] Remove the preliminary hydride implementation and point the portal at the mature repository.
- [x] Run focused portal tests and calculator smoke tests.
- [x] Run the local launcher smoke check and verify health/landing links for all four services.
- [x] Mount Tabular ML, add its reviewed catalog card, and verify index,
  health, dataset discovery, and built-in loading through host tests.

## Final verification

- Portal full suite: `28 passed, 1 warning`.
- Scientific calculator suite: `4 passed`.
- Live smoke: portal `/`, portal `/api/catalog`, portal `/pdf_tools/`, calculator `/` plus `/api/health` and `/api/evaluate`, PyTex `/` plus `/api/health`, and HydrideSegmentation `/` plus `/health` all returned HTTP 200.
- Visual QA: landing page renders only the reviewed active service catalog; experimental or placeholder utility cards are not cataloged or launched.
- The former PyPDF2 warning was removed in the 1.0.0 release migration to pypdf.
- The preliminary hydride icon assets were also removed; the portal uses a neutral catalog icon while the mature service owns its own UI and assets.

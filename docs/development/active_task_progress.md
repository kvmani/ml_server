# Active task: mature scientific-tools portal

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
- Known warning: the portal's existing PyPDF2 dependency emits its upstream deprecation warning.
- The preliminary hydride icon assets were also removed; the portal uses a neutral catalog icon while the mature service owns its own UI and assets.

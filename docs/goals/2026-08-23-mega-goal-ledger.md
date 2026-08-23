# Working Ledger — Mega Goal (started 2026-08-23)

**Overall status: all three milestones (M1, M2, M3) implemented and independently verified as of
2026-08-23. Nothing has been committed in any repo — that's left for the user's review/approval.**

Tracks progress on the multi-repo goal set via `/goal`. Resume from here after any interruption — re-read this whole file before doing anything else.

## Scope (as requested)

1. **Scientific calculator** (`~/PycharmProjects/scientific_calculator`): add an Atom fraction ⇄ Mass fraction conversion tab.
2. **Admin dashboard** (`ml_server`, `src/ml_server/app/admin/`): richer usage analytics — browsers/versions, session times, tool usage, operation timings, uptime, insight dashboards.
3. **PyTex EBSD module** (`~/PycharmProjects/pytex`): new Kikuchi (kinematic) simulation tab —
   - Plot kinematic Kikuchi lines/bands on a flat detector for a given crystal system, detector geometry (elevation, sample-to-detector distance, etc.), beam kV, and crystal orientation.
   - Annotate bands and zone axes (band intersections) with Miller indices, with an on/off toggle.
   - Simultaneously simulate the on-axis BSE-detector SAED pattern (as if in TEM mode) to guide 2-beam-condition tilting for ECCI.
   - ECCI workflow tool: given EBSD Euler angles, predict the stage tilt/rotation needed for a 2-beam ECCI condition; dynamically visualize the Kikuchi/SAED pattern changing with tilt, and show current zone axis proximity live.
   - `.ipynb` tutorial notebook demonstrating the full ECCI workflow (EBSD orientation → predicted tilt/rotation → simulated on-axis SAED verifying 2-beam condition).
   - Same functionality surfaced in both the web app and the desktop app, as an EBSD sub-tab.
4. Everything delivered coherently, tested, and working together.

## Repo map

- `ml_server` (this repo) — portal, admin dashboard, links out to sibling tool services.
- `scientific_calculator` — standalone Flask microservice, single `app.py` + `templates/index.html` (inline CSS/JS, no build step). Linked from ml_server portal via `SCIENTIFIC_CALCULATOR_URL` (default `127.0.0.1:5055`).
- `pytex` — large materials-texture-analysis package (`src/pytex/...`), has existing `ebsd` subsystem incl. `app/static/js/panels/ebsdkikuchi.js` (found via search — **needs inspection**, may already have partial Kikuchi plotting to build on rather than duplicate). Has its own docs site, notebooks (`docs/site/tutorials/notebooks/`), desktop app, and web app.

## Milestone status

### M1 — Atom fraction ⇄ Mass fraction tab (scientific_calculator) — ✅ DONE (2026-08-23)
- `src/scientific_calculator_service/elements.py`: new IUPAC standard atomic weight table (118 elements).
- `src/scientific_calculator_service/app.py`: `convert_composition(mode, composition)` (atom_to_mass / mass_to_atom), `/api/composition/convert`, `/api/elements`, version bumped 0.3.0 → 0.4.0.
- `templates/index.html`: new "Atom ⇄ Mass %" tab, dynamic element rows (add/remove), results table with atomic weights + mean atomic mass.
- Tests added in `tests/test_app.py` (conversion math, round-trip, validation, API contract) — **18/18 passing**.
- Verified live in browser: Fe70/Cr19/Ni11 atom% → 70.528/17.824/11.648 mass%, mean atomic mass 55.427 g/mol. Correct (Cr lightest → mass share shrinks, Ni heaviest → grows).
- Not yet done: not wired into ml_server's `docs/help` pages or CHANGELOG; scientific_calculator's own `/help` page and README don't mention the new tab yet.

### M2 — Admin analytics dashboard (ml_server) — ✅ DONE (2026-08-23)
- Baseline was already solid: `admin/dashboard.py` (Flask-Admin, token-gated) + `services/engagement.py` (SQLite: `analytics_sessions`, `analytics_events`, anonymous-by-design — browser reduced to coarse family, no IP/UA stored) + `services/metrics.py` (Prometheus counters: request latency, visits, active users, uptime).
- Added `browser_major_version()` to `services/engagement.py`: extracts **only the major version number** (e.g. `"120"`) per browser family — never the full dotted UA string — to stay inside the existing privacy contract (tested by `test_analytics_stores_no_identifying_information` et al.). New column `analytics_sessions.browser_major_version`, migrated via `_migrate_to_anonymous_analytics`.
- `analytics_summary()` now also returns `browser_versions` (family+version breakdown) and `session_duration_buckets` (<10s / 10s-1m / 1m-5m / 5m-15m / 15m+ histogram).
- `templates/admin_dashboard.html`: replaced flat tables with Chart.js bar/doughnut charts — tool usage counts, per-tool average action time, browser family doughnut, session-length histogram — plus a browser+version table and the existing recent-sessions/log/Prometheus sections.
- Tests: added `test_browser_major_version_is_coarse_bucket_only` and extended `test_analytics_stores_no_identifying_information` to assert the version bucket in `tests/test_submit_feedback.py`. Full suite: **49/49 passing** (`./.venv/Scripts/python.exe -m pytest -q`).
- Not done: uptime/log tail were already present and untouched; did not vendor Chart.js off the jsdelivr CDN (pre-existing choice, out of scope for this pass — flag if the offline-first pattern established for MathJax should extend here too).

### M3 — PyTex Kikuchi/SAED/ECCI module — SCOPED, IMPLEMENTATION STARTING (2026-08-23)

**Key finding: pytex already has almost the entire physics stack.** This is NOT a from-scratch
build — it's new orchestration + a new panel wiring existing primitives together. Full survey
(via Explore agent) below; re-read this before touching code.

Reusable pytex primitives (own stack, not orix/kikuchipy wrappers — those are only optional
exchange adapters in `adapters/orix.py`):
- `core/orientation.py` — `Orientation`, `OrientationSet`, `Rotation` (Bunge/Roe/Kocks/ABG/Matthies).
- `core/lattice.py` — `Phase`, `CrystalDirection`, `CrystalPlane`, `ZoneAxis`, reciprocal lattice.
- `core/miller.py` — `MillerPlane`, `MillerDirection`.
- `diffraction/models.py:137` — `DiffractionGeometry` dataclass: detector/specimen/lab
  `ReferenceFrame`s, `beam_energy_kev`, `camera_length_mm`, `pattern_center`,
  `detector_pixel_size_um`, `detector_shape`, `beam_direction_lab`, `specimen_to_lab_matrix`,
  `tilt_degrees` — covers elevation angle / PC / sample-to-detector distance / kV directly.
- `diffraction/kikuchi.py` — `simulate_kikuchi_pattern(geometry, phase, orientation, *, max_index=3,
  min_d_spacing_angstrom=None, min_relative_intensity=1e-3, max_bands=None,
  zone_axis_max_index=2, provenance=None) -> KikuchiPattern` (bands + zone axes with Miller
  indices) — **the exact detector-plane Kikuchi simulation needed.**
- `diffraction/saed.py` — `generate_saed_pattern(phase, zone_axis: ZoneAxis, *,
  camera_constant_mm_angstrom=180.0, max_index=6, max_g_inv_angstrom=None,
  zone_tolerance_inv_angstrom=1e-6, intensity_model=..., label_limit=20,
  provenance=None) -> SAEDPattern` — **on-axis TEM-style SAED, needed for the BSE on-axis view.**
- `diffraction/kikuchi_map.py` — `compute_kikuchi_map`, `plan_kikuchi_route`,
  `StereographicKikuchiMap`, `KikuchiRoute/Leg` — a stereographic map + **routing solver between
  zone axes already exists**, directly reusable for the tilt/rotation solve.
- `tem/navigation.py:plan_tilt_to_zone_axis`, `tem/stage.py:DoubleTiltStage/RectangularEnvelope/
  StagePosition`, `tem/reconstruction.py:CurrentState` — **an existing TEM stage-tilt solver**;
  template for the ECCI-specific "solve tilt/rotation for 2-beam condition" op is
  `app/services/tem.py:868 _plan_tilt` (registry wiring), plus `_kikuchi_overlay` (3272) and
  `_simulate_saed` (1777), `_stereogram` (2454) for combined rendering patterns.
- `electron_wavelength_angstrom(kev)` in `diffraction/kinematic.py`.

Backend wiring (no Flask — stdlib `http.server`):
- `app/registry.py` `ServiceRegistry` + `REGISTRY.operation(id, title, summary, help_text,
  parameters, returns)(handler)` in `services/*.py`. Frontend builds forms from the manifest
  automatically (`core/controls.js: buildForm`) — no hardcoded HTML forms needed per operation.
- Template handler: `app/services/ebsd_pattern.py:314 _simulate_kikuchi_pattern(request) -> dict`
  (Euler/geometry → JSON: band edges/centre polylines, zone_axes w/ pixel coords, pattern_centre_px).
- **Plan: new `app/services/ecci.py`** registering 1-2 operations, e.g.
  `ecci.simulate_state` (orientation + stage tilt/rotation + geometry → Kikuchi + on-axis SAED +
  current zone-axis proximity, for live re-simulation as tilt/rotation change) and
  `ecci.solve_two_beam_tilt` (EBSD Euler angles + target g/zone axis → predicted stage
  tilt/rotation using `plan_tilt_to_zone_axis`/`DoubleTiltStage`).

Frontend wiring:
- `app/static/js/panels/ebsdkikuchi.js` (~440 lines, full impl, not a stub) — clone as the
  layout/interaction template: filled-polygon+dashed-centerline SVG bands, zone-axis circles
  sized by band count with Miller labels, `state.showAxes` on/off toggle, pattern-centre
  crosshair, hover readout. Calls backend via `call(operation.id, values)` from `core/api.js`.
  Shares `core/kikuchilabel.js`, `core/plotframe.js`, `core/result.js`.
- `panels/saedsim.js` + `core/saedplot.js` (`drawKikuchiBands`, `drawSimulatedPattern`) — SAED
  drawing to reuse for the simultaneous on-axis view.
- **Plan: new `panels/ecciWorkflow.js`** combining both views + tilt/rotation controls + live
  zone-axis-proximity readout.
- Register as EBSD sub-tab in `app/static/js/main.js`: `EBSD_ANALYSIS.panels` array — append
  `ecciKikuchiSaed`/`ecciWorkflow` after `ebsdKikuchi`.

Desktop app: **no separate implementation exists** (`app/desktop.py` just opens the same
`AppServer` in a pywebview window or the default browser). New EBSD panels appear automatically
in both web and desktop — no extra desktop-specific work needed for this feature.

Notebook style: model on `docs/site/tutorials/notebooks/30_kikuchi_maps_and_zone_axis_routing.ipynb`
— imports from top-level `pytex` package, narrative markdown + code cells that assert
physics-derived expectations inline (not golden values), `get_phase_fixture` for built-in phases,
`plot_kikuchi_map`-style matplotlib plotting. New notebook:
`docs/site/tutorials/notebooks/<NN>_ecci_workflow_from_ebsd.ipynb` — build `DiffractionGeometry`
+ `Phase` + `Orientation` from a stated Euler triplet, call `simulate_kikuchi_pattern`/
`generate_saed_pattern`, solve tilt via the new ECCI op, verify 2-beam condition by re-simulating
SAED at the solved tilt.

Test style: `tests/unit/test_ebsd_kikuchi_pattern.py`, `test_kikuchi_map.py`, etc. — expected
values derived independently from Bragg's law/geometry (never from running the code under test),
built via `REGISTRY.operations()`/request dicts with `phase={"builtin": "ni_fcc"}`, called through
`REGISTRY` directly (no HTTP). New tests: `tests/unit/test_ecci_*.py` in the same style.

**Status: ✅ DONE, independently verified (2026-08-23).** Implemented by a background agent from
the API survey above, then verified directly (not taken on faith) — see verification log below.

**Files added:**
- `src/pytex/app/services/ecci.py` — backend, two registered operations:
  - `ecci.solve_workflow` — from an EBSD-measured Bunge orientation + current stage state +
    target `[uvw]`: returns the current EBSD Kikuchi pattern, current on-axis (TEM-style) view,
    ranked reachable stage moves (tilt, rotation) that bring the target onto the beam, and current
    zone-axis proximity.
  - `ecci.resimulate` — same three views at an *explicit* stage tilt/rotation, no solving — what
    the frontend's live tilt/rotation controls call on every move.
  - Stage kinematics: `plan_tilt_to_zone_axis` (TEM double-tilt holder) does NOT match an SEM/ECCI
    eucentric stage (one tilt about a fixed lab axis + one rotation about the specimen normal,
    applied before the tilt), so a new closed-form solver (`_stage_branches`) was derived for it —
    proven to reduce exactly to `DiffractionGeometry.for_ebsd`'s own matrix at rotation=0, and every
    solution is forward-validated through an independently re-derived path (`_forward_residual_deg`)
    rather than trusting the algebra that produced it.
  - On-axis SAED view reuses `pytex.tem.synthetic.synthesize_saed_image`/`DetectorRaster` rather
    than a second `DiffractionGeometry` at elevation≈90° (a deliberate, documented deviation from
    one option floated in the brief — simpler and avoids inventing an excitation-error path the
    geometry class doesn't provide).
- `src/pytex/app/static/js/panels/ecciWorkflow.js` — frontend panel: side-by-side EBSD Kikuchi +
  on-axis SAED views, phase/geometry/target-direction inputs, "Solve the ECCI tilt" button, live
  tilt/rotation scrub controls with a "go to solved tilt/rotation" shortcut, zone-axis-proximity
  readout.
- `tests/unit/test_ecci_workflow.py` — 18 tests, physics-derived expectations (no golden values).
- `docs/site/tutorials/notebooks/32_ecci_workflow_from_ebsd.ipynb` — nickel [111] ECCI tutorial;
  triple-checks the core claim: (1) hand-rederives the stage closed form independently and matches
  the library's solved tilts to 1e-6°, (2) calls `ecci.resimulate` before/after the solved move and
  shows the target's angle-off-beam collapsing from >1° to <1e-6° and every on-axis reflection's
  excitation error collapsing from >1e-3 Å⁻¹ to <1e-6 Å⁻¹, (3) a third hand-computed excitation-error
  check (`dot(g, beam_direction)` from the reciprocal basis, not imported from the module under
  test) confirming both the number and beam/[111] alignment to 1e-9.

**Files modified:** `app/services/__init__.py` (registers `ecci`), `app/registry.py` (added
`"ecci"` to `_PANEL_DOCUMENTATION`, reusing the existing `workflows/kikuchi_geometry` Sphinx page),
`app/static/js/main.js` (panel import + appended to `EBSD_ANALYSIS.panels`), `app/static/app.css`
(`.stage__split` side-by-side layout), `docs/site/tutorials/notebooks.md` (toctree entry).

**Verification performed independently (not just the agent's self-report):**
1. `git status` in `pytex/` — file list matches the agent's report exactly, nothing extra touched,
   nothing committed.
2. `./.venv/Scripts/python.exe -m pytest tests/unit/test_ecci_workflow.py -q` → **18/18 passed**.
3. `pytest tests/unit/test_ebsd_kikuchi_pattern.py test_kikuchi_map.py test_app_tem_kikuchi.py
   test_app_manifest.py test_notebooks.py -q` → **all passed, no regressions** (2 skips unrelated,
   pre-existing).
4. Read `ecci.py`'s `_stage_branches`/`_forward_residual_deg` directly — confirmed the
   forward-validation is genuinely independent of the closed form, not circular.
5. Executed the notebook end-to-end via `nbclient.NotebookClient` (nbconvert CLI wasn't installed,
   used the library directly) → **all cells including every `assert` ran clean, no errors**.
6. Started the real app server (`AppServer(('127.0.0.1', 5098))`), confirmed via `/api/manifest`
   that both `ecci.resimulate` and `ecci.solve_workflow` are registered, then drove the actual
   browser UI: EBSD tab → new sub-tab "From an EBSD orientation: the on-axis view and the tilt to
   a two-beam condition" renders with side-by-side Kikuchi/on-axis plots, phase defaulted to
   Nickel (fcc) matching the notebook, target-`[uvw]`/orientation/stage/geometry inputs, "Solve the
   ECCI tilt" control, live tilt/rotation scrub inputs, and a zone-axis-proximity readout — matches
   the spec. (Did not click every control interactively — the notebook already exercises the exact
   same backend operations end-to-end with real assertions, which is the stronger check.)

**Not done / deliberately out of scope for this pass:** nothing committed to git (left for the
user to review/commit at their discretion); no separate desktop-specific work was needed or done,
by design (the desktop shell just opens the same web UI).

## Next actions (resume here)
1. Inspect pytex's existing EBSD/Kikuchi code (listed above) before designing M3 — don't duplicate existing kinematic simulation utilities.
2. Inspect `ml_server/src/ml_server/app/services/metrics.py` and `engagement.py` to scope M2 precisely.
3. Work M2 and M3 in that order (M2 is contained to this repo and faster to land; M3 is the largest piece and should be broken into its own sub-ledger once scoped).
4. Update this ledger after every milestone (status, files touched, test results) — treat it as the source of truth across session interruptions.

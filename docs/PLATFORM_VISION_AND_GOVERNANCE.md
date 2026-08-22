# Office Scientific Tools Platform Vision and Engineering Governance

**Policy version:** 1.0

**Effective date:** 2026-08-22

**Canonical location:** `ml_server/docs/PLATFORM_VISION_AND_GOVERNANCE.md`

## 1. Authority and scope

This document defines the shared product vision, architecture direction, delivery stages, and
engineering governance for the office scientific-tools platform. It governs the portal and every
tool or infrastructure repository that participates in the platform, including:

- `ml_server`, which will become the stable portal and common entry point;
- `HydrideSegmentation`, which owns microstructural and hydride segmentation;
- `pytex`, which owns crystallographic texture, diffraction, EBSD, TEM, and related analysis;
- the future productivity-tools repository;
- the future platform-infrastructure repository; and
- every tool added to the portal later.

Each member repository must link to this document from its local `AGENTS.md` and contributor
documentation. Repository-local rules remain authoritative for repository-specific scientific,
testing, safety, and documentation requirements. If a local rule is stricter than this document,
the stricter rule applies. If two rules genuinely conflict, development stops until the conflict is
recorded and reconciled; it must not be resolved silently in code.

This is a living governance document, but changes to it are deliberate platform decisions. They
must update the policy version, explain the change in `ml_server/CHANGELOG.md`, and be committed and
pushed to `main`.

## 2. Platform mission

Build one dependable office website through which colleagues can discover and launch a growing
collection of scientific and productivity tools without needing to know where those tools run.

The homepage URL and user experience remain stable while individual tools evolve independently,
release on their own schedules, and move between physical machines or virtual machines. Each tool
concentrates on its domain functionality. Common concerns such as discovery, stable routing,
traffic control, access logging, feedback intake, platform status, and administration are handled
once by the platform.

The platform succeeds when adding, replacing, moving, disabling, or upgrading a tool is a routine,
auditable operation that does not require redesigning the homepage or changing a URL already given
to users.

## 3. Cardinal principles

### 3.1 Every goal is resumable and no context is disposable

This is a cardinal rule for human and automated contributors.

No substantial goal may exist only in a person's memory, an agent conversation, or an uncommitted
worktree. Work must be resumable after a crash, sign-out, hand-off, interrupted session, or change
of developer without reconstructing intent from chat history.

For every substantial or multi-step goal:

1. Create or update the repository's durable progress ledger before implementation begins.
2. Record the objective, scope, decisions, completed work, verification results, current Git state,
   blockers, and exact next actions.
3. Update the ledger after each substantial increment and before long-running work, commits,
   pushes, deployments, or any likely interruption point.
4. Commit and push each verified substantial increment to `main` so completed work is recoverable
   from the repository and remote history.
5. When resuming, read the governing documents, progress ledger, recent `main` history, and current
   worktree before taking new action. Continue from the recorded next action; do not restart the
   goal or repeat finished work without evidence that it is necessary.
6. When a goal finishes, is deferred, or is abandoned, record that outcome explicitly. Silence is
   not a hand-off.

Every member repository must use `docs/development/active_task_progress.md` unless its local
governance defines a more specific tracked ledger. A goal spanning multiple repositories must also
maintain a coordinating ledger under `ml_server/docs/development/` that identifies every affected
repository, its last pushed commit, its verification state, and the next cross-repository action.

### 3.2 Durable progress lands on `main`

All normal development commits and pushes go directly to `main`.

- Do not create branches for ordinary feature, documentation, refactoring, testing, or deployment
  work.
- Do not leave substantial completed work only in a local commit.
- Pull or fetch and reconcile current `origin/main` before starting an increment and again before
  pushing when another contributor may have advanced it.
- Commit after each self-consistent, verified increment rather than accumulating one large final
  commit.
- Stage explicit paths so unrelated user work is not included accidentally.
- Preserve unrelated worktree changes and never discard another contributor's work to make a commit
  convenient.
- If repository protection or an external process prevents a required direct push to `main`, stop,
  record the blocker, and request a governance decision. Do not create an unapproved workaround
  branch.

This policy intentionally minimizes branch drift and makes the remote `main` history the durable
record from which interrupted work can resume.

### 3.3 One capability has one owning repository

A production capability must have one canonical implementation and one owning repository.
Compatibility redirects or adapters may exist temporarily, but copied scientific or productivity
implementations may not evolve independently in multiple repositories.

In particular:

- the advanced `HydrideSegmentation` implementation replaces the preliminary hydride code in
  `ml_server`;
- PyTex remains the owner of its crystallographic and diffraction semantics;
- productivity utilities leave the portal and gain their own owner; and
- an experimental stub is not moved into a scientific repository merely because its name overlaps
  that repository's domain.

### 3.4 Stable interfaces, independent implementations

The portal and gateway depend on small operational contracts, not on tool internals. A tool may
change language, framework, host, model, or deployment method while its public URL and operational
contract stay stable.

### 3.5 Verification is proportional to risk

Run the smallest test set that gives credible evidence for the changed behavior during normal
development. Do not run every repository's complete suite after every minor change.

Focused testing is not permission to skip verification. Full testing is mandatory before a major
release, production deployment, architecture migration, shared-contract change, or other change
whose failure could affect multiple tools or users.

### 3.6 Releases are explicit products

Every member repository owns its version, changelog, release notes, artifacts, compatibility
claims, and rollback information. A deployed working tree without a named version is not a release.

### 3.7 Common operations are centralized; domain safety stays local

The gateway owns network-wide controls such as TLS, routing, trusted client-IP handling, access
logs, request IDs, and general rate limits. The portal owns discovery, feedback, launch analytics,
and administration. Each tool still owns domain-specific validation, job concurrency, scientific
provenance, upload interpretation, and safe failure behavior.

## 4. Target architecture

```text
Office users
    |
    v
Internal DNS and HTTPS
    |
    v
Common reverse-proxy gateway
    |-- tools.<office-domain>     -> ml_server portal
    |-- hydride.tools.<domain>    -> HydrideSegmentation service on any approved VM
    |-- pytex.tools.<domain>      -> PyTex workbench on any approved VM
    |-- pdf.tools.<domain>        -> productivity-tools service on any approved VM
    `-- future.tools.<domain>     -> future independently deployed service
```

All user-facing names resolve to the gateway. Backend addresses and ports are private operational
details. Moving a service changes only infrastructure configuration, never the address already
shared with users.

Host-based routing is the default because the current tools use root-relative routes such as
`/api`, `/static`, and downloads. Path-prefix routing may be introduced only after the affected tool
explicitly supports a configurable base path and tests it through the gateway.

Backend services should accept traffic only from the gateway and approved administrators. The
portal must not relay scientific uploads or downloads through its Flask process; the gateway sends
them directly to the owning service.

## 5. Repository responsibilities

### 5.1 `ml_server`: portal and control surface

`ml_server` will own only:

- the stable homepage and searchable tool catalog;
- tool cards, categories, ownership, documentation links, and availability state;
- launch-event analytics;
- central user feedback and its authenticated administration workflow;
- maintenance announcements and platform status presentation;
- portal health, release identity, and operational metrics; and
- compatibility redirects from retired portal-owned routes.

It will not own scientific models, segmentation, diffraction, EBSD processing, PDF manipulation,
or other tool functionality. Celery, Redis, image libraries, PDF libraries, and model startup logic
must leave the portal when no remaining portal responsibility requires them.

The catalog must be data-driven and version-controlled. Adding a card must not require editing the
homepage template.

### 5.2 `HydrideSegmentation`: segmentation owner

This repository owns segmentation models, conventional and ML pipelines, model lifecycle,
scientific measurements, bounded job execution, reports, correction workflows, and segmentation
deployment behavior. The preliminary implementation in `ml_server` is retired after a documented
redirect and compatibility period.

### 5.3 `pytex`: crystallography and diffraction owner

This repository owns crystallographic data models, texture, diffraction, EBSD, TEM,
orientation-relationship analysis, the PyTex workbench, and their scientific contracts. Portal or
gateway integration must not weaken its frame, symmetry, provenance, validation, documentation, or
explainable-result requirements.

### 5.4 Productivity-tools repository

Lightweight office utilities such as PDF merge and extraction belong in a separately released
repository and service. A compute-heavy or independently evolving capability such as a real
super-resolution product should gain its own repository instead of turning the productivity
service into another monolith.

### 5.5 Platform-infrastructure repository

Gateway configuration, internal DNS inventory, deployment templates, monitoring configuration,
backup procedures, service accounts, firewall expectations, smoke checks, and rollback runbooks
belong in a dedicated infrastructure repository. Secrets and private keys never belong in Git.

## 6. Shared operational contract

Every production tool must declare:

- a stable tool identifier;
- a user-facing name, summary, category, icon, owner, and support contact;
- a stable public URL routed through the gateway;
- a lightweight health endpoint that does not initiate expensive computation;
- a machine-readable application name and release version;
- upload-size, timeout, and expected-concurrency limits;
- whether it persists uploads, results, logs, or user identifiers, and for how long;
- a documentation URL and release-notes URL;
- a central-feedback link carrying the tool identifier and optional page context; and
- a deployment and rollback procedure.

The preferred health response is:

```json
{
  "status": "ok",
  "tool_id": "example-tool",
  "version": "1.2.3"
}
```

Existing tools may use their current health shape during migration, with the portal adapter
recording the difference. New tools use the preferred contract from their first release.

Gateway request IDs must be forwarded to tools and included in tool logs where practical. Tools
must trust forwarded client-IP or identity headers only when the direct peer is the approved
gateway.

## 7. Data-driven discovery and future-tool onboarding

The portal catalog is a reviewed source file or schema-backed data set. At minimum, each entry
contains:

- `id`, `name`, `summary`, `category`, `tags`, and display order;
- public URL and internal health target;
- icon and documentation link;
- owning repository, owner, and support contact;
- lifecycle state: `experimental`, `active`, `maintenance`, `retired`, or `unavailable`;
- access policy or user group when applicable; and
- expected release version or version-discovery method.

Adding a tool follows one repeatable workflow:

1. Establish the owning repository and release identity.
2. Implement the shared operational contract and focused contract tests.
3. Deploy the service privately and pass direct health and functional smoke tests.
4. Add gateway routing, limits, logging, and TLS.
5. Add and validate one portal catalog entry.
6. Verify the tool launches in a new tab, reports feedback context, and survives an upstream
   restart or unavailable state gracefully.
7. Commit and push the tool, infrastructure, and portal increments to each repository's `main`,
   recording their exact commits in the coordinating progress ledger.

No homepage template edit is part of this workflow.

## 8. Development and progress workflow

### 8.1 Before implementation

- Read this document and the affected repositories' local governance.
- Read the current progress ledger and recent `main` history.
- Inspect the worktree and preserve unrelated changes.
- State the objective, in-scope repositories, expected contracts, risks, verification plan, and
  release impact in the ledger.
- Confirm whether the task changes a public URL, shared contract, stored data, scientific meaning,
  security boundary, or deployment procedure.

### 8.2 During implementation

- Work in small, self-consistent increments on `main`.
- Update code, tests, documentation, configuration examples, and release notes together when they
  describe the same behavior.
- Keep tool-specific logic out of the portal and gateway.
- Keep secrets, generated build output, local data, logs, caches, and inspection artifacts out of
  version control unless a repository explicitly defines a referenced canonical asset.
- Update the ledger before and after any step whose interruption would otherwise lose context.
- Stage explicit files, run focused verification, commit, and push after each substantial green
  increment.

### 8.3 Resuming interrupted work

The resuming contributor must:

1. read the ledger's objective and next actions;
2. compare recorded commits with `origin/main` in every affected repository;
3. inspect uncommitted and untracked files without deleting them;
4. verify the last recorded successful check if the environment may have changed;
5. continue from the first incomplete action; and
6. update the ledger with the resumed session and any discovered divergence.

### 8.4 Closing a goal

A goal is complete only when:

- the requested behavior and documentation exist;
- focused tests pass in every affected repository;
- cross-repository contracts and gateway behavior are verified where relevant;
- release notes and versions are updated when required;
- all intended commits are present on `origin/main`;
- the ledger records final verification, deployed state if applicable, rollback instructions, and
  any deferred work; and
- no required action remains only in a chat message or local worktree.

## 9. Proportional testing policy

Testing depth follows change risk.

### 9.1 Minor, localized changes

Run focused tests for the changed module, route, template, schema, or documentation contract.
Examples include:

- a relevant unit-test file;
- template-render and route tests for one portal page;
- schema validation for one catalog change;
- documentation lint, link, or spelling checks for a documentation-only change; and
- a targeted service test for a localized bug fix.

### 9.2 Shared or integration changes

Run focused unit tests plus the relevant integration and contract tests when changing:

- the gateway-to-tool headers or routing behavior;
- health, version, feedback, or catalog contracts;
- authentication, storage, migrations, uploads, downloads, or job orchestration;
- shared deployment configuration; or
- behavior consumed by another repository.

### 9.3 Full verification gates

Run the complete repository test suite, required static checks, and deployment smoke tests before:

- a major or minor production release;
- any production deployment;
- a platform architecture or data migration;
- deleting a compatibility route or legacy implementation;
- changing authentication, permissions, networking, or persistent storage;
- changing a stable scientific API or numerical algorithm under its repository's local rules; or
- declaring a development stage complete.

For a platform release or coordinated deployment, run the full release lane in every affected
repository, not in unrelated repositories. Record commands, versions, results, warnings, and
coverage in the progress ledger and release notes.

Tests must not introduce new warnings, leave resources open, reduce governed coverage, or silently
relax a scientific or security assertion.

## 10. Versioning and release governance

Each repository versions and releases independently using Semantic Versioning unless its local
governance documents a stronger domain-specific policy:

- `MAJOR`: incompatible public API, data-contract, URL, or operational-contract change;
- `MINOR`: backward-compatible functionality or substantial new capability; and
- `PATCH`: backward-compatible correction, documentation repair, or operational fix.

Every repository must maintain:

- one authoritative runtime version source;
- `CHANGELOG.md` with an `Unreleased` section;
- human-readable release notes for each production release;
- a Git tag matching the release version, such as `v1.4.0`;
- the build and deployment instructions for that release;
- migration and rollback notes when state or contracts change;
- compatibility notes for shared platform contracts; and
- provenance for released binaries, model checkpoints, containers, wheels, installers, or other
  deployed artifacts.

Release notes must identify added, changed, fixed, deprecated, removed, security-relevant, and
deployment-relevant behavior as applicable. A tool's UI and health response must show or expose the
version actually running, not a manually typed display value.

The portal has its own version; it does not impose one common version across independent tools. A
coordinated platform deployment records a release manifest containing the exact released version
and Git commit of the portal, gateway configuration, and every tool included in that deployment.

No release is complete until its artifacts can be associated with a source commit and its rollback
path has been documented and, for production-critical changes, exercised.

## 11. Security, privacy, and traffic governance

The gateway owns:

- HTTPS and certificate management;
- authentication or office-network access policy;
- stable host routing and upstream selection;
- trusted client-IP processing;
- structured access logs and request IDs;
- general connection and request-rate limits;
- per-tool body-size and timeout ceilings; and
- safe maintenance or upstream-unavailable responses.

Individual tools own validation and resource limits that require domain knowledge. Hydride job
capacity and PyTex scientific-computation serialization, for example, cannot be inferred safely by
the gateway.

Access logs must not contain request bodies, secrets, authorization headers, feedback messages, or
private scientific data. Raw IP retention, user identity, feedback contact information, and backup
retention must be documented and approved under office policy. Administrative actions and feedback
state changes must be auditable.

Backend ports are not public user interfaces. Firewalls must restrict them to the gateway and
approved operators. Existing tools without authentication may be deployed only behind this
boundary or on an explicitly trusted network while migration is underway.

## 12. Staged platform roadmap

### Stage 0: governance, baseline, and inventory

**Goal:** Establish one authoritative plan and a recoverable baseline before structural changes.

**Deliverables:**

- adopt this document from every member repository;
- create local and coordinating progress ledgers;
- inventory routes, dependencies, data stores, ports, health endpoints, owners, and versions;
- reconcile existing worktrees and `origin/main` without losing user work;
- classify duplicate, experimental, production, and retired capabilities; and
- decide internal DNS, TLS, identity, log retention, and backup ownership.

**Success looks like:** Any contributor can identify the owner, state, next action, last pushed
commit, and verification evidence for every migration item without consulting chat history.

### Stage 1: stable gateway and network boundary

**Goal:** Decouple public URLs from backend machines.

**Deliverables:**

- infrastructure repository;
- common reverse-proxy gateway;
- stable portal and tool hostnames;
- TLS, trusted client-IP handling, access logs, request IDs, rate limits, and timeouts;
- backend firewall restrictions; and
- health and rollback smoke checks.

**Success looks like:** A tool can move to a different VM by changing only reviewed infrastructure
configuration. Users keep the same URL, and the old upstream can be restored quickly.

### Stage 2: `ml_server` becomes the portal

**Goal:** Make the entry website stable, data-driven, and free of tool implementations.

**Deliverables:**

- schema-validated tool catalog;
- catalog-generated homepage and new-tab launch behavior;
- central PostgreSQL-backed feedback and authenticated administration;
- launch analytics, maintenance notices, and cached health state;
- compatibility redirects; and
- removal of portal dependencies that exist only for legacy tools.

**Success looks like:** Adding or reordering a tool requires a catalog change, not a template or
route change. A failed tool appears unavailable without slowing or breaking the homepage.

### Stage 3: dedicated HydrideSegmentation and PyTex cutover

**Goal:** Put the mature domain applications behind stable gateway URLs.

**Deliverables:**

- independently released and deployed HydrideSegmentation and PyTex services;
- gateway health, upload, download, timeout, and concurrency verification;
- central feedback links and portal-return links;
- redirects from obsolete portal routes; and
- deployment, rollback, and capacity notes for both services.

**Success looks like:** Users launch each dedicated application from the unchanged portal. No
hydride or PyTex scientific behavior is implemented in `ml_server`, and moving either service does
not change its public link.

### Stage 4: productivity extraction and duplicate retirement

**Goal:** Complete single ownership for the remaining portal tools.

**Deliverables:**

- separately released productivity-tools service for supported PDF utilities;
- an explicit product decision for super-resolution;
- retirement or validated ownership of the EBSD-cleanup stub;
- deletion of preliminary hydride code after its compatibility window; and
- removal of unused Celery, Redis, model, image, and PDF dependencies from the portal.

**Success looks like:** `ml_server` can be installed and operated without scientific, model, or
document-processing dependencies. Every visible card names one maintained owner and release.

### Stage 5: operational maturity

**Goal:** Make the platform supportable across reboots, failures, upgrades, and staff changes.

**Deliverables:**

- monitoring for gateway and tool availability, latency, errors, queues, and disk use;
- tested database, configuration, and artifact backups;
- deployment and rollback automation;
- release manifest and compatibility reporting;
- maintenance windows and user-facing status communication; and
- disaster-recovery and gateway-replacement procedures.

**Success looks like:** An operator can identify a failing layer, restore service, recover feedback,
and roll back a deployment using repository documentation alone.

### Stage 6: repeatable growth

**Goal:** Make new-tool onboarding ordinary rather than architectural work.

**Deliverables:**

- validated service and catalog templates;
- focused contract and gateway smoke tests;
- a release checklist and ownership checklist;
- documented capacity and privacy declarations; and
- periodic retirement review for unused or unsupported tools.

**Success looks like:** A compliant new tool is added through one repeatable checklist, appears on
the unchanged homepage, has a stable URL and owner, records feedback centrally, exposes its running
version, and can be removed without breaking other services.

## 13. Platform definition of done

A platform change is done only when all applicable items are true:

- ownership and repository boundaries remain clear;
- implementation, focused tests, documentation, configuration examples, and release notes agree;
- security, privacy, persistence, and rollback consequences are explicit;
- shared contracts have automated tests;
- public URLs remain stable or have documented compatibility redirects;
- exact commits and verification results are recorded in the ledger;
- completed increments are committed and pushed to `origin/main` in every affected repository;
- deployment status is recorded when deployment was in scope; and
- another contributor can resume any remaining work from the repository alone.

## 14. Governance review questions

Before completing a substantial increment, answer:

- Does this put a capability in more than one repository?
- Does it make the portal aware of tool internals?
- Does it expose a backend address or unstable URL to users?
- Does it change a shared contract, stored record, scientific meaning, or security boundary?
- Can the focused tests actually detect the likely failure introduced by this change?
- Is full verification now required by the release gates?
- Are the version, changelog, release notes, migration, and rollback information current?
- Is every completed step pushed to `main`?
- Could a new contributor resume immediately from the ledger and Git history?

If any answer is uncertain, the change is not ready to close.

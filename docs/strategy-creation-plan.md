# Strategy Creation Feature Plan

## Current State Snapshot
- The Strategy Library screen already presents a primary "Create New Strategy" call to action, but it only opens a placeholder modal and informational toast without collecting user input or persisting anything (`showCreateModal` handler and toast messaging). This leaves a visible gap between user intent and functionality (`frontend/src/pages/Strategies/Strategies.tsx:132`, `frontend/src/pages/Strategies/Strategies.tsx:240`).
- Strategies are read via `useStrategiesData`, which ultimately calls `StrategyService.getStrategies()` to pull registered entries from the backend registry API (`frontend/src/hooks/useStrategiesData.ts:8`, `frontend/src/services/strategyService.ts:33`).
- Strategy management on the backend focuses on discovering filesystem strategies, registering them in the database, and validating them. There is no route that creates a brand-new strategy artifact or DB record from scratch (`backend/app/api/v1/strategies.py:18`, `backend/app/services/strategy_service.py:59`).
- Each strategy is expected to be a Python class stored under `strategies/`, inheriting from `StrategyBase` and implementing `generate_signals()` (and optionally configuration helpers), so any creation flow must ultimately produce such a file (`backtester/strategy_base.py:6`).

## Goals & Guardrails
- Deliver a lightweight, easy-to-understand creation experience directly inside the Strategies view.
- Keep first delivery narrow enough to ship quickly, yet extensible toward richer authoring later (e.g., inline editor, code preview).
- Ensure newly created strategies become discoverable by the existing discovery/registration pipeline without requiring the user to leave the page.
- Maintain deterministic, testable strategy code with minimal risk of users creating invalid modules.

## User Flow Options
### Option A — Guided Template Wizard (Recommended MVP)
1. User clicks "Create New Strategy".
2. Multi-step modal collects metadata (strategy name, description), optional parameter scaffolding, and picks a starting template (e.g., moving average crossover, blank skeleton).
3. On submit, frontend requests backend to generate the file and register the strategy (see backend requirements below).
4. When the API confirms success, run `refetch()` so the new strategy appears immediately in the grid; show success toast and deep-link to the detail view.

**Pros:** Fast to build UI (reuses existing modal, form primitives); constrains output to known-good templates; low user error. **Cons:** No free-form coding yet; requires server-side templating.

### Option B — Upload Existing Strategy File
1. Provide an "Upload Python file" tab in the same modal.
2. Accept `.py` file, show basic lint/validation feedback via `/strategies/validate-by-path` before persisting.
3. Backend saves file into `strategies/` namespace and registers it.

**Pros:** Enables advanced users to onboard existing logic fast. **Cons:** Requires sandboxing and validation to avoid unsafe code; needs backend write safeguards.

### Option C — Full Inline Code Editor (Future)
1. Embed a richer editor (Monaco/CodeMirror) with syntax highlighting.
2. Offer live parameter schema builder, linting, and preview backtests.

**Pros:** Powerful experience. **Cons:** Significant scope (state management, diffing, linting); not ideal for short-term delivery.

## Recommended MVP Blueprint (Option A Core)
1. **Modal Structure** – Convert the existing placeholder modal into a multi-step wizard using the shared `Modal` component and stepper UI (or light wrapper). Step 1: Strategy metadata. Step 2: Template selection & parameter schema seeds. Step 3: Summary + create.
2. **Form Controls** – Reuse `Button`, `Card`, `Badge`, and form utility components for consistent styling; add small `FormField` wrappers if needed for validation feedback.
3. **Template Definitions** – Maintain a frontend constant (or fetch from backend) describing templates: identifier, display label, description, default parameter schema. This can later be served by the API to keep templates in sync.
4. **API Contract** – Introduce a `StrategyService.createStrategy()` client that POSTs to a new backend route (e.g., `POST /api/v1/strategies/`) with payload `{ name, description, template_key, parameters_schema, default_parameters }`. The backend should materialize the Python file, optionally run validation, register it, and return the new strategy metadata.
5. **Post-Create Handling** – On success, close modal, call `refetch()` from `useStrategiesData`, and optionally navigate to the detail view (`handleStrategyClick`) to encourage next actions.
6. **Error States** – Surface backend validation errors inline; keep the modal open and highlight offending fields.

## Backend Considerations (Needed to Unlock Frontend)
- **New Endpoint:** Implement a create route that orchestrates file generation and DB registration. It can reuse `StrategyRegistry.register_strategies` after writing the file to disk (`backend/app/services/strategy_service.py:59`).
- **Template Engine:** Store template files or Jinja2 snippets server-side to produce structured strategy modules conforming to `StrategyBase` (`backtester/strategy_base.py:6`).
- **Validation:** Run the existing validation routine before finalizing create; respond with errors so the UI can prompt fixes (`backend/app/api/v1/strategies.py:130`).
- **Safety:** Sanitize identifiers (module + class names), prevent overwriting existing files without explicit confirmation, and ensure generated modules pass discovery checks.

## Frontend Implementation Notes
- **State Management:** Keep wizard state local to the Strategies page; pass callbacks into the Modal, similar to how backtest modal state is handled now (`frontend/src/pages/Strategies/Strategies.tsx:210`).
- **Service Layer:** Extend `StrategyService` with `createStrategy`, `listTemplates`, and optionally `validateDraft` helpers, mirroring the existing fetch/validate patterns (`frontend/src/services/strategyService.ts:33`).
- **Grid Refresh:** Ensure the create flow calls `refetch()` so the new strategy surfaces in the `StrategiesGrid` without requiring manual reload (`frontend/src/hooks/useStrategiesData.ts:35`).
- **Empty State CTA:** When no strategies exist, reuse the grid’s empty-state CTA so creation is discoverable (`frontend/src/components/strategies/StrategiesGrid.tsx:20`).

## Validation & UX Enhancements
- Enforce unique strategy names on the frontend before calling the API; cross-check via current `strategies` state.
- Provide inline JSON schema builder for parameters (fields: type, default, bounds) with basic validation.
- Offer quick preview for generated module path/class naming so advanced users trust the output.
- Add success toast and optional link to trigger an immediate backtest setup (integrate with existing backtest modal logic).

## Delivery Phasing & Effort
1. **MVP (2–3 days):** Modal wizard + template selection + new API integration; backend endpoint with simple templates and validation.
2. **Enhancement (1–2 days):** File upload tab with validation using `/strategies/validate-by-path` before registration.
3. **Future Roadmap:** Inline editor, live linting, collaborative drafts, version history.

## Open Questions
- Should generated strategies live purely on disk, or do we want DB-backed storage with code blobs for audit/versioning?
- Do we require role-based access to restrict who can create strategies?
- How should we handle cleanup if validation fails after file generation (rollback, temp directories)?

## Next Steps
- Align with backend team on creation endpoint contract and template storage.
- Define initial template set (e.g., SMA crossover, RSI mean reversion, empty skeleton).
- Wireframe the modal steps to confirm UX, then implement frontend wizard scaffolding.
- Implement backend route(s), run discovery/registration automatically, and expose new service methods.
- QA the end-to-end flow with sample template, ensuring the strategy appears in the grid and can run a backtest immediately.

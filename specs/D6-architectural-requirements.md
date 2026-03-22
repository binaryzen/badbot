# D6 — Architectural Requirements & Constraints

## Architectural Requirements

Non-functional requirements expressed as observable, testable statements. Prefixed AR- to distinguish from functional requirements.

**AR-001** `[M]` The tool shall add no more than 50ms of per-step processing overhead beyond actual network round-trip time, measured against a local loopback target with a no-op protocol definition.

**AR-002** `[M]` Session artifact save and load operations shall each complete in under 2 seconds for a session containing up to 100 sequence executions and 1,000 log entries.

**AR-003** `[M]` Buffer parse and dual-view render for a single buffer up to 64KB shall complete in under 500ms.

**AR-004** `[M]` The tool shall require no server infrastructure, background daemon, database, or persistent network service to operate. All state lives on the local filesystem.

**AR-005** `[M]` The tool shall run without modification on Windows 10+, macOS 12+, and mainstream Linux distributions (Ubuntu 20.04+, Fedora 36+).

**AR-006** `[M]` The tool shall target Python 3.10 or later. No features requiring a later version shall be used without explicit justification.

**AR-007** `[M]` The tool shall be distributable as a pip-installable package with no mandatory build step for the end user.

**AR-008** `[M]` Each component (C-01 through C-14, U-01) shall be testable in isolation using constructor or parameter injection. No component test shall require network access, an external process, or another non-mocked component.

**AR-009** `[M]` All inter-component dependencies shall be expressed as constructor or function parameter injection. No component shall depend on module-level singletons or global mutable state.

**AR-010** `[M]` The core library (C-01 through C-12, U-01) shall have no import dependency on C-13 (Library API) or C-14 (CLI Layer). The dependency graph shall remain strictly top-down.

**AR-011** `[M]` Session artifacts shall be forward-compatible: a newer tool version shall load an artifact produced by an older version without data loss, applying migration (FR-007) where schema changes require it.

**AR-012** `[M]` The plugin interface shall follow semantic versioning as a public contract: minor versions may add; patch versions may fix; major versions may break with a defined migration path. A version support window of at minimum two major versions shall be maintained.

**AR-013** `[S]` The tool shall emit structured diagnostic logs — distinct from the session execution log — at a configurable log level, to support debugging of tool internals without exposing session data.

---

## Constraints

Each constraint states the decision, its rationale, its cost, and the tradeoff accepted.

---

### CON-01 — Implementation Language: Python 3.10+

**Decision:** Python is the sole implementation language for the core library and all first-party components.

**Rationale:** The entire selected OSS stack (mitmproxy, Construct, transitions, Boofuzz, Hypothesis, Prefect, jwt-tool, CORScanner, Arjun) is Python-native. Python allows library-level integration for all of these rather than subprocess wrappers, directly reducing integration cost across the board.

**Cost:** Not distributed as a compiled binary by default. Requires Python to be installed by the user. Higher memory footprint and startup time than Go or Rust.

**Tradeoff:** Development velocity and OSS leverage depth (library imports vs. subprocess wrappers) vs. distribution simplicity and runtime performance. Accepted because the OSS stack advantage is decisive and startup/runtime performance is not a primary concern for an interactive security testing tool.

---

### CON-02 — Deployment: Local Only, No Server Infrastructure

**Decision:** The tool operates entirely on the local machine. No server, no database, no cloud dependency.

**Rationale:** CLI-first model; works offline and in air-gapped environments; no authentication or multi-tenancy complexity; session artifacts are files the user controls directly.

**Cost:** No collaborative features without manual artifact transfer. No central finding aggregation across users or machines. Remote execution not possible.

**Tradeoff:** Simplicity, portability, and security (no external attack surface) vs. collaboration and remote orchestration. Accepted because the primary use case (a Domain Engineer testing their own application) is inherently local. Collaboration via artifact sharing is sufficient for v1.

---

### CON-03 — License Strategy: No GPL-Linked Dependencies

**Decision:** No GPL-licensed library shall be imported as a direct dependency. GPL-licensed tools may be invoked as subprocesses only.

**Rationale:** Keeps the tool's licensing options open for both open source (MIT/Apache) and commercial distribution. A GPL-linked dependency imposes GPL terms on the entire tool.

**Cost:** Cannot import Scapy or libwireshark directly. tshark used as subprocess only — loses real-time streaming of dissection results; tshark output must be buffered and parsed.

**Tradeoff:** Licensing flexibility vs. access to the richest binary protocol dissection library (libwireshark). Accepted because tshark subprocess covers the dissection use case and Construct covers the build/parse use case.

---

### CON-04 — Protocol Scope: Pluggable, Protocol-Agnostic Core

**Decision:** The core tool has no built-in knowledge of any specific protocol. All protocol behavior is provided via plugins loaded at runtime.

**Rationale:** Enables gradual onboarding of protocols, community contribution, and product extensibility. The HTTP/REST seed plugin validates the model before it is published as a public API.

**Cost:** Higher architectural scaffolding than a single-protocol tool. Protocol definition authoring has a higher initial learning curve. First working test requires loading a protocol definition.

**Tradeoff:** Long-term scalability and extensibility vs. short-term time-to-first-test. Accepted because the HTTP/REST seed plugin ships bundled — the Domain Engineer doesn't author a definition to get started.

---

### CON-05 — Plugin Interface v1 Publication Timing

**Decision:** Plugin interface v1 is not published as a public contract until the HTTP/REST seed plugin has been implemented internally and has validated the contract under real conditions.

**Rationale:** Premature API commitment requiring a breaking change causes version churn and damages ecosystem trust. The seed plugin is the proof of concept.

**Cost:** Community cannot build third-party plugins until v1 is published. Delays ecosystem growth.

**Tradeoff:** API stability and ecosystem trust vs. ecosystem growth speed. Accepted because a broken API published early costs more than a delayed but stable one.

*Resolves: FR-030 vs FR-034 conflict from D3. FR-030 (Provider/Source abstraction, Must) ships with the seed plugin. FR-034 (custom plugin sources, Should) ships when v1 is published.*

---

### CON-06 — Context Store as the Single Redaction Enforcement Point

**Decision:** Sensitive values are stored exclusively in C-02 (Context Store). All other components receive opaque typed references. Raw value resolution happens only within C-07 (Sequence Engine) at message construction time.

**Rationale:** Structural security property — leakage is architecturally impossible rather than relying on per-integration discipline. Every new consumer of session data is automatically safe without additional enforcement.

**Cost:** Indirection overhead on every sensitive value access. Cognitive overhead for contributors — two access patterns (value() vs ref()) must be understood and applied correctly.

**Tradeoff:** Security property strength and future-safety vs. implementation simplicity. Accepted because the tool handles sensitive data by design — structural enforcement is the appropriate standard for a security tool.

---

### CON-07 — Prefect Result Persistence: Disabled

**Decision:** All Prefect tasks in C-09 (Suite Orchestrator) shall be configured with persist_result=False. Prefect is an orchestration engine only — not a data persistence layer.

**Rationale:** Belt-and-suspenders with CON-06. Even if a raw value were accidentally passed as a task argument, Prefect would not persist it to disk.

**Cost:** Prefect's result inspection and replay features are unavailable. Debugging failed suite runs requires reading the session log, not Prefect's UI.

**Tradeoff:** Defense in depth vs. orchestration observability. Accepted because the session log (C-10) provides full execution observability — Prefect's result layer is redundant.

---

### CON-08 — UI Layer Deferred; C-13 Is the Boundary

**Decision:** No interactive UI (TUI or local web UI) is built until the core library is stable. C-13 (Library API) is the sole boundary — any UI is a new consumer of C-13, not a modification of anything below it.

**Rationale:** Building a UI before the library API stabilizes risks coupling the UI to implementation details that will change. The C-13 boundary is already well-defined.

**Cost:** The Domain Engineer's primary experience (progressive disclosure, buffer visualization, interactive sequence authoring) is served by CLI until the UI is built.

**Tradeoff:** Architectural cleanliness and library API stability vs. earlier delivery of the rich interactive experience the primary persona needs. Accepted with the expectation that UI work begins immediately after the HTTP/REST seed plugin ships.

---

### CON-09 — HTTP/REST as the First Protocol

**Decision:** The HTTP/REST plugin is the first and only bundled protocol. Binary protocol support is deferred until after the plugin model is validated.

**Rationale:** The OSS landscape is overwhelmingly HTTP-oriented. HTTP/REST maximizes OSS leverage and addresses the highest-value API security scenarios (S-01 through S-07 from D4). Covers the widest Domain Engineer use case.

**Cost:** Binary protocol testing, raw TCP, WebSocket beyond HTTP upgrade, and gRPC are not available in v1.

**Tradeoff:** Time-to-value for the primary use case vs. breadth of protocol coverage. Accepted because WebSocket and gRPC can be added as plugins without touching core.

---

## Constraint / FR Consistency Check

| Constraint | Potentially Conflicting FRs | Resolution |
|---|---|---|
| CON-01 (Python only) | FR-034 (custom plugins) — plugins must also be Python | Acceptable — document as a plugin authoring requirement |
| CON-03 (no GPL links) | FR-019–FR-024 (buffer rendering) — richest dissection is GPL | Resolved — tshark subprocess + Construct covers both rendering and build/parse |
| CON-04 (pluggable core) | FR-021 (field correlation) — requires protocol schema knowledge | Resolved — C-06 uses C-03's schema; no hardcoded protocol knowledge in core |
| CON-07 (Prefect no-persist) | FR-065 (parallel execution) | No conflict — parallelism is Prefect's execution model; result persistence is independent |
| CON-08 (UI deferred) | FR-021, FR-023 (interactive selection in visualization) | Known gap — interactive selection requires richer UI than CLI provides; resolved when UI ships |

---

## Summary

| Category | Count |
|---|---|
| Architectural Requirements | 13 (AR-001–AR-013) |
| Constraints | 9 (CON-01–CON-09) |
| Tradeoffs named | 9 (one per constraint) |
| Constraint/FR conflicts checked | 5 — all resolved or explicitly accepted |
| Open items resolved from D3 | 1 (FR-030 vs FR-034 plugin timing) |

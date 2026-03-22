# D4 — OSS Landscape Analysis

## API Security Testing Scenario Analysis

Eight scenarios evaluated for coverage, OSS tool fit, and build/leverage decisions.

| # | Scenario | OSS Coverage | Decision | Integration Candidate |
|---|---|---|---|---|
| S-01 | Auth token lifecycle | Partial (jwt-tool, mitmproxy) | Hybrid | jwt-tool as mutation source |
| S-02 | BOLA/IDOR | Weak (Burp-dependent) | Build | None strong |
| S-03 | Input fuzzing (boundary, type confusion, injection) | Strong (RESTler, Boofuzz) | Leverage | RESTler approach; Boofuzz primitives |
| S-04 | Excessive data exposure | Partial (Dredd) | Hybrid | OpenAPI spec as protocol definition input |
| S-05 | Mass assignment | Weak (Arjun) | Build | Arjun for parameter discovery phase |
| S-06 | Rate limiting verification | Weak | Build | None |
| S-07 | CORS misconfiguration | Strong (CORScanner) | Leverage | CORScanner as wrapped check |
| S-08 | Multi-step workflow bypass | None | Build | None — highest-differentiation native capability |

**Highest-differentiation scenarios (weakest OSS coverage, strongest native tool advantage):**
- S-02 BOLA/IDOR — multi-session context management not supported without Burp
- S-08 Workflow bypass — precisely what state machine + context extraction was designed for
- S-01 multi-session auth — token lifecycle across sessions benefits from native sequence model

---

## OSS Landscape by Functional Area

**Integration cost scale:** Low = import as library / minimal wrapping — Medium = subprocess or API boundary — High = significant adaptation or architectural coupling risk

---

### Area 1 — Protocol Definition & Parsing

**Kaitai Struct**
- Covers: binary protocol structure definition, field types, variable-length fields, conditional fields, enums
- Gaps: no sequence/state machine support; read-only (parse only, no generate)
- License: Compiler GPL-3.0 ⚠️; generated code and Python runtime MIT ✓
- Integration cost: Medium
- Verdict: **Leverage as reference model and parse-side integration for binary protocols.** The .ksy format is a strong candidate for the binary protocol definition schema.

**Construct** (Python)
- Covers: binary struct definition, nested structures, variable-length fields, conditional logic; bidirectional (parse AND build)
- Gaps: no sequence support; code-driven not config-driven
- License: MIT ✓
- Integration cost: Low
- Verdict: **Leverage as the binary protocol parse/build engine.** Bidirectionality is critical.

**OpenAPI parsers** (prance, openapi-core, swagger-parser)
- Covers: REST endpoint definitions, parameter schemas, request/response structure, security scheme declarations
- Gaps: no binary protocol support; no state machine sequences
- License: MIT/Apache ✓
- Integration cost: Low
- Verdict: **Leverage for FR-067/FR-068 (OpenAPI ingestion).** First-class REST API definition import path.

**Scapy**
- Covers: wide range of network protocols L2–L7; packet crafting, sending, capturing, dissecting
- Gaps: GPL license creates copyleft obligation if linked; definitions are code not config
- License: GPL-2.0 ⚠️
- Integration cost: Medium
- Verdict: **Reference only. Do not take as direct dependency.** Use Construct for parse/build. Treat Scapy-based tools as subprocess integrations only.

---

### Area 2 — Protocol Buffer Rendering

**Wireshark / tshark**
- Covers: thousands of protocols; field-level dissection; hex dump output; JSON output via tshark
- Gaps: GUI-only for interactive use; libwireshark is GPL-2.0; tshark subprocess loses real-time interactivity
- License: GPL-2.0 ⚠️ — subprocess use avoids copyleft; linking does not
- Integration cost: Medium
- Verdict: **Leverage tshark as subprocess for dissection.** Call tshark for dissection output; render natively. Do not link libwireshark.

**hexyl**
- Covers: clean terminal hex display with color-coded byte categories
- Gaps: no protocol-aware field annotations; display only
- License: MIT ✓
- Integration cost: Low (reference)
- Verdict: **Reference for low-level hex view rendering approach.** Adopt its visual model natively; not a direct dependency.

**Gap:** No OSS tool provides dual-view (high-level ↔ low-level) with interactive field correlation. Rendering layer is **Build**; tshark provides dissection data; hexyl informs visual design.

---

### Area 3 — State Machine / Sequence Engine

**transitions** (Python)
- Covers: named states, transitions, triggers, callbacks on enter/exit, condition guards, hierarchical states
- Gaps: no protocol awareness; no built-in serialization; no sequence definition format
- License: MIT ✓
- Integration cost: Low
- Verdict: **Leverage as the FSM engine underlying FR-025.** Build the sequence node configuration layer on top.

No OSS tool provides the full sequence node model (state machine with role assignment, data source binding, protocol-aware transitions). Sequence execution layer is entirely **Build** using transitions as the engine.

---

### Area 4 — Data Source / Provider

**Boofuzz** (Python)
- Covers: binary protocol fuzzing primitives; mutation strategies; session recording
- Gaps: tightly coupled to its own session model; not easily decomposed into a standalone Source
- License: MIT ✓
- Integration cost: Medium
- Verdict: **Leverage Boofuzz's primitive model as the mutation-based generative Source for binary protocols.**

**RESTler** (Microsoft Research)
- Covers: grammar-based stateful REST API fuzzing; OpenAPI input; dependency chaining (uses response values in subsequent requests)
- Gaps: .NET/F# — language boundary; not a library; subprocess integration requires output parsing
- License: MIT ✓
- Integration cost: High
- Verdict: **Adopt RESTler's dependency-chaining approach as design reference; do not integrate directly.** Its approach validates our context extraction model. Adopt the approach, not the tool.

**AFL++**
- Covers: coverage-guided mutation fuzzing for compiled targets
- Gaps: requires target instrumentation; not applicable to network API testing without significant adaptation
- License: Apache 2.0 ✓
- Integration cost: High
- Verdict: **Deferred.** Relevant only if scope extends to testing compiled protocol handlers directly.

**Hypothesis** (Python)
- Covers: property-based testing with smart data generation; shrinking on failure
- Gaps: not protocol-aware natively
- License: MPL-2.0 ✓
- Integration cost: Low
- Verdict: **Leverage as the parameterized template Source engine.**

---

### Area 5 — Proxy / MITM

**mitmproxy** (Python)
- Covers: HTTP/1.1, HTTP/2, HTTPS, WebSocket; Python addon API; flow serialization; certificate management
- Gaps: HTTP-centric; raw TCP/binary protocol MITM requires lower-level approach; no built-in state machine
- License: MIT ✓
- Integration cost: Low
- Verdict: **Leverage as the proxy layer for HTTP/HTTPS.** Strongest OSS candidate in the analysis — high coverage, clean Python API, correct license. MITM for HTTP/HTTPS is essentially solved.

**mkcert**
- Covers: local CA creation, trust store installation, certificate generation for localhost
- License: MIT ✓
- Integration cost: Low
- Verdict: **Leverage for TLS provisioning (FR-048–FR-050).** Already decided.

---

### Area 6 — Suite Orchestration

**Prefect v3** (local mode)
- Covers: flow/task model; retry logic; parallel execution (asyncio-backed); state persistence to local filesystem; no server required in local mode
- Gaps: result persistence may capture sensitive values from task outputs — mitigated by typed context store (raw values never passed as task results)
- License: Apache 2.0 ✓
- Integration cost: Low-Medium
- Verdict: **Leverage for suite-level orchestration (UC-15).** `@flow` = test suite; `@task` = sequence execution unit. Prefect result persistence disabled (`persist_result=False`) as belt-and-suspenders; primary protection is the typed context store ensuring raw values are never passed as task arguments.

**asyncio** (Python stdlib)
- Covers: async I/O, concurrent execution, timeout/cancellation
- License: Python stdlib
- Integration cost: Low (already required for network I/O)
- Verdict: **Leverage as the async foundation throughout.** Required regardless of orchestration choice.

---

### Area 7 — API-Specific Security Checks

**jwt-tool**
- Covers: algorithm confusion (RS256→HS256), none-alg, key injection, claim manipulation
- License: MIT ✓
- Integration cost: Low-Medium
- Verdict: **Leverage as a mutation Source implementation for JWT fields.**

**CORScanner**
- Covers: reflected origin, wildcard + credentials, dangerous method allowance
- License: MIT ✓
- Integration cost: Low
- Verdict: **Leverage as a wrapped check for S-07 (CORS misconfiguration).**

**Arjun**
- Covers: hidden HTTP parameter discovery via wordlist and heuristics
- License: MIT ✓
- Integration cost: Low
- Verdict: **Leverage in the discovery phase (UC-01) for REST APIs.**

**nuclei**
- Covers: template-based vulnerability scanning; large community template library
- Gaps: template execution model not directly portable to our sequence format
- License: MIT ✓
- Integration cost: High
- Verdict: **Use nuclei templates as content reference for our sequence definition library; do not integrate the engine.**

**OWASP ZAP**
- Covers: broad vulnerability coverage; passive and active scanning
- Gaps: Java process; architectural mismatch with our sequence model
- License: Apache 2.0 ✓
- Integration cost: High
- Verdict: **Out of scope as direct dependency.** Use as reference for vulnerability coverage completeness.

**Dredd**
- Covers: API contract testing against OpenAPI specs; runtime response validation
- License: Apache 2.0 ✓
- Integration cost: Low-Medium
- Verdict: **Leverage as optional integration for contract validation (S-04).**

---

## Full Verdict Matrix

| Functional Area | Verdict | Primary OSS Candidate | License | Integration Cost | Covers (FRs) |
|---|---|---|---|---|---|
| Binary protocol parse/build | Leverage | Construct | MIT | Low | FR-010, FR-011, FR-015, FR-016 |
| Binary protocol schema format | Leverage (reference) | Kaitai Struct (.ksy) | MIT (runtime) | Medium | FR-010 (reference) |
| REST protocol definition | Leverage | OpenAPI parsers | MIT/Apache | Low | FR-010, FR-067, FR-068 |
| Buffer rendering — dissection | Leverage | tshark (subprocess) | GPL-2.0 (subprocess safe) | Medium | FR-019, FR-020, FR-021, FR-047 |
| Buffer rendering — display | Build (reference hexyl) | hexyl | MIT | Low | FR-019, FR-020, FR-021, FR-022, FR-024 |
| State machine engine | Leverage | transitions (Python) | MIT | Low | FR-025, FR-026, FR-027, FR-028, FR-029 |
| Sequence execution | Build | — | — | — | FR-037–FR-045 |
| Mutation-based fuzzing (binary) | Leverage | Boofuzz primitives | MIT | Medium | FR-030, FR-035, FR-036 |
| Grammar-based fuzzing (REST) | Leverage (approach) | RESTler (reference) | MIT | High (adopt approach) | FR-030, FR-038, FR-039 |
| Parameterized generation | Leverage | Hypothesis | MPL-2.0 | Low | FR-030, FR-036 |
| HTTP/HTTPS proxy | Leverage | mitmproxy | MIT | Low | FR-046, FR-047, FR-051, FR-054, FR-055 |
| TLS provisioning | Leverage | mkcert | MIT | Low | FR-048, FR-049, FR-050 |
| Suite orchestration | Leverage | Prefect v3 (local mode) | Apache 2.0 | Low-Medium | FR-063, FR-065, FR-066, FR-069 |
| Async I/O / concurrency | Leverage | asyncio (stdlib) | Python stdlib | Low | FR-037, FR-042, FR-046, FR-065 |
| JWT mutation | Leverage | jwt-tool | MIT | Low-Medium | FR-030, FR-051 |
| CORS check | Leverage | CORScanner | MIT | Low | FR-030, FR-046 |
| Parameter discovery | Leverage | Arjun | MIT | Low | FR-068 |
| API contract validation | Leverage | Dredd | Apache 2.0 | Medium | FR-017, FR-018 |
| Session management | Build | — | — | — | FR-001–FR-009 |
| Reporting & output | Build | — | — | — | FR-056–FR-062 |
| Outbound TLS enforcement | Build (U-01 utility) | — | — | Low | FR-077 |
| Coverage-guided fuzzing | Deferred | AFL++ | Apache 2.0 | High | — |

---

## License Risk Summary

No GPL-linked dependencies required. All leveraged libraries are MIT, Apache 2.0, or MPL-2.0. Two GPL-licensed tools (Scapy, Wireshark/tshark) used as subprocess calls only — no copyleft obligation triggered. Tool's licensing options remain open for both open source and commercial distribution.

---

## Key Signals for D5

1. **Python is the implementation language.** Every leveraged library except RESTler and mkcert is Python-native. Named as architectural constraint in D6.

2. **RESTler's approach, not the tool.** Dependency-chaining validates our context extraction design. Adopt the approach; avoid the integration cost.

3. **Core proprietary build surface:** sequence execution engine, session model (including typed context store), and reporting format. Everything else is leveraged OSS or thin wrappers.

4. **First protocol: HTTP/REST with OpenAPI ingestion.** OSS landscape is overwhelmingly HTTP-oriented. Maximizes leverage and addresses S-01 through S-07 before extending to binary protocols.

5. **Prefect/context store boundary:** Prefect result persistence disabled; typed context store ensures raw sensitive values are never passed as Prefect task arguments. Two-layer protection.

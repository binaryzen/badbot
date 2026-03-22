# D7 — Master Specification

**Version:** 1.0
**Status:** Authoritative
**Date:** 2026-03-21
**Source documents:** D1 (User Stories), D2 (Use Cases), D3 (Functional Requirements), D4 (OSS Landscape), D5 (Modularization), D6 (Architectural Requirements & Constraints)

---

## Purpose

This document is the single authoritative specification for the tool. It synthesizes D1 through D6 into a self-contained reference that is developer-actionable without consulting source documents. All traceability chains are preserved inline. All contradictions and open items from prior documents are resolved here.

---

## 1. Product Summary

An interactive, local-only CLI tool for orchestrated ad-hoc networked application vulnerability testing. The tool enables a Domain Engineer — an engineer with solid technical depth but without formal security training — to discover, simulate, and verify security behaviors in their applications at the protocol level.

**Core value proposition:** The tool does what no existing OSS tool does on its own — stateful, context-aware, protocol-aware multi-step workflow execution with guided entry points, progressive disclosure, and reproducible session artifacts.

**In scope for v1:**
- HTTP/REST protocol (bundled seed plugin)
- Local proxy / MITM with TLS provisioning
- Sequence-based test execution with context extraction
- Suite execution with parallel/serial modes
- Session persistence with redaction policy
- CLI interface with structured JSON output

**Out of scope for v1:**
- Binary protocol testing (architecture supports it; deferred until after plugin model validates)
- WebSocket, gRPC, raw TCP (addable as plugins without core changes)
- Interactive TUI or local web UI (deferred until after HTTP/REST seed plugin ships)
- Plugin interface v1 public commitment (deferred until seed plugin validates contract)
- Collaborative features or remote execution

---

## 2. Personas

| Persona | Role | Tradeoff Authority |
|---|---|---|
| **[DE] Domain Engineer** | **Primary** | **Yes — when tradeoffs conflict, DE's needs take priority** |
| [SR] Security Researcher | Specialist — deep security and protocol knowledge | No |
| [PD] Protocol Developer | Specialist — protocol authoring and harness definition | No |
| [RTO] Red Team Operator | Specialist — scripted attack chains, reproducible artifacts | No |
| [AP] Automation Pipeline | Non-human — CI/CD consumers of structured output | No |

### Primary Persona Detail
An engineer with a CS degree and strong practical depth in one or two technical domains (e.g. backend, networking, embedded) but without formal security training. Capable of understanding complex multi-layer problems when context is surfaced — the gap is not comprehension, it's knowing where to look and what to look for.

**Key requirement pressures:**
- Context must travel with results (output explains significance, not just facts)
- Guided entry points — opinionated starting paths, not blank canvas
- Progressive disclosure — summary first, raw detail behind a drill-down
- Vocabulary bridging — security terms defined inline or mapped to known domain concepts

---

## 3. User Stories

**Priority key:** `[M]` Must — `[S]` Should — `[C]` Could

### Test Discovery & Guided Entry
**US-01** `[DE]` As a Domain Engineer, I want the tool to suggest relevant test categories when I point it at an application endpoint, so that I can start a meaningful test run without knowing the security testing vocabulary in advance.

**US-02** `[DE]` As a Domain Engineer, I want test results to explain what was found and why it matters in terms of application behavior, so that I can act on findings without having to separately research each vulnerability class.

### Protocol Visualization
**US-03** `[DE]` As a Domain Engineer, I want to see my application's protocol exchanges in a human-readable key/value format alongside the raw bytes, so that I can understand what's happening at both semantic and wire levels without switching tools.

**US-04** `[PD]` As a Protocol Developer, I want to inspect raw hex buffers with per-field annotations for a specific protocol, so that I can verify my implementation produces correctly structured messages.

**US-05** `[SR]` As a Security Researcher, I want to correlate decoded high-level fields with their exact byte positions in the stream, so that I can identify parsing discrepancies that may indicate exploitable edge cases.

### Simulation Test Bench
**US-06** `[DE]` As a Domain Engineer, I want to run my application against a simulated protocol peer without needing a live external service, so that I can test security behavior in a controlled, reproducible environment.

**US-07** `[PD]` As a Protocol Developer, I want to define a protocol harness that validates the structure and sequencing of request/response exchanges, so that I can catch malformed or out-of-order messages early in development.

**US-08** `[RTO]` As a Red Team Operator, I want to replay captured traffic and inject mutations at specified fields, so that I can test how the application handles unexpected or malformed inputs at the protocol level.

### Scripted Workflows
**US-09** `[DE]` As a Domain Engineer, I want to run a named test suite against my application with a single invocation and receive a prioritized summary report, so that I can integrate security checks into my development workflow without manual orchestration.

**US-10** `[RTO]` As a Red Team Operator, I want to script a multi-step attack chain that sequences protocol interactions with branching logic, so that I can automate complex scenarios that depend on stateful exchanges.

**US-11** `[AP]` As an Automation Pipeline, I want to execute a scripted test suite and receive structured output (pass/fail with traceable detail), so that I can gate deployments on security test results without human interpretation.

### Conditional Sequences & Context Extraction
**US-12** `[DE]` As a Domain Engineer, I want the tool to extract tokens or session values from application responses and automatically use them in subsequent requests, so that I can test authenticated workflows without manually managing session state.

**US-13** `[SR]` As a Security Researcher, I want to define conditional branching in a test sequence based on response content or status, so that I can probe different application code paths depending on how the target responds.

**US-14** `[PD]` As a Protocol Developer, I want to simulate a stateful protocol peer that responds based on what the application under test sends, so that I can validate my implementation against realistic, context-aware server behavior.

### Reporting & Output
**US-15** `[DE]` As a Domain Engineer, I want a summary view that surfaces actionable findings first with drill-down to technical detail, so that I can assess what needs attention without being confronted with raw protocol output as the default.

### MITM / Proxy
**US-16** `[DE]` As a Domain Engineer, I want to route my application's traffic through a transparent proxy so I can observe real protocol exchanges before writing any tests, so that I can discover what my application actually does rather than guessing at what to target.

**US-17** `[DE]` As a Domain Engineer, I want the tool to handle TLS certificate setup for local development automatically, so that Chrome and other clients can communicate through the proxy without manual certificate management or browser warnings.

**US-18** `[SR]` As a Security Researcher, I want to intercept live requests between a client and server, modify them in flight, and observe the application's response, so that I can probe behavior interactively before committing it to a scripted test sequence.

### Protocol Definition
**US-19** `[PD]` As a Protocol Developer, I want to define a protocol as a structured configuration — specifying data structures, field types, static and parameterized values, validation constraints, and formats — so that the tool can parse, analyze, generate, and validate messages for that protocol without requiring changes to the tool's core.

**US-20** `[PD]` As a Protocol Developer, I want to define a stateful interaction sequence as a flowchart with parameterized decision points and context extraction steps, so that the tool can automate multi-step protocol exchanges where each step depends on what the previous response contained.

**US-21** `[DE]` As a Domain Engineer, I want to load an existing protocol definition and immediately begin testing my application against it, so that I can benefit from contributed protocol knowledge without needing to understand the protocol internals first.

**US-22** `[SR]` As a Security Researcher, I want to define automated request and response transformations within a protocol definition, so that the proxy layer can modify in-flight traffic according to protocol-aware rules rather than raw byte offsets.

### Session Persistence
**US-23** `[DE]` As a Domain Engineer, I want to save my complete test session — configuration, active state, findings, and extracted context — as a portable artifact, so that I can resume it later or share it without losing progress or reconstructing it manually.

**US-24** `[DE]` As a Domain Engineer, I want the tool to identify and flag potentially sensitive values in my session before export — credentials, tokens, captured secrets — and require confirmation before including them, so that I don't inadvertently share confidential data.

**US-25** `[RTO]` As a Red Team Operator, I want to export a completed test session as a fully reproducible artifact, so that I can replay or adapt the sequence in a different environment without reconstructing it from memory.

### Provider / Source Abstraction
**US-26** `[SR]` As a Security Researcher, I want to configure a sequence step to use a generative data source — producing protocol-valid inputs automatically via mutation or grammar-based strategies — so that I can explore edge cases without manually crafting each payload.

**US-27** `[DE]` As a Domain Engineer, I want to swap the data source for a sequence step without rewriting the sequence definition, so that I can run the same test flow against captured traffic, generated inputs, or static fixtures interchangeably.

**US-28** `[PD]` As a Protocol Developer, I want to define a custom data provider that generates field values according to protocol-specific domain rules, so that generated test inputs respect the semantic constraints of the protocol and produce meaningful results rather than noise.

### State Machine Sequence Model
**US-29** `[PD]` As a Protocol Developer, I want to define protocol participants as state machines with named states, transitions, and triggering events, so that the tool can model and automate either side of a protocol exchange from a single definition.

**US-30** `[SR]` As a Security Researcher, I want to assign a sequence node to an initiator or responder role using a shared state machine definition, so that I can simulate either side of a protocol exchange without maintaining separate implementations for each.

**US-31** `[DE]` As a Domain Engineer, I want to run my application against a simulated counterpart whose behavior is driven by the same state machine model as a real peer, so that the simulation produces realistic, state-aware responses rather than static scripted ones.

### CLI / Pipeline Interface
**US-32** `[AP]` As an Automation Pipeline, I want the tool's CLI to emit structured output (JSON, exit codes) in addition to human-readable output, so that I can consume results programmatically without parsing formatted text.

---

## 4. Use Cases

Each use case is tagged with the user stories that motivate it.

| UC | Title | Stories |
|---|---|---|
| UC-01 | Initialize test session | US-01, US-06, US-21 |
| UC-02 | Render protocol buffer | US-03, US-04, US-05 |
| UC-03 | Load or define protocol definition | US-19, US-20, US-21 |
| UC-04 | Validate protocol definition against reference buffer | US-07, US-19 |
| UC-05 | Configure sequence node | US-06, US-07, US-14, US-29, US-30, US-31 |
| UC-06 | Configure data source (Provider/Source) | US-08, US-26, US-27, US-28 |
| UC-07 | Execute test sequence | US-09, US-10, US-11, US-12, US-13, US-14, US-31 |
| UC-08 | Extract context from protocol response | US-12, US-13 |
| UC-09 | Start proxy / MITM session | US-16, US-17, US-18, US-22 |
| UC-10 | Provision TLS for local development | US-17 |
| UC-11 | Intercept and transform in-flight traffic | US-18, US-22 |
| UC-12 | Save and serialize session | US-23, US-24, US-25 |
| UC-13 | Load saved session | US-23, US-25 |
| UC-14 | Generate test report | US-02, US-15, US-32 |
| UC-15 | Execute scripted test suite | US-09, US-10, US-11, US-32 |

*Full use case flows (nominal, alternate, preconditions, postconditions, exceptions) are in D2.*

---

## 5. Functional Requirements

**Priority key:** `[M]` Must — `[S]` Should — `[C]` Could
Each FR is tagged with the use case(s) it supports.

### 5.1 Session Management

**FR-001** `[M]` The tool shall assign a unique identifier to each session at initialization. *UC-01*

**FR-002** `[M]` The tool shall persist complete session state — configuration, sequence definitions, execution logs, context store references, and findings — to a serializable artifact on explicit user request. *UC-12*

**FR-003** `[S]` The tool shall persist session state at a configurable auto-save interval, applying the session's configured redaction policy silently. If no policy has been configured and the result would be 100% redacted, the tool shall prompt the user to configure a policy before completing the save. *UC-12*

**FR-003a** `[M]` The tool shall treat auto-save as a distinct operation from user-initiated export: auto-save applies the configured redaction policy silently; user-initiated export presents a confirmation summary of what will be included or redacted. *UC-12*

**FR-004** `[M]` The tool shall support three named redaction policies: *no-redactions* (export all values), *allowlist* (only explicitly permitted categories pass through), and *denylist* (all values pass through except explicitly denied categories). Policy is configured at session level and persisted in the session artifact. *UC-12*

**FR-005** `[M]` The tool shall store a redaction manifest alongside any artifact from which values were excluded, identifying the type and count of redacted entries without revealing redacted content. *UC-12*

**FR-006** `[M]` The tool shall restore a session fully — state, configuration, execution logs, and context store — from a valid session artifact. *UC-13*

**FR-007** `[S]` The tool shall migrate a session artifact from a prior schema version, reporting fields that could not be migrated and the fallback values applied. *UC-13*

**FR-008** `[M]` The tool shall note redacted value placeholders when loading a session artifact, and allow the user to supply replacement values interactively to restore full execution capability. *UC-13*

**FR-009** `[S]` The tool shall initialize a session in offline authoring mode when a specified target is unreachable, recording the connectivity failure in session state. *UC-01*

### 5.2 Protocol Definition

**FR-010** `[M]` The tool shall accept protocol definitions as structured configuration files specifying: data structures, field types, static and parameterized values, validation constraints, sequence definitions, rendering formats, and optional plain-language description metadata. *UC-03*

**FR-011** `[M]` The tool shall validate a protocol definition for structural integrity before registering it, reporting specific errors with field and line references. *UC-03*

**FR-012** `[M]` The tool shall support loading protocol definitions from local file paths. *UC-03*

**FR-013** `[S]` The tool shall support loading protocol definitions from a versioned registry, pinning the version reference to the session at load time. *UC-03*

**FR-014** `[M]` The tool shall register a protocol definition that contains structures but no sequences, marking sequence-dependent features as unavailable until sequences are defined. *UC-03*

**FR-015** `[M]` The tool shall detect and report circular field references in a protocol definition at load time, rejecting the definition. *UC-03*

**FR-016** `[M]` The tool shall detect and report ambiguous variable-length field definitions at load time, rejecting the definition. *UC-03*

**FR-017** `[M]` The tool shall validate a loaded protocol definition against a user-provided reference buffer, reporting: fields matched, values decoded, constraint violations, and unparsed bytes with offsets. *UC-04*

**FR-018** `[S]` The tool shall compare decoded field values against user-provided expected values during definition validation and report each mismatch with field name and offset. *UC-04*

**FR-067** `[S]` The tool shall accept an OpenAPI specification as a protocol definition input, deriving data structures, field types, parameter constraints, and endpoint patterns from the spec without requiring manual definition authoring. *UC-03*

**FR-068** `[S]` The tool shall use an imported OpenAPI specification as input to test discovery, suggesting test categories and sequence patterns derived from the spec's declared endpoints, parameters, schemas, and security schemes. *UC-01*

### 5.3 Protocol Buffer Rendering

**FR-019** `[M]` The tool shall render a protocol buffer in a high-level view showing field name, decoded value, and human-readable description for each parsed field. *UC-02*

**FR-020** `[M]` The tool shall render a protocol buffer in a low-level view showing a hex dump with field boundary markers and per-field annotations. *UC-02*

**FR-021** `[M]` The tool shall correlate field selection between high-level and low-level views, highlighting the corresponding byte region when a field is selected in either view. *UC-02*

**FR-022** `[M]` The tool shall render unparsed bytes in the low-level view with byte offset markers and an explicit "unknown" label when a full parse cannot be completed. *UC-02*

**FR-023** `[M]` The tool shall present all valid parse interpretations when a buffer is ambiguous under the loaded definition, and allow the user to select one. *UC-02*

**FR-024** `[M]` The tool shall render a raw hex dump with byte offset markers when no protocol definition is loaded, without requiring one. *UC-02*

### 5.4 Sequence Node Configuration

**FR-025** `[M]` The tool shall model protocol participants as state machines with named states, named transitions, triggering events, and configurable timeout values per state. *UC-05*

**FR-026** `[M]` The tool shall support assigning a sequence node to an initiator role or a responder role using the same state machine definition without requiring separate definitions for each role. *UC-05*

**FR-027** `[M]` The tool shall validate a sequence node configuration against the sequence definition's state machine contract before marking the node execution-ready. *UC-05*

**FR-028** `[M]` The tool shall detect and report incomplete state machines — missing transitions, undefined state references — during node configuration, saving the node in draft state rather than blocking the session. *UC-05*

**FR-029** `[M]` The tool shall detect and report circular state transitions during node configuration. *UC-05*

### 5.5 Data Source / Provider

**FR-030** `[M]` The tool shall implement a Provider/Source abstraction supporting the following source types as interchangeable implementations: captured replay, generative (mutation-based), generative (grammar-based), static fixture, and parameterized template. *UC-06*

**FR-031** `[M]` The tool shall allow a data source to be replaced on a sequence node or step without modifying the sequence definition, archiving the prior source configuration in the session. *UC-06*

**FR-032** `[M]` The tool shall validate a configured data source against the bound protocol definition's constraints before accepting the binding. *UC-06*

**FR-033** `[M]` The tool shall record source type and full configuration in the session artifact to enable reproduction of a test run. *UC-06*

**FR-034** `[S]` The tool shall support custom data source plugins via a defined interface, validating interface compliance before accepting the binding. *UC-06*

**FR-035** `[M]` The tool shall index a captured replay source by sequence step mapping at bind time, and flag frames that cannot be mapped to a sequence step. *UC-06*

**FR-036** `[S]` The tool shall verify that a generative source can produce at least one output satisfying protocol definition constraints before accepting the binding, reporting failure if it cannot. *UC-06*

### 5.6 Sequence Execution

**FR-037** `[M]` The tool shall execute a sequence by: sending messages from the bound data source per current state, capturing responses, parsing responses per protocol definition, evaluating transition conditions, and advancing state. *UC-07*

**FR-038** `[M]` The tool shall apply context extraction operations at defined sequence steps, storing extracted values exclusively in the session context store under named typed references. Raw values shall not appear in execution logs, task results, or any output outside the store. The store shall expose two access patterns: `value(key)` for use within sequence execution to construct protocol messages, and `ref(key)` for all other consumers (logs, results, reports, exports) which receive an opaque typed handle only. *UC-08*

**FR-039** `[M]` The tool shall resolve named context store references as parameters in subsequent sequence steps within the same session, passing opaque typed references through the orchestration layer and resolving to raw values only at the point of protocol message construction. *UC-08*

**FR-040** `[M]` The tool shall record every state transition in the execution log, including the transition condition matched and the branch path taken. *UC-07*

**FR-041** `[M]` The tool shall record response parse failures in the execution log and invoke the sequence's defined exception handler if present, otherwise halting the sequence. *UC-07*

**FR-042** `[M]` The tool shall record timeout events in the execution log and apply configured retry count or termination behavior. *UC-07*

**FR-043** `[M]` The tool shall associate every finding with its originating sequence step, state machine state, and parsed protocol context. *UC-07*

**FR-044** `[M]` The tool shall record context extraction failures with the source field reference and halt the sequence or follow the defined exception path. *UC-08*

**FR-045** `[S]` The tool shall support a configurable step limit that terminates a sequence without a natural terminal state after a defined number of transitions. *UC-07*

### 5.7 Proxy / MITM

**FR-046** `[M]` The tool shall operate as a local network proxy, capturing all traffic between a configured client and target for the duration of a proxy session. *UC-09*

**FR-047** `[M]` The tool shall parse captured proxy traffic using an applicable loaded protocol definition, and fall back to raw hex capture when no definition applies. *UC-09*

**FR-048** `[M]` The tool shall automate local TLS certificate provisioning, prompting for elevation only on first invocation, and requiring no re-setup in subsequent sessions. *UC-10*

**FR-049** `[M]` The tool shall detect whether a trusted local CA and valid certificate already exist and skip provisioning steps that are already satisfied. *UC-10*

**FR-050** `[M]` The tool shall output exact manual provisioning commands when elevation is denied, leaving the session in a pending-TLS state. *UC-10*

**FR-051** `[M]` The tool shall support protocol-aware transformation rules in interception mode, modifying named field values in in-flight messages according to protocol definition semantics. *UC-11*

**FR-052** `[M]` The tool shall persist both the original and modified versions of every intercepted exchange in the session log. *UC-11*

**FR-053** `[M]` The tool shall warn the user and require confirmation before forwarding a transformed message that fails protocol definition structural validation. *UC-11*

**FR-054** `[S]` The tool shall support a manual interception mode that pauses each exchange for user inspection and optional modification before forwarding. *UC-11*

**FR-055** `[S]` The tool shall support a drop rule in interception mode that discards a message, returns a connection reset to the originating side, and logs the event. *UC-11*

### 5.8 Reporting & Output

**FR-056** `[M]` The tool shall produce a test report that prioritizes findings by severity, with each finding stating: what was observed, why it is significant in application behavior terms, protocol context, and a reference to the raw evidence in the session log. *UC-14*

**FR-057** `[C]` The tool shall express finding significance in plain-language terms in addition to technical precision when plain-language descriptions are available in the protocol definition's content metadata. *UC-14*

**FR-057a** `[C]` During plugin/module onboarding, the tool shall use an LLM to generate plain-language descriptions for protocol elements and finding types that lack them, storing the generated content in the plugin's metadata for review and correction before use.

**FR-058** `[C]` The tool shall provide inline plain-language definitions for protocol elements and finding types when present in the plugin's content metadata. *UC-14*

**FR-059** `[M]` The tool shall emit structured JSON output for all reports alongside human-readable output. *UC-14, UC-15*

**FR-060** `[M]` The tool shall set exit code 0 when a report contains no findings, and a non-zero exit code when findings are present. *UC-14, UC-15*

**FR-061** `[M]` The tool shall include an execution coverage summary — sequences run, states reached, inputs exercised — in any report that contains no findings. *UC-14*

**FR-062** `[M]` The tool shall suppress human-readable output and emit JSON only when invoked in non-interactive mode. *UC-15*

**FR-063** `[M]` The tool shall accept a test suite definition file specifying: sequence list, source bindings, execution order, pass/fail criteria, and execution mode (serial or parallel). *UC-15*

**FR-064** `[M]` The tool shall merge results from all sequences in a suite into a single session artifact. *UC-15*

**FR-065** `[S]` The tool shall support parallel sequence execution within a suite, preserving sequence ordering in the log via timestamps. *UC-15*

**FR-066** `[M]` The tool shall support a fail-fast mode in suite execution that halts on the first sequence failure and records partial results. *UC-15*

**FR-069** `[S]` The tool's suite execution engine shall support parallel sequence execution, per-task retry with configurable limits, and timeout enforcement without requiring custom implementations of these primitives. *UC-15*

### 5.9 Structured Messaging Content Model

**FR-070** `[M]` All user-facing messages — errors, findings, status, and guidance — shall be structured as content objects with at minimum two levels: a summary level (concise, generalized, plain-language) and a detail level (technically precise, full context). The active verbosity level shall be configurable per session and per invocation. *UC-01, UC-14*

**FR-071** `[M]` Error messages shall be structured to include: what failed, in what context it failed, and what the user can do next — expressed at the configured verbosity level. No error shall produce only a raw exception or internal state dump as its user-facing output. *UC-01 through UC-15*

**FR-072** `[M]` The structured message content model shall be the single authoring target for all message types in the tool and its protocol plugins. Plugin-contributed messages shall conform to the same multi-level structure.

**FR-073** `[S]` The tool shall emit structured messages in machine-readable JSON format in non-interactive mode, preserving all levels of detail as distinct fields so that consumers can select the appropriate level programmatically. *UC-15, UC-14*

### 5.10 Tool Security Posture

**FR-074** `[M]` The tool shall encrypt sensitive values in the session context store at rest using a session-scoped key, such that the raw values are not recoverable from the session artifact without the key. *UC-12*

**FR-075** `[M]` The tool shall overwrite sensitive values held in memory in the context store when the session terminates or the value is explicitly released, and shall not retain them in process memory beyond their required lifetime. *UC-07, UC-08*

**FR-076** `[S]` The tool shall sign session artifacts to enable tamper detection on load, rejecting artifacts whose signatures do not match. *UC-13*

**FR-077** `[M]` The tool shall validate TLS certificates for all outbound connections it initiates — registry lookups, plugin downloads, update checks — and refuse connections with invalid or untrusted certificates.

**FR-078** `[S]` The tool shall execute custom plugin code in an isolated execution environment that prevents direct access to the session context store's internal value store, the host filesystem beyond a declared sandbox path, and the network beyond declared allowed endpoints. *UC-06 (FR-034)*

**FR-079** `[M]` The tool shall validate plugin interface compliance structurally before loading, and reject any plugin that attempts to register interfaces or hooks beyond those declared in its manifest. *UC-06 (FR-034)*

### FR Summary

| Area | Count | Must | Should | Could |
|---|---|---|---|---|
| Session Management | 9 | 7 | 2 | 0 |
| Protocol Definition | 11 | 7 | 4 | 0 |
| Buffer Rendering | 6 | 6 | 0 | 0 |
| Sequence Node Config | 5 | 5 | 0 | 0 |
| Data Source / Provider | 7 | 5 | 2 | 0 |
| Sequence Execution | 9 | 8 | 1 | 0 |
| Proxy / MITM | 10 | 7 | 3 | 0 |
| Reporting & Output | 13 | 9 | 1 | 3 |
| Structured Messaging | 4 | 3 | 1 | 0 |
| Tool Security Posture | 6 | 4 | 2 | 0 |
| **Total** | **80** | **61** | **16** | **3** |

---

## 6. Architectural Requirements

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

## 7. Constraints

### CON-01 — Implementation Language: Python 3.10+
**Decision:** Python is the sole implementation language for the core library and all first-party components. Plugins must also be Python (document as plugin authoring requirement).
**Rationale:** The entire selected OSS stack is Python-native — library-level integration rather than subprocess wrappers for all major components.
**Cost:** Not distributed as compiled binary; higher memory and startup time than Go/Rust.
**Tradeoff accepted:** Development velocity and OSS leverage vs. distribution simplicity and runtime performance.

### CON-02 — Deployment: Local Only, No Server Infrastructure
**Decision:** Operates entirely on the local machine. No server, database, or cloud dependency.
**Rationale:** CLI-first; works offline and in air-gapped environments; no auth or multi-tenancy complexity; session artifacts are user-controlled files.
**Cost:** No collaborative features without manual artifact transfer.
**Tradeoff accepted:** Simplicity, portability, and security vs. collaboration and remote orchestration.

### CON-03 — License Strategy: No GPL-Linked Dependencies
**Decision:** No GPL-licensed library imported as a direct dependency. GPL tools (Scapy, tshark/Wireshark) may be invoked as subprocesses only.
**Rationale:** Keeps licensing options open for MIT/Apache or commercial distribution.
**Cost:** Cannot import Scapy or libwireshark directly; tshark subprocess loses real-time streaming.
**Tradeoff accepted:** Licensing flexibility vs. access to the richest binary protocol dissection library.

### CON-04 — Protocol Scope: Pluggable, Protocol-Agnostic Core
**Decision:** The core tool has no built-in knowledge of any specific protocol. All protocol behavior is provided via plugins loaded at runtime.
**Rationale:** Enables gradual onboarding of protocols, community contribution, and extensibility. HTTP/REST seed plugin validates the model before the API is published.
**Cost:** Higher architectural scaffolding; first working test requires loading a protocol definition.
**Tradeoff accepted:** Long-term scalability vs. short-term time-to-first-test. *Mitigated: HTTP/REST seed plugin ships bundled.*

### CON-05 — Plugin Interface v1 Publication Timing
**Decision:** Plugin interface v1 is not published as a public contract until the HTTP/REST seed plugin has been implemented internally and has validated the contract under real conditions.
**Rationale:** Premature commitment requiring a breaking change damages ecosystem trust.
**Cost:** Community cannot build third-party plugins until v1 is published.
**Tradeoff accepted:** API stability vs. ecosystem growth speed.
*Resolves: FR-030 (Must — ships with seed plugin) vs FR-034 (Should — ships when v1 is published).*

### CON-06 — Context Store as the Single Redaction Enforcement Point
**Decision:** Sensitive values stored exclusively in C-02 (Context Store). All other components receive opaque typed references. Raw value resolution happens only within C-07 (Sequence Engine) at message construction time.
**Rationale:** Structural security property — leakage is architecturally impossible rather than relying on per-integration discipline.
**Cost:** Indirection overhead on every sensitive value access; two access patterns (`value()` vs `ref()`) must be understood.
**Tradeoff accepted:** Security property strength vs. implementation simplicity.

### CON-07 — Prefect Result Persistence: Disabled
**Decision:** All Prefect tasks in C-09 (Suite Orchestrator) configured with `persist_result=False`.
**Rationale:** Belt-and-suspenders with CON-06. Even if a raw value were accidentally passed as a task argument, Prefect would not persist it.
**Cost:** Prefect's result inspection and replay features unavailable.
**Tradeoff accepted:** Defense in depth vs. orchestration observability. *Session log (C-10) provides full observability.*

### CON-08 — UI Layer Deferred; C-13 Is the Boundary
**Decision:** No interactive UI (TUI or local web UI) built until the core library is stable. C-13 (Library API) is the sole boundary — any UI is a new consumer of C-13, not a modification of anything below it.
**Rationale:** Building UI before library API stabilizes risks coupling UI to implementation details that will change.
**Known gap:** FR-021 and FR-023 (interactive field selection in visualization) require richer UI than CLI provides. Resolved when UI ships.
**Tradeoff accepted:** Architectural cleanliness vs. earlier delivery of rich interactive experience.

### CON-09 — HTTP/REST as the First Protocol
**Decision:** HTTP/REST plugin is the first and only bundled protocol. Binary protocol support deferred until after plugin model validates.
**Rationale:** OSS landscape is overwhelmingly HTTP-oriented; maximizes leverage; addresses S-01 through S-07.
**Cost:** Binary protocol testing, raw TCP, WebSocket beyond HTTP upgrade, and gRPC not available in v1.
**Tradeoff accepted:** Time-to-value for primary use case vs. breadth of protocol coverage. *WebSocket and gRPC addable as plugins without core changes.*

---

## 8. Component Model

### 8.1 Component Inventory

| ID | Component | Primary Responsibility | Covers (FRs) |
|---|---|---|---|
| C-01 | Message Registry | URN-to-IMessage template mapping; param schema validation; resolution at boundary layer only | FR-070, FR-071, FR-072, FR-073 |
| C-02 | Context Store | Typed reference store; redaction enforcement; sensitive value lifecycle | FR-004, FR-038, FR-039, FR-074, FR-075 |
| C-03 | Protocol Definition Engine | Parse, validate, build protocol messages; binary and REST backends | FR-010, FR-011, FR-015, FR-016, FR-017, FR-018, FR-023, FR-067 |
| C-04 | Protocol Registry | Catalog of loaded definitions; versioning; discovery suggestions | FR-012, FR-013, FR-014, FR-068 |
| C-05 | Provider/Source Framework | ISource abstraction + built-in implementations; plugin seam | FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036 |
| C-06 | Buffer Renderer | Dual-view rendering; tshark dissection; field correlation | FR-019, FR-020, FR-021, FR-022, FR-024 |
| C-07 | Sequence Engine | State machine execution; step advancement; context extraction; log production | FR-025–FR-029, FR-037–FR-045 |
| C-08 | Proxy Engine | mitmproxy integration; TLS provisioning; traffic capture; interception rules | FR-046–FR-055 |
| C-09 | Suite Orchestrator | Prefect-based suite execution; parallel/serial; pass/fail; result aggregation | FR-063, FR-064, FR-065, FR-066, FR-069 |
| C-10 | Session Manager | Session lifecycle; artifact serialization/migration; key management; log recording | FR-001–FR-009, FR-074, FR-075, FR-076 |
| C-11 | Report Generator | Finding aggregation; severity prioritization; multi-level output; JSON emission | FR-056, FR-057, FR-057a, FR-058, FR-059, FR-061 |
| C-12 | Plugin Manager | Plugin loading; manifest validation; sandboxing; content onboarding | FR-034, FR-072, FR-078, FR-079 |
| C-13 | Library API | Public surface; execution log handoff; non-interactive mode detection | FR-009, FR-060, FR-062 |
| C-14 | CLI Layer | Argument parsing; command routing; output formatting; exit codes | FR-060, FR-062, FR-073 |
| U-01 | NetworkClient (utility) | Shared outbound HTTP/S client with enforced TLS validation | FR-077 |

### 8.2 Shared Data Types

##### MessageRef
```
MessageRef
  urn:        str             # e.g. "urn:badbot:c07:context_extraction_failed"
  params:     dict            # typed parameters consumed by the template at render time
  schema_ref: URNSchemaRef?   # optional — when present, params validated against registered schema at build/test time
```
Emitted by all core components (C-02 through C-10) in place of constructed IMessage objects. Resolved to IMessage only at the boundary layer (C-11, C-13, C-14) via `C-01.resolve()`. Zero-dependency primitive — no C-01 import required to produce one.

**URN schema validation:** When `schema_ref` is present, the registered URN schema defines the expected param keys and types. Validation can be run at build or test time against the registry to catch param contract violations before runtime. Schemas are registered by core components at initialization and by plugins during onboarding via C-12.

### Finding
```
Finding
  id:               UUID
  severity:         Severity   # CRITICAL | HIGH | MEDIUM | LOW | INFO
  message:          MessageRef # resolved to IMessage at render time by C-11 or C-13
  sequence_step:    StepRef
  state:            StateName
  protocol_context: ParseResult
  evidence_ref:     ContextRef # opaque reference — raw value stays in C-02
  timestamp:        datetime
```
*Produced by C-07 and C-08. Consumed by C-11 and C-10.*

#### LogEntry
```
LogEntry
  id:          UUID
  timestamp:   datetime
  kind:        LogKind     # TRANSITION | PARSE_FAILURE | TIMEOUT | EXTRACTION | EXCHANGE | FINDING
  message:     MessageRef  # resolved to IMessage at render time
  context_ref: ContextRef? # optional reference to associated context value
  step_ref:    StepRef?
  state:       StateName?
```
*Produced by C-07 and C-08. Written to session via `C-10.record()`.*

#### ExecutionResult
```
ExecutionResult
  sequence_id:  UUID
  status:       ExecutionStatus  # COMPLETED | HALTED | FAILED | TIMEOUT
  log_entries:  List[LogEntry]
  findings:     List[Finding]
  coverage:     CoverageSummary  # states reached, steps executed, inputs exercised
```
*Returned by C-07. Caller (C-09 or C-13) writes log entries and findings to C-10.*

### 8.3 Interfaces

#### C-01 — IMessageRegistry
```
register(urn: str, template: MessageTemplate, schema?: URNSchema)
resolve(ref: MessageRef) → IMessage
render(ref: MessageRef, verbosity: Verbosity) → str
validate(ref: MessageRef) → ValidationResult   # checks params against schema if registered
```
**IMessage** (rendered output type — consumed only at C-11, C-13, C-14):
```
summary:    str    # plain-language, always present
detail:     str    # technically precise, always present
structured: dict   # machine-readable fields
render(verbosity: Verbosity) → str
```
Core components (C-02 through C-10) emit `MessageRef` primitives — they do not import or depend on C-01. C-01 is a dependency only of the boundary layer: C-11 (resolves at report generation), C-12 (registers URN schemas during plugin onboarding), C-13 (resolves for library consumers), and C-14 (renders for CLI). No component emits raw strings to the user.

#### C-02 — IContextStore
```
store(key, value, type: SensitiveType) → ContextRef
value(ref: ContextRef) → RawValue        # RESTRICTED — C-07 only; type error for all other callers
ref(key) → ContextRef                    # opaque handle for all other consumers
release(ref: ContextRef)                 # overwrites value in memory
release_all()                            # called by C-10.close() on session termination
apply_redaction(policy: RedactionPolicy) → RedactedExport
encrypt_at_rest(key: SessionKey) → EncryptedStore
```
`value()` is enforced at the component boundary — callers outside C-07 receive a type error at call time, not at runtime.

#### C-03 — IProtocolDefinition
```
parse(buffer: bytes) → ParseResult
parse_all(buffer: bytes) → List[ParseResult]   # for ambiguous buffers; FR-023
build(fields: FieldMap) → bytes
validate(buffer: bytes, expected?: FieldMap) → ValidationResult
sequences() → List[SequenceDefinition]
schema() → ProtocolSchema
```
`parse_all()` returns all structurally valid interpretations when the buffer is ambiguous. C-06 presents alternatives to the user when `len(parse_all()) > 1`.

#### C-04 — IProtocolRegistry
```
load(source: FilePath | RegistryID) → IProtocolDefinition
register(definition: IProtocolDefinition)
lookup(hint: TargetHint) → List[IProtocolDefinition]
versions(name) → List[VersionRef]
```
Outbound registry calls route through U-01 (NetworkClient) for TLS enforcement.

#### C-05 — ISource
```
next() → bytes | FieldMap
reset()
is_exhausted() → bool
bind(definition: IProtocolDefinition)
validate_against(definition: IProtocolDefinition) → ValidationResult
config() → SourceConfig                  # serializable; stored in session by C-10
```

#### C-06 — IBufferRenderer
```
render(buffer: bytes, definition?: IProtocolDefinition) → RenderResult
correlate(field: FieldRef) → ByteRange
```
`RenderResult` contains both high-level and low-level views plus the correlation map. When `C-03.parse_all()` returns multiple results, `render()` includes all interpretations and the caller presents a selection prompt (satisfies FR-023 jointly with C-03).

#### C-07 — ISequenceEngine
```
configure(node: SequenceNodeConfig) → SequenceNode
execute(node: SequenceNode, context: IContextStore) → ExecutionResult
```
`SequenceNode` encapsulates: role (INITIATOR | RESPONDER), state machine instance, bound source, protocol definition. `ExecutionResult` contains `List[LogEntry]` and `List[Finding]` — callers (C-09 or C-13) write these to C-10 via `record()`. C-07 never writes to C-10 directly (no dependency).

#### C-08 — IProxyEngine
```
start(config: ProxyConfig) → ProxySession
stop(session: ProxySession) → List[LogEntry]   # returns captured exchanges as log entries
add_rule(session: ProxySession, rule: InterceptionRule)
provision_tls(hostnames: List[str]) → CertificateBundle
```
`stop()` returns all captured and intercepted exchanges as `LogEntry` objects. The caller (C-13) writes these to C-10 via `record()`. C-08 does not depend on C-10 directly.

#### C-09 — ISuiteOrchestrator
```
run(suite: SuiteDefinition, session: Session) → SuiteResult
```
`SuiteDefinition` specifies sequences, sources, order, pass/fail criteria, execution mode. After each sequence execution, C-09 calls `C-10.record()` with the `ExecutionResult` log entries and findings. Prefect flows are an internal implementation detail — not exposed at this interface.

#### C-10 — ISessionManager
```
create(config: SessionConfig) → Session
close(session: Session)                                    # triggers C-02.release_all(); FR-075
save(session: Session, policy: RedactionPolicy) → ArtifactPath
load(path: ArtifactPath) → Session
migrate(artifact: Artifact) → MigrationResult
record(session: Session, entry: LogEntry | ExecutionResult) # FR-040–044, FR-052
fill_placeholder(session: Session, key: str, value: Any)   # FR-008
generate_key(session: Session) → SessionKey                # FR-074; called at create()
signing_key(session: Session) → SigningKey                 # FR-076
```
`generate_key()` is called internally during `create()` — the session key is passed to `C-02.encrypt_at_rest()` at session initialization. `close()` calls `C-02.release_all()` to satisfy FR-075.

#### C-11 — IReportGenerator
```
generate(session: Session) → Report
```
`Report` contains `List[Finding]`, each with a `MessageRef` resolved to `IMessage` via `C-01.resolve()` at report generation time. C-11 is one of the four boundary-layer consumers of C-01. C-11 reads findings from the session log — it never calls `C-02.value()`.

#### C-12 — IPluginManager
```
load(path: PluginPath) → Plugin
validate(plugin: Plugin) → ValidationResult
onboard(plugin: Plugin) → OnboardedPlugin    # triggers LLM description generation; FR-057a
                                              # registers plugin URN schemas with C-01
sandbox(plugin: Plugin) → SandboxedPlugin
```
C-12 depends on C-01 for URN schema registration during `onboard()` — a write-only dependency (registration only; C-12 never calls `resolve()` or `render()`). Outbound plugin download calls route through U-01 (NetworkClient) for TLS enforcement (FR-077).

#### C-13 — ILibraryAPI
```
new_session(target, config?) → SessionHandle
load_session(path) → SessionHandle
run_suite(handle, suite_path) → SuiteResult
start_proxy(handle, config) → ProxyHandle
stop_proxy(handle, proxy_handle)             # calls C-08.stop(); writes log entries to C-10
render_buffer(handle, buffer) → RenderResult
generate_report(handle) → Report
save_session(handle, policy?) → ArtifactPath
close_session(handle)                        # calls C-10.close()
load_protocol(handle, source) → DefinitionRef
```
C-13 is the execution log handoff coordinator for non-suite paths: after `C-07.execute()` returns `ExecutionResult`, C-13 calls `C-10.record()`. After `C-08.stop()` returns captured exchanges, C-13 calls `C-10.record()`. Exit codes (FR-060) and non-interactive mode (FR-062) are determined at C-13/C-14 boundary.

#### C-14 — CLI Layer
Thin shell over C-13. Responsible for: argument parsing, command routing, exit code emission, suppressing human-readable output in non-interactive mode, and rendering structured JSON messages in pipeline mode.

#### U-01 — NetworkClient (Shared Utility)
```
get(url, headers?) → Response
post(url, body, headers?) → Response
```
All outbound HTTP/S calls from C-04 (registry lookups) and C-12 (plugin downloads) route through this utility. TLS certificate validation is enforced unconditionally — connections with invalid or untrusted certificates are refused and raise a typed error.

### 8.4 Dependency Graph

```
C-14 CLI Layer
  └→ C-13 Library API
        ├→ C-01 Message Registry          ← resolve/render; boundary layer only
        ├→ C-10 Session Manager
        │     └→ C-02 Context Store
        ├→ C-04 Protocol Registry
        │     ├→ C-03 Protocol Definition Engine
        │     │     ├→ [Construct OSS]
        │     │     └→ [OpenAPI parsers OSS]
        │     ├→ C-12 Plugin Manager
        │     │     ├→ C-01 Message Registry   ← register URN schemas at onboarding only
        │     │     └→ [U-01 NetworkClient]
        │     └→ [U-01 NetworkClient]
        ├→ C-06 Buffer Renderer
        │     ├→ C-03 Protocol Definition Engine
        │     └→ [tshark subprocess]
        ├→ C-07 Sequence Engine
        │     ├→ C-03 Protocol Definition Engine
        │     ├→ C-05 Provider/Source Framework
        │     │     ├→ C-03 Protocol Definition Engine
        │     │     ├→ [Boofuzz primitives OSS]
        │     │     └→ [Hypothesis OSS]
        │     ├→ C-02 Context Store
        │     └→ [transitions OSS]
        ├→ C-08 Proxy Engine
        │     ├→ C-03 Protocol Definition Engine
        │     ├→ C-06 Buffer Renderer
        │     ├→ C-07 Sequence Engine
        │     ├→ C-02 Context Store
        │     ├→ [mitmproxy OSS]
        │     └→ [mkcert subprocess]
        ├→ C-09 Suite Orchestrator
        │     ├→ C-07 Sequence Engine
        │     ├→ C-10 Session Manager
        │     └→ [Prefect OSS]
        └→ C-11 Report Generator
              ├→ C-01 Message Registry   ← resolves MessageRefs to IMessage at report time
              ├→ C-10 Session Manager
              └→ C-02 Context Store      (refs only — never calls value())
```

No circular dependencies. C-02 is the infrastructure foundation. C-01 (Message Registry) is a boundary-layer dependency only — core components C-02 through C-10 emit `MessageRef` primitives and carry no C-01 import. C-01 is resolved at C-11 (report generation), C-12 (URN schema registration during plugin onboarding), C-13 (library boundary), and C-14 (CLI rendering). U-01 (NetworkClient) is a leaf with no internal dependencies. Core library (C-01 through C-12, U-01) has no import dependency on C-13 or C-14 — satisfies AR-010.

**Execution log write path:** C-07 and C-08 return log entries and findings in their return types. C-09 and C-13 write these to C-10 via `record()`. Neither C-07 nor C-08 depends on C-10 directly.

---

## 9. OSS Integration Plan

| OSS Candidate | Component | Mode | License | Covers (FRs) |
|---|---|---|---|---|
| Construct | C-03 | Library import | MIT | FR-010, FR-011, FR-015, FR-016 |
| OpenAPI parsers (prance/openapi-core) | C-03 | Library import | MIT/Apache | FR-067, FR-068, FR-010 |
| transitions | C-07 | Library import | MIT | FR-025–FR-029 |
| mitmproxy | C-08 | Library import | MIT | FR-046, FR-047, FR-051, FR-054, FR-055 |
| Boofuzz primitives | C-05 | Library import | MIT | FR-030, FR-035, FR-036 |
| Hypothesis | C-05 | Library import | MPL-2.0 | FR-030, FR-036 |
| Prefect v3 (local mode) | C-09 | Library import | Apache 2.0 | FR-063, FR-065, FR-066, FR-069 |
| tshark | C-06 | Subprocess | GPL-2.0 (subprocess safe) | FR-019, FR-020, FR-021, FR-047 |
| mkcert | C-08 | Subprocess | MIT | FR-048, FR-049, FR-050 |
| jwt-tool | C-05 | Plugin (first-party) | MIT | FR-030, FR-051 |
| CORScanner | C-05 | Plugin (first-party) | MIT | FR-030, FR-046 |
| Arjun | C-04 | Subprocess (discovery) | MIT | FR-068 |
| Dredd | C-03 | Subprocess (optional) | Apache 2.0 | FR-017, FR-018 |

**License summary:** No GPL-linked dependencies. All library imports are MIT, Apache 2.0, or MPL-2.0. tshark and Scapy invoked as subprocess only — no copyleft obligation triggered.

**Not integrated (reference only):** RESTler (dependency-chaining approach adopted; .NET language boundary prohibits integration), Scapy (GPL), libwireshark (GPL), OWASP ZAP (Java/architectural mismatch), AFL++ (deferred — requires instrumented targets).

---

## 10. Plugin API Surface

A plugin is a package implementing any combination of:

```
PluginManifest
  name, version, author
  implements: [protocol_definition, source, message_registry]
  capabilities:
    filesystem: [declared sandbox paths]
    network: [declared allowed endpoints]

IPluginProtocolDefinition  →  implements IProtocolDefinition (C-03)
IPluginSource              →  implements ISource (C-05)
IPluginMessageRegistry     →  contributes URN schemas and MessageTemplate definitions
                               for finding types, protocol elements, and error conditions;
                               registered with C-01 during onboarding via C-12
```

A plugin cannot:
- Call `IContextStore.value()` directly
- Register hooks outside declared manifest capabilities
- Access other plugins' state

**Plugin authoring requirement:** Plugins must be Python (CON-01). This is a documented constraint for plugin authors, not a runtime enforcement gap.

**Versioning commitment:** Plugin interface v1 published only after HTTP/REST seed plugin validates the contract internally (CON-05). Minor versions may add; patch versions may fix; major versions may break with migration path; minimum two-major-version support window (AR-012).

### First Protocol: HTTP/REST Plugin (Seed)

Ships bundled. Validates the plugin model before the public API is committed.

- `IPluginProtocolDefinition` — HTTP/HTTPS structures; OpenAPI import pipeline
- `IPluginSource` implementations — JWT mutation (jwt-tool), CORS check (CORScanner), HTTP replay
- `IPluginMessageRegistry` — structured messages for all HTTP-specific findings
- Sequence definitions covering: S-01 (auth token lifecycle), S-02 (BOLA/IDOR), S-03 (input fuzzing), S-04 (excessive data exposure), S-05 (mass assignment), S-06 (rate limiting), S-07 (CORS misconfiguration), S-08 (multi-step workflow bypass)

---

## 11. Traceability Matrix

Full chain: User Story → Use Case → Functional Requirements → Component(s)

| Story | Use Case | FRs | Component(s) |
|---|---|---|---|
| US-01 | UC-01 | FR-001, FR-068 | C-10, C-04 |
| US-02 | UC-14 | FR-056, FR-057, FR-058, FR-070 | C-11, C-01 |
| US-03 | UC-02 | FR-019, FR-020, FR-021, FR-070 | C-06, C-01 |
| US-04 | UC-02 | FR-020, FR-022, FR-024 | C-06 |
| US-05 | UC-02 | FR-021, FR-023 | C-06, C-03 |
| US-06 | UC-01, UC-05 | FR-001, FR-025, FR-026, FR-027 | C-10, C-07 |
| US-07 | UC-04, UC-05 | FR-017, FR-027, FR-028, FR-029 | C-03, C-07 |
| US-08 | UC-06 | FR-030, FR-031, FR-035 | C-05 |
| US-09 | UC-15 | FR-063, FR-064, FR-065, FR-066 | C-09, C-10 |
| US-10 | UC-07, UC-15 | FR-037, FR-040, FR-045, FR-063 | C-07, C-09 |
| US-11 | UC-15 | FR-059, FR-060, FR-062, FR-063 | C-09, C-13, C-14 |
| US-12 | UC-07, UC-08 | FR-037, FR-038, FR-039, FR-044 | C-07, C-02 |
| US-13 | UC-07, UC-08 | FR-037, FR-038, FR-040 | C-07, C-02 |
| US-14 | UC-05, UC-07 | FR-025, FR-026, FR-037 | C-07 |
| US-15 | UC-14 | FR-056, FR-061, FR-070, FR-071 | C-11, C-01 |
| US-16 | UC-09 | FR-046, FR-047 | C-08 |
| US-17 | UC-09, UC-10 | FR-048, FR-049, FR-050 | C-08 |
| US-18 | UC-09, UC-11 | FR-051, FR-052, FR-053, FR-054 | C-08 |
| US-19 | UC-03, UC-04 | FR-010, FR-011, FR-015, FR-016, FR-017 | C-03, C-04 |
| US-20 | UC-03 | FR-010, FR-025 | C-03, C-07 |
| US-21 | UC-01, UC-03 | FR-012, FR-013, FR-014 | C-04 |
| US-22 | UC-11 | FR-051, FR-052, FR-053 | C-08 |
| US-23 | UC-12, UC-13 | FR-002, FR-006, FR-033 | C-10 |
| US-24 | UC-12 | FR-003, FR-004, FR-005, FR-074 | C-10, C-02 |
| US-25 | UC-12, UC-13 | FR-002, FR-006, FR-033 | C-10, C-05 |
| US-26 | UC-06 | FR-030, FR-036 | C-05 |
| US-27 | UC-06 | FR-031, FR-032 | C-05 |
| US-28 | UC-06 | FR-028, FR-030, FR-034 | C-05, C-12 |
| US-29 | UC-05 | FR-025, FR-026, FR-027, FR-028, FR-029 | C-07 |
| US-30 | UC-05 | FR-026, FR-027 | C-07 |
| US-31 | UC-05, UC-07 | FR-026, FR-037 | C-07 |
| US-32 | UC-15 | FR-059, FR-060, FR-062, FR-073 | C-13, C-14 |

---

## 12. Scope Boundaries

### Explicitly In Scope (v1)
- HTTP/REST protocol testing via bundled seed plugin
- Local proxy / MITM via mitmproxy with automatic TLS provisioning
- Sequence-based test execution with FSM model and context extraction
- Suite execution (serial and parallel) via Prefect
- Session persistence with three-mode redaction policy
- CLI interface with JSON output and exit codes
- Plugin architecture (internal validation via seed plugin; public v1 deferred)
- Structured multi-level messaging throughout

### Explicitly Out of Scope (v1) — With Architectural Path to Add
| Item | Deferred Until | Addition Path |
|---|---|---|
| Binary protocol testing | After plugin model validates | New `IPluginProtocolDefinition` — no core changes |
| WebSocket beyond HTTP upgrade | After plugin model validates | New plugin |
| gRPC | After plugin model validates | New plugin |
| Interactive TUI or web UI | After HTTP/REST seed plugin ships | New consumer of C-13 — no core changes |
| Plugin interface v1 public commitment | After seed plugin validates contract | Publish semver-committed API |
| Third-party plugin ecosystem | After v1 published | Community authors against published API |
| Coverage-guided fuzzing (AFL++) | Scope extension — requires instrumented targets | New `ISource` implementation |
| Collaborative session sharing | Future version | Artifact transfer already works; multi-user tooling is separate |
| Remote execution | Future version | Violates CON-02; requires separate product consideration |

---

## 13. Resolved Open Items

| Source | Item | Resolution |
|---|---|---|
| D3 | FR-030 (Must) vs FR-034 (Should) — plugin interface timing | CON-05: FR-030 ships with seed plugin; FR-034 ships when v1 published |
| D3 | Redaction policy model — how aggressive? | Default-redact; 100% trigger prompts user to configure policy; three named modes |
| D3 | Plain-language descriptions — runtime LLM or static? | Static, precision-first at runtime; LLM generates at plugin onboarding (FR-057a, Could) |
| D5 | FR-077 (outbound TLS) had no component owner | Added U-01 NetworkClient utility; C-04 and C-12 route through it |
| D5 | C-03 parse() — singular result for ambiguous buffers | Added `parse_all()` returning `List[ParseResult]`; C-06 presents alternatives |
| D5 | Execution log write path — C-07 no dependency on C-10 | C-07 returns LogEntry list in ExecutionResult; C-09/C-13 call `C-10.record()` |
| D5 | Finding data model undefined | Defined `Finding` as named shared type with MessageRef, ContextRef, severity, etc. |
| D5 | C-01 as cross-cutting dependency | Introduced `MessageRef` primitive; C-01 becomes Message Registry; core components emit MessageRef, resolve only at boundary (C-11, C-12, C-13, C-14) |
| D6 | CON-08 — interactive UI limitation for DE | Known gap explicitly accepted; CLI serves v1; UI ships after seed plugin |

---

## 14. Deferred Decisions

| Decision | Deferred Until | Notes |
|---|---|---|
| Plugin interface v1 public commitment | After HTTP/REST seed plugin validates contract internally | AR-012 governs versioning when published |
| Interactive UI technology choice (TUI vs local web) | After core library stabilizes | C-13 Library API is the defined boundary; no internal changes needed |
| Binary protocol test scenario catalog | After plugin model proves out with HTTP/REST | S-09+ scenarios analogous to D4's S-01 through S-08 |
| CON-01 documentation for plugin authors | Plugin authoring docs | Plugins must be Python; document as plugin authoring requirement |
| Governance and observability framework | Post-v1 process review | User intent: distill process wins/misses from this project into a reusable framework |

---

## 15. Document Traceability Index

| Deliverable | File | Content |
|---|---|---|
| D1 — User Stories | `specs/D1-user-stories.md` | 32 stories, 5 personas, primary persona detail |
| D2 — Use Cases | `specs/D2-use-cases.md` | 15 use cases with full flows |
| D3 — Functional Requirements | `specs/D3-functional-requirements.md` | 80 FRs across 10 areas |
| D4 — OSS Landscape | `specs/D4-oss-landscape.md` | 8 test scenarios, OSS verdict matrix, license risk summary |
| D5 — Modularization | `specs/D5-modularization.md` | 14 components + U-01, interfaces, dependency graph, gap resolution record |
| D6 — Architectural Requirements | `specs/D6-architectural-requirements.md` | 13 ARs, 9 constraints with rationale/cost/tradeoff |
| D7 — Master Spec (this document) | `specs/D7-master-spec.md` | Authoritative synthesis; no dangling references |

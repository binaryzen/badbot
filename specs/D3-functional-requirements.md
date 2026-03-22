# D3 — Functional Requirements

**Priority key:** `[M]` Must — `[S]` Should — `[C]` Could

## Amendments Applied
- FR-003/FR-004: Updated for redaction policy model (default-redact, 3 modes, 100% trigger)
- FR-003a: Added — distinguishes auto-save from user-initiated export
- FR-057/FR-058: Downgraded from M/S to C — plain-language as plugin content, not runtime rendering
- FR-057a: Added — LLM-generated plain-language descriptions at plugin onboarding
- FR-067/FR-068: Added — OpenAPI spec ingestion
- FR-069: Added — suite orchestration primitives
- FR-038/FR-039: Updated to reflect typed context store reference model
- FR-070–FR-073: Added — structured messaging content model
- FR-074–FR-079: Added — tool security posture

---

## Session Management

**FR-001** `[M]` The tool shall assign a unique identifier to each session at initialization.
*UC-01*

**FR-002** `[M]` The tool shall persist complete session state — configuration, sequence definitions, execution logs, context store references, and findings — to a serializable artifact on explicit user request.
*UC-12*

**FR-003** `[S]` The tool shall persist session state at a configurable auto-save interval, applying the session's configured redaction policy silently. If no policy has been configured and the result would be 100% redacted, the tool shall prompt the user to configure a policy before completing the save.
*UC-12*

**FR-003a** `[M]` The tool shall treat auto-save as a distinct operation from user-initiated export: auto-save applies the configured redaction policy silently; user-initiated export presents a confirmation summary of what will be included or redacted.
*UC-12*

**FR-004** `[M]` The tool shall support three named redaction policies: *no-redactions* (export all values), *allowlist* (only explicitly permitted categories pass through), and *denylist* (all values pass through except explicitly denied categories). Policy is configured at session level and persisted in the session artifact.
*UC-12*

**FR-005** `[M]` The tool shall store a redaction manifest alongside any artifact from which values were excluded, identifying the type and count of redacted entries without revealing redacted content.
*UC-12*

**FR-006** `[M]` The tool shall restore a session fully — state, configuration, execution logs, and context store — from a valid session artifact.
*UC-13*

**FR-007** `[S]` The tool shall migrate a session artifact from a prior schema version, reporting fields that could not be migrated and the fallback values applied.
*UC-13*

**FR-008** `[M]` The tool shall note redacted value placeholders when loading a session artifact, and allow the user to supply replacement values interactively to restore full execution capability.
*UC-13*

**FR-009** `[S]` The tool shall initialize a session in offline authoring mode when a specified target is unreachable, recording the connectivity failure in session state.
*UC-01*

---

## Protocol Definition

**FR-010** `[M]` The tool shall accept protocol definitions as structured configuration files specifying: data structures, field types, static and parameterized values, validation constraints, sequence definitions, rendering formats, and optional plain-language description metadata.
*UC-03*

**FR-011** `[M]` The tool shall validate a protocol definition for structural integrity before registering it, reporting specific errors with field and line references.
*UC-03*

**FR-012** `[M]` The tool shall support loading protocol definitions from local file paths.
*UC-03*

**FR-013** `[S]` The tool shall support loading protocol definitions from a versioned registry, pinning the version reference to the session at load time.
*UC-03*

**FR-014** `[M]` The tool shall register a protocol definition that contains structures but no sequences, marking sequence-dependent features as unavailable until sequences are defined.
*UC-03*

**FR-015** `[M]` The tool shall detect and report circular field references in a protocol definition at load time, rejecting the definition.
*UC-03*

**FR-016** `[M]` The tool shall detect and report ambiguous variable-length field definitions at load time, rejecting the definition.
*UC-03*

**FR-017** `[M]` The tool shall validate a loaded protocol definition against a user-provided reference buffer, reporting: fields matched, values decoded, constraint violations, and unparsed bytes with offsets.
*UC-04*

**FR-018** `[S]` The tool shall compare decoded field values against user-provided expected values during definition validation and report each mismatch with field name and offset.
*UC-04*

**FR-067** `[S]` The tool shall accept an OpenAPI specification as a protocol definition input, deriving data structures, field types, parameter constraints, and endpoint patterns from the spec without requiring manual definition authoring.
*UC-03*

**FR-068** `[S]` The tool shall use an imported OpenAPI specification as input to test discovery, suggesting test categories and sequence patterns derived from the spec's declared endpoints, parameters, schemas, and security schemes.
*UC-01*

---

## Protocol Buffer Rendering

**FR-019** `[M]` The tool shall render a protocol buffer in a high-level view showing field name, decoded value, and human-readable description for each parsed field.
*UC-02*

**FR-020** `[M]` The tool shall render a protocol buffer in a low-level view showing a hex dump with field boundary markers and per-field annotations.
*UC-02*

**FR-021** `[M]` The tool shall correlate field selection between high-level and low-level views, highlighting the corresponding byte region when a field is selected in either view.
*UC-02*

**FR-022** `[M]` The tool shall render unparsed bytes in the low-level view with byte offset markers and an explicit "unknown" label when a full parse cannot be completed.
*UC-02*

**FR-023** `[M]` The tool shall present all valid parse interpretations when a buffer is ambiguous under the loaded definition, and allow the user to select one.
*UC-02*

**FR-024** `[M]` The tool shall render a raw hex dump with byte offset markers when no protocol definition is loaded, without requiring one.
*UC-02*

---

## Sequence Node Configuration

**FR-025** `[M]` The tool shall model protocol participants as state machines with named states, named transitions, triggering events, and configurable timeout values per state.
*UC-05*

**FR-026** `[M]` The tool shall support assigning a sequence node to an initiator role or a responder role using the same state machine definition without requiring separate definitions for each role.
*UC-05*

**FR-027** `[M]` The tool shall validate a sequence node configuration against the sequence definition's state machine contract before marking the node execution-ready.
*UC-05*

**FR-028** `[M]` The tool shall detect and report incomplete state machines — missing transitions, undefined state references — during node configuration, saving the node in draft state rather than blocking the session.
*UC-05*

**FR-029** `[M]` The tool shall detect and report circular state transitions during node configuration.
*UC-05*

---

## Data Source / Provider

**FR-030** `[M]` The tool shall implement a Provider/Source abstraction supporting the following source types as interchangeable implementations: captured replay, generative (mutation-based), generative (grammar-based), static fixture, and parameterized template.
*UC-06*

**FR-031** `[M]` The tool shall allow a data source to be replaced on a sequence node or step without modifying the sequence definition, archiving the prior source configuration in the session.
*UC-06*

**FR-032** `[M]` The tool shall validate a configured data source against the bound protocol definition's constraints before accepting the binding.
*UC-06*

**FR-033** `[M]` The tool shall record source type and full configuration in the session artifact to enable reproduction of a test run.
*UC-06*

**FR-034** `[S]` The tool shall support custom data source plugins via a defined interface, validating interface compliance before accepting the binding.
*UC-06*

**FR-035** `[M]` The tool shall index a captured replay source by sequence step mapping at bind time, and flag frames that cannot be mapped to a sequence step.
*UC-06*

**FR-036** `[S]` The tool shall verify that a generative source can produce at least one output satisfying protocol definition constraints before accepting the binding, reporting failure if it cannot.
*UC-06*

---

## Sequence Execution

**FR-037** `[M]` The tool shall execute a sequence by: sending messages from the bound data source per current state, capturing responses, parsing responses per protocol definition, evaluating transition conditions, and advancing state.
*UC-07*

**FR-038** `[M]` The tool shall apply context extraction operations at defined sequence steps, storing extracted values exclusively in the session context store under named typed references. Raw values shall not appear in execution logs, task results, or any output outside the store. The store shall expose two access patterns: `value(key)` for use within sequence execution to construct protocol messages, and `ref(key)` for all other consumers (logs, results, reports, exports) which receive an opaque typed handle only.
*UC-08*

**FR-039** `[M]` The tool shall resolve named context store references as parameters in subsequent sequence steps within the same session, passing opaque typed references through the orchestration layer and resolving to raw values only at the point of protocol message construction.
*UC-08*

**FR-040** `[M]` The tool shall record every state transition in the execution log, including the transition condition matched and the branch path taken.
*UC-07*

**FR-041** `[M]` The tool shall record response parse failures in the execution log and invoke the sequence's defined exception handler if present, otherwise halting the sequence.
*UC-07*

**FR-042** `[M]` The tool shall record timeout events in the execution log and apply configured retry count or termination behavior.
*UC-07*

**FR-043** `[M]` The tool shall associate every finding with its originating sequence step, state machine state, and parsed protocol context.
*UC-07*

**FR-044** `[M]` The tool shall record context extraction failures with the source field reference and halt the sequence or follow the defined exception path.
*UC-08*

**FR-045** `[S]` The tool shall support a configurable step limit that terminates a sequence without a natural terminal state after a defined number of transitions.
*UC-07*

---

## Proxy / MITM

**FR-046** `[M]` The tool shall operate as a local network proxy, capturing all traffic between a configured client and target for the duration of a proxy session.
*UC-09*

**FR-047** `[M]` The tool shall parse captured proxy traffic using an applicable loaded protocol definition, and fall back to raw hex capture when no definition applies.
*UC-09*

**FR-048** `[M]` The tool shall automate local TLS certificate provisioning, prompting for elevation only on first invocation, and requiring no re-setup in subsequent sessions.
*UC-10*

**FR-049** `[M]` The tool shall detect whether a trusted local CA and valid certificate already exist and skip provisioning steps that are already satisfied.
*UC-10*

**FR-050** `[M]` The tool shall output exact manual provisioning commands when elevation is denied, leaving the session in a pending-TLS state.
*UC-10*

**FR-051** `[M]` The tool shall support protocol-aware transformation rules in interception mode, modifying named field values in in-flight messages according to protocol definition semantics.
*UC-11*

**FR-052** `[M]` The tool shall persist both the original and modified versions of every intercepted exchange in the session log.
*UC-11*

**FR-053** `[M]` The tool shall warn the user and require confirmation before forwarding a transformed message that fails protocol definition structural validation.
*UC-11*

**FR-054** `[S]` The tool shall support a manual interception mode that pauses each exchange for user inspection and optional modification before forwarding.
*UC-11*

**FR-055** `[S]` The tool shall support a drop rule in interception mode that discards a message, returns a connection reset to the originating side, and logs the event.
*UC-11*

---

## Reporting & Output

**FR-056** `[M]` The tool shall produce a test report that prioritizes findings by severity, with each finding stating: what was observed, why it is significant in application behavior terms, protocol context, and a reference to the raw evidence in the session log.
*UC-14*

**FR-057** `[C]` The tool shall express finding significance in plain-language terms in addition to technical precision when plain-language descriptions are available in the protocol definition's content metadata.
*UC-14*

**FR-057a** `[C]` During plugin/module onboarding, the tool shall use an LLM to generate plain-language descriptions for protocol elements and finding types that lack them, storing the generated content in the plugin's metadata for review and correction before use.
*(Plugin onboarding pipeline — D5)*

**FR-058** `[C]` The tool shall provide inline plain-language definitions for protocol elements and finding types when present in the plugin's content metadata.
*UC-14*

**FR-059** `[M]` The tool shall emit structured JSON output for all reports alongside human-readable output.
*UC-14, UC-15*

**FR-060** `[M]` The tool shall set exit code 0 when a report contains no findings, and a non-zero exit code when findings are present.
*UC-14, UC-15*

**FR-061** `[M]` The tool shall include an execution coverage summary — sequences run, states reached, inputs exercised — in any report that contains no findings.
*UC-14*

**FR-062** `[M]` The tool shall suppress human-readable output and emit JSON only when invoked in non-interactive mode.
*UC-15*

**FR-063** `[M]` The tool shall accept a test suite definition file specifying: sequence list, source bindings, execution order, pass/fail criteria, and execution mode (serial or parallel).
*UC-15*

**FR-064** `[M]` The tool shall merge results from all sequences in a suite into a single session artifact.
*UC-15*

**FR-065** `[S]` The tool shall support parallel sequence execution within a suite, preserving sequence ordering in the log via timestamps.
*UC-15*

**FR-066** `[M]` The tool shall support a fail-fast mode in suite execution that halts on the first sequence failure and records partial results.
*UC-15*

**FR-069** `[S]` The tool's suite execution engine shall support parallel sequence execution, per-task retry with configurable limits, and timeout enforcement without requiring custom implementations of these primitives.
*UC-15*

---

## Structured Messaging Content Model

**FR-070** `[M]` All user-facing messages — errors, findings, status, and guidance — shall be structured as content objects with at minimum two levels: a summary level (concise, generalized, plain-language) and a detail level (technically precise, full context). The active verbosity level shall be configurable per session and per invocation.
*UC-01, UC-14*

**FR-071** `[M]` Error messages shall be structured to include: what failed, in what context it failed, and what the user can do next — expressed at the configured verbosity level. No error shall produce only a raw exception or internal state dump as its user-facing output.
*UC-01 through UC-15*

**FR-072** `[M]` The structured message content model shall be the single authoring target for all message types in the tool and its protocol plugins. Plugin-contributed messages (finding descriptions, error explanations, protocol element descriptions) shall conform to the same multi-level structure.
*(Plugin authoring — D5)*

**FR-073** `[S]` The tool shall emit structured messages in machine-readable JSON format in non-interactive mode, preserving all levels of detail as distinct fields so that consumers can select the appropriate level programmatically.
*UC-15, UC-14*

---

## Tool Security Posture

**FR-074** `[M]` The tool shall encrypt sensitive values in the session context store at rest using a session-scoped key, such that the raw values are not recoverable from the session artifact without the key.
*UC-12*

**FR-075** `[M]` The tool shall overwrite sensitive values held in memory in the context store when the session terminates or the value is explicitly released, and shall not retain them in process memory beyond their required lifetime.
*UC-07, UC-08*

**FR-076** `[S]` The tool shall sign session artifacts to enable tamper detection on load, rejecting artifacts whose signatures do not match.
*UC-13*

**FR-077** `[M]` The tool shall validate TLS certificates for all outbound connections it initiates — registry lookups, plugin downloads, update checks — and refuse connections with invalid or untrusted certificates.
*(Registry, plugin distribution — D5)*

**FR-078** `[S]` The tool shall execute custom plugin code in an isolated execution environment that prevents direct access to the session context store's internal value store, the host filesystem beyond a declared sandbox path, and the network beyond declared allowed endpoints.
*UC-06 (FR-034)*

**FR-079** `[M]` The tool shall validate plugin interface compliance structurally before loading, and reject any plugin that attempts to register interfaces or hooks beyond those declared in its manifest.
*UC-06 (FR-034)*

---

## Summary

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

## Open Items

1. **FR-030 vs FR-034 conflict** — Plugin interface public API commitment timing. Deferred to D6 as a named constraint.

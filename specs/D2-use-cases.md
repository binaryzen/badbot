# D2 — Technical Use Case Matrix

## Coverage Map

| Use Case | Title | Stories |
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

---

## Use Cases

### UC-01 — Initialize Test Session
**Stories:** US-01, US-06, US-21
**Actor:** Any persona
**Preconditions:**
- Tool installed and accessible via CLI
- Target endpoint specified, or session artifact provided for restore

**Trigger:** User invokes tool with a target specification or session file

**Nominal flow:**
1. User provides target (host/port, protocol hint, or session file)
2. Tool loads applicable protocol definitions from registry
3. Tool initializes session context (ID, timestamp, configuration snapshot)
4. Tool evaluates target and presents relevant test categories
5. User selects or accepts suggested configuration
6. Session enters ready state

**Alternate flows:**
- *No matching protocol definition:* tool presents generic options; prompts to load or define one
- *Target unreachable:* session initialized in offline/authoring mode; connectivity error recorded

**Postconditions:** Session initialized with unique ID; config persisted; target reachability recorded
**Exceptions:** Malformed target specification; protocol definition version incompatible with tool version

---

### UC-02 — Render Protocol Buffer
**Stories:** US-03, US-04, US-05
**Actor:** DE, PD, SR
**Preconditions:**
- Session active
- At least one buffer available (captured, injected, or from file)
- Protocol definition loaded (optional — degrades gracefully without it)

**Trigger:** Buffer received from network capture, sequence execution, or user-provided file

**Nominal flow:**
1. Tool receives raw buffer
2. Protocol definition applied; fields parsed and decoded
3. High-level view rendered: field name → decoded value → description
4. Low-level view rendered: hex dump with field boundary and annotation overlays
5. Field selected in either view highlights corresponding region in the other

**Alternate flows:**
- *Partial parse:* buffer doesn't fully match definition → parsed portion rendered; unparsed bytes marked as unknown with offset
- *No definition loaded:* raw hex with byte offset markers only; no field annotation
- *Ambiguous parse:* multiple valid interpretations → tool presents alternatives; user selects

**Postconditions:** Buffer stored in session with parse annotation map; correlation index available for subsequent analysis
**Exceptions:** Buffer truncated mid-field; conflicting field boundaries in definition

---

### UC-03 — Load or Define Protocol Definition
**Stories:** US-19, US-20, US-21
**Actor:** PD, DE
**Preconditions:**
- Tool installed
- Definition source available: file path, registry ID, or user authoring intent

**Trigger:** User loads a file, queries a registry, or invokes definition authoring mode

**Nominal flow:**
1. User provides definition source
2. Tool parses schema: data structures, field types, static/parameterized values, validation constraints, sequence definitions
3. Tool validates definition for structural integrity
4. Definition registered and available to current and future sessions
5. Tool reports validation result with summary of registered structures and sequences

**Alternate flows:**
- *Validation failure:* tool reports specific errors with field/line references; definition not registered
- *Partial definition (structures only, no sequences):* registered with warning; sequence-dependent features unavailable
- *Registry lookup:* tool fetches and caches definition; version pinned to session

**Postconditions:** Definition registered; validation report attached to session; definition version recorded
**Exceptions:** Schema version mismatch; circular field references; ambiguous variable-length field definitions

---

### UC-04 — Validate Protocol Definition Against Reference Buffer
**Stories:** US-07, US-19
**Actor:** PD
**Preconditions:**
- Protocol definition loaded
- Known-good reference buffer available (file, hex string, or captured frame)

**Trigger:** User invokes definition validation against a reference buffer

**Nominal flow:**
1. User provides reference buffer and optionally a set of expected decoded values
2. Tool parses buffer using loaded definition
3. Tool reports: fields matched, values decoded, constraint violations, unparsed bytes
4. If expected values provided: tool compares decoded values against expectations and reports mismatches

**Alternate flows:**
- *Complete parse failure:* tool reports first field that fails to match and byte offset
- *Partial match:* matched fields reported; deviation point marked with context
- *Constraint violation:* field value decoded but fails defined constraint; reported as warning not error

**Postconditions:** Validation report stored in session; definition annotated with pass/fail against reference
**Exceptions:** Reference buffer ambiguous (multiple valid parses exist); buffer format unreadable

---

### UC-05 — Configure Sequence Node
**Stories:** US-06, US-07, US-14, US-29, US-30, US-31
**Actor:** PD, DE, SR
**Preconditions:**
- Protocol definition loaded with at least one sequence defined
- Session active

**Trigger:** User creates a sequence node within a test session

**Nominal flow:**
1. User selects a sequence definition
2. User assigns node role: initiator or responder
3. User configures state machine: initial state, named transitions, event bindings, timeout values
4. User binds a data source to the node (UC-06)
5. Tool validates node configuration against the sequence definition's state machine contract
6. Node registered in session as ready

**Alternate flows:**
- *Role conflicts with sequence constraints:* tool reports conflict and suggests valid role assignment
- *Incomplete state machine:* missing transitions flagged; node saved in draft state, not ready
- *Responder role:* tool binds node to listen on specified address/port; waits for inbound connection

**Postconditions:** Node registered with role, state machine configuration, and source binding; execution-ready flag set
**Exceptions:** Circular state transitions; transitions reference undefined states; initiator and responder both unbound in same sequence

---

### UC-06 — Configure Data Source (Provider/Source)
**Stories:** US-08, US-26, US-27, US-28
**Actor:** SR, PD, DE
**Preconditions:**
- Session active
- Sequence node exists to bind source to

**Trigger:** User selects or defines a data source for a node or individual sequence step

**Nominal flow:**
1. User selects source type: captured replay / generative / static fixture / parameterized template / custom plugin
2. User provides source configuration appropriate to type
3. Tool validates configuration against protocol definition constraints
4. Source bound to node or step; type and configuration recorded in session

**Alternate flows:**
- *Generative source:* user specifies strategy (random, mutation-based, grammar-based) and seed/boundary constraints; tool confirms valid inputs are producible
- *Replay source:* user provides capture file; tool indexes frames and maps to sequence steps; unmatched frames flagged
- *Custom plugin source:* user provides plugin path; tool loads and validates interface compliance before binding
- *Swap existing source:* user replaces bound source without modifying sequence definition; prior source config archived in session

**Postconditions:** Source bound and validated; source type and config recorded for session reproducibility
**Exceptions:** Capture file format unsupported; custom plugin fails interface validation; generative source cannot produce valid outputs under given constraints

---

### UC-07 — Execute Test Sequence
**Stories:** US-09, US-10, US-11, US-12, US-13, US-14, US-31
**Actor:** DE, SR, RTO, AP
**Preconditions:**
- Session initialized
- At least one sequence node configured and ready (UC-05)
- Data source bound (UC-06)
- Target reachable (or responder node listening)

**Trigger:** User invokes execution interactively or via scripted suite

**Nominal flow:**
1. Tool initializes execution context; associates with session
2. Initiator node sends first message per current state and data source
3. Tool captures response from target
4. Response parsed per protocol definition
5. Context extraction steps applied (UC-08)
6. State machine evaluates transition conditions against parsed response
7. Next state determined; corresponding action executed
8. Steps 3–7 repeat until terminal state or configured step limit reached
9. Execution summary appended to session log

**Alternate flows:**
- *Conditional branch:* response satisfies alternate transition condition → sequence follows alternate path; branch recorded in log
- *Timeout:* no response within configured window → timeout recorded; sequence retries or terminates per config
- *Unexpected response structure:* parse fails → failure recorded; exception handler invoked if defined in sequence, otherwise sequence halts

**Postconditions:** Full execution log stored in session; extracted context available to subsequent sequences; findings recorded with protocol context
**Exceptions:** Target connection lost mid-sequence; state machine reaches undefined state; data source exhausted before terminal state

---

### UC-08 — Extract Context from Protocol Response
**Stories:** US-12, US-13
**Actor:** DE, SR
**Preconditions:**
- Sequence execution active (UC-07)
- Response received and successfully parsed
- Sequence definition contains at least one extraction step at current position

**Trigger:** Execution reaches a sequence step with a defined context extraction operation

**Nominal flow:**
1. Tool applies extraction expression to parsed response fields
2. Extracted value stored in session context store under a named typed reference
3. Named reference made available as a resolvable parameter in subsequent sequence steps
4. Extraction event logged with source field reference (reference only — not value)

**Alternate flows:**
- *Extraction fails to match:* tool logs failure; sequence follows defined exception path if present, otherwise halts
- *Type constraint violation:* extracted value decoded but fails type check → tool logs mismatch; applies coercion if configured, otherwise halts

**Postconditions:** Named typed reference available in session context store; extraction logged with provenance (no raw values in log)
**Exceptions:** Extraction expression syntax error (surfaced at definition load time, not runtime); extracted value reference cycle

---

### UC-09 — Start Proxy / MITM Session
**Stories:** US-16, US-17, US-18, US-22
**Actor:** DE, SR
**Preconditions:**
- Tool installed
- TLS provisioned if target uses HTTPS (UC-10, one-time)
- Client (Chrome, application) configurable to route through proxy

**Trigger:** User invokes proxy mode with target and local port specification

**Nominal flow:**
1. Tool starts local proxy listener on configured port
2. User configures client to route traffic through proxy address
3. Traffic flows through tool; each exchange captured
4. Exchanges parsed per matching protocol definition
5. Parsed exchanges rendered in real-time (UC-02)
6. Session context updated with each observed exchange

**Alternate flows:**
- *No matching protocol definition:* raw capture mode; hex-only rendering, no field annotation
- *Interception mode enabled:* tool pauses each exchange at configured points for inspection or rule-based transformation (UC-11) before forwarding

**Postconditions:** All observed exchanges stored in session with parse annotations; session fully replayable
**Exceptions:** Client rejects proxy certificate; target uses certificate pinning; proxy port already in use

---

### UC-10 — Provision TLS for Local Development
**Stories:** US-17
**Actor:** DE
**Preconditions:**
- User intends to proxy HTTPS traffic to a local application
- OS allows trust store modification (standard user scenario)

**Trigger:** Tool detects HTTPS target and no trusted local CA present; or user explicitly invokes TLS setup

**Nominal flow:**
1. Tool checks for mkcert installation and trusted local CA
2. If absent: tool installs mkcert and runs `mkcert -install` (elevation prompt issued once)
3. Tool generates certificate for localhost / 127.0.0.1 (and any additional specified hostnames)
4. Certificate and key stored in tool's config directory
5. Proxy listener configured to present generated certificate
6. Tool confirms trust store updated; reports readiness

**Alternate flows:**
- *mkcert already installed and CA trusted:* skip to step 3
- *Elevation denied:* tool outputs manual setup steps with exact commands; marks TLS as pending

**Postconditions:** Local CA trusted by system and Chrome; certificate ready for proxy use; no re-setup required in future sessions
**Exceptions:** Corporate policy blocks trust store modification; OS keychain inaccessible; conflicting existing local CA

---

### UC-11 — Intercept and Transform In-Flight Traffic
**Stories:** US-18, US-22
**Actor:** SR, RTO
**Preconditions:**
- Proxy session active (UC-09)
- Interception rules defined in protocol definition, or manual interception mode enabled

**Trigger:** Traffic captured by proxy matches an interception rule, or manual pause is active

**Nominal flow:**
1. Request arrives at proxy from client
2. Tool evaluates request against interception rules
3. Matching rule applied: field modified, value injected, or message dropped per protocol-aware transformation
4. Modified request forwarded to target
5. Response captured; response-side rules evaluated and applied
6. Modified response returned to client
7. Both original and modified versions of each exchange logged to session

**Alternate flows:**
- *No rule matches:* traffic forwarded unmodified; still logged
- *Manual mode:* tool pauses exchange; presents to user for ad-hoc modification; user confirms before forwarding
- *Drop rule:* request discarded; client receives connection reset; logged

**Postconditions:** Original and modified exchanges both persisted in session; transformation log available for replay
**Exceptions:** Transformation produces structurally invalid message per protocol definition (tool warns, user confirms or aborts); target drops connection on receipt of modified message

---

### UC-12 — Save and Serialize Session
**Stories:** US-23, US-24, US-25
**Actor:** DE, RTO
**Preconditions:** Active session with state to serialize

**Trigger:** User invokes save explicitly, or auto-save interval fires

**Nominal flow:**
1. Tool serializes session: configuration, sequence definitions, execution logs, context store references, findings, source bindings
2. Tool applies configured redaction policy to context store values
3. If auto-save and no policy configured and result would be 100% redacted: tool prompts user to configure policy
4. Artifact written to file with session ID, version, and timestamp
5. Redaction manifest stored alongside artifact

**Alternate flows:**
- *User-initiated export:* tool presents summary of what will be included or redacted; user confirms
- *Export-for-sharing mode:* stricter redaction profile applied; user confirms sharing intent before write

**Postconditions:** Session artifact persisted; redaction manifest stored; session restorable from artifact
**Exceptions:** Filesystem write permission denied; sensitive pattern scan produces excessive false positives on binary field data (user can override per field type)

---

### UC-13 — Load Saved Session
**Stories:** US-23, US-25
**Actor:** DE, RTO
**Preconditions:** Valid session artifact file accessible

**Trigger:** User invokes tool with session file path argument

**Nominal flow:**
1. Tool reads and validates artifact schema and version
2. Session state, configuration, context store, and logs restored
3. Tool presents session summary: creation timestamp, sequences executed, findings count, redacted fields present
4. User continues from restored state or reviews historical data

**Alternate flows:**
- *Version mismatch:* tool attempts schema migration; reports fields that could not be migrated with fallback values used
- *Redacted values present:* tool notes placeholders in context store; user may supply values interactively to restore full execution capability

**Postconditions:** Session fully restored; execution continuable; historical log browsable
**Exceptions:** Artifact corrupt or truncated; schema version incompatible and migration fails; referenced protocol definition no longer available in registry

---

### UC-14 — Generate Test Report
**Stories:** US-02, US-15, US-32
**Actor:** DE, AP
**Preconditions:** Session with at least one completed sequence execution

**Trigger:** User requests report explicitly, or sequence execution completes in non-interactive mode

**Nominal flow:**
1. Tool aggregates findings from session execution log
2. Findings prioritized by severity and exploitability signal
3. High-level summary rendered: finding count, categories, top items with plain-language significance
4. Each finding includes: what was observed, why it matters in application behavior terms, protocol context, drill-down path to raw evidence
5. Structured JSON output emitted alongside human-readable format

**Alternate flows:**
- *No findings:* tool reports clean result with execution coverage summary (sequences run, states reached, inputs tested)
- *Pipeline / non-interactive mode:* human-readable output suppressed; JSON only; exit code set

**Postconditions:** Report stored in session; exit code set for pipeline consumers; JSON output available for downstream tooling
**Exceptions:** Session log corrupted mid-execution; finding significance classification unavailable for unrecognized protocol (raw observation reported without interpretation)

---

### UC-15 — Execute Scripted Test Suite
**Stories:** US-09, US-10, US-11, US-32
**Actor:** AP, RTO, DE
**Preconditions:**
- Test suite definition file exists and is valid
- Protocol definitions referenced by suite are available
- Target reachable

**Trigger:** CLI invocation with suite file and target arguments

**Nominal flow:**
1. Tool reads suite definition: sequence list, source bindings, execution order, pass/fail criteria
2. Tool initializes session
3. Sequences executed in defined order (or parallel per suite config)
4. Findings collected per sequence; pass/fail evaluated against criteria
5. Report generated (UC-14)
6. Session saved; exit code set

**Alternate flows:**
- *Step failure, default mode:* subsequent steps continue; failure logged; final exit code reflects any failure
- *Fail-fast mode:* execution halts on first failure; partial session saved; exit code non-zero
- *Parallel execution:* results merged into single session; ordering preserved in log with timestamps

**Postconditions:** Session artifact saved; structured report available; exit code machine-readable by pipeline
**Exceptions:** Suite definition schema invalid; circular sequence dependencies; target unreachable at invocation time

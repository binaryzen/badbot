# D5 — Modularization Design

## Component Inventory

Fourteen components plus one shared utility. Organized from infrastructure outward.

| ID | Component | Primary Responsibility | Covers (FRs) |
|---|---|---|---|
| C-01 | Message Content Model | Structured multi-level messages for all user-facing output | FR-070, FR-071, FR-072, FR-073 |
| C-02 | Context Store | Typed reference store; redaction enforcement; sensitive value lifecycle | FR-004, FR-038, FR-039, FR-074, FR-075 |
| C-03 | Protocol Definition Engine | Parse, validate, build protocol messages; binary and REST backends | FR-010, FR-011, FR-015, FR-016, FR-017, FR-018, FR-023, FR-067 |
| C-04 | Protocol Registry | Catalog of loaded definitions; versioning; discovery suggestions | FR-012, FR-013, FR-014, FR-068 |
| C-05 | Provider/Source Framework | ISource abstraction + built-in implementations; plugin seam | FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036 |
| C-06 | Buffer Renderer | Dual-view rendering; tshark dissection; field correlation | FR-019, FR-020, FR-021, FR-022, FR-024 |
| C-07 | Sequence Engine | State machine execution; step advancement; context extraction; log production | FR-025, FR-026, FR-027, FR-028, FR-029, FR-037, FR-038, FR-039, FR-040, FR-041, FR-042, FR-043, FR-044, FR-045 |
| C-08 | Proxy Engine | mitmproxy integration; TLS provisioning; traffic capture; interception rules | FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055 |
| C-09 | Suite Orchestrator | Prefect-based suite execution; parallel/serial; pass/fail; result aggregation | FR-063, FR-064, FR-065, FR-066, FR-069 |
| C-10 | Session Manager | Session lifecycle; artifact serialization/migration; key management; log recording | FR-001, FR-002, FR-003, FR-003a, FR-005, FR-006, FR-007, FR-008, FR-009, FR-074, FR-075, FR-076 |
| C-11 | Report Generator | Finding aggregation; severity prioritization; multi-level output; JSON emission | FR-056, FR-057, FR-057a, FR-058, FR-059, FR-061 |
| C-12 | Plugin Manager | Plugin loading; manifest validation; sandboxing; content onboarding | FR-034, FR-072, FR-078, FR-079 |
| C-13 | Library API | Public surface; execution log handoff; non-interactive mode detection | FR-009, FR-060, FR-062 |
| C-14 | CLI Layer | Argument parsing; command routing; output formatting; exit codes | FR-060, FR-062, FR-073 |
| U-01 | NetworkClient (utility) | Shared outbound HTTP/S client with enforced TLS validation | FR-077 |

---

## Shared Data Types

Named types that cross component boundaries. Defined here to prevent interface ambiguity.

### Finding
```
Finding
  id:               UUID
  severity:         Severity  # CRITICAL | HIGH | MEDIUM | LOW | INFO
  message:          IMessage  # summary + detail levels per C-01
  sequence_step:    StepRef
  state:            StateName
  protocol_context: ParseResult
  evidence_ref:     ContextRef   # opaque reference — raw value stays in C-02
  timestamp:        datetime
```
Produced by C-07 (Sequence Engine) and C-08 (Proxy Engine). Consumed by C-11 (Report Generator) and C-10 (Session Manager for persistence).

### LogEntry
```
LogEntry
  id:          UUID
  timestamp:   datetime
  kind:        LogKind  # TRANSITION | PARSE_FAILURE | TIMEOUT | EXTRACTION | EXCHANGE | FINDING
  message:     IMessage
  context_ref: ContextRef?   # optional reference to associated context value
  step_ref:    StepRef?
  state:       StateName?
```
Produced by C-07 and C-08. Written to session via `C-10.record()`.

### ExecutionResult
```
ExecutionResult
  sequence_id:  UUID
  status:       ExecutionStatus  # COMPLETED | HALTED | FAILED | TIMEOUT
  log_entries:  List[LogEntry]
  findings:     List[Finding]
  coverage:     CoverageSummary  # states reached, steps executed, inputs exercised
```
Returned by C-07. Caller (C-09 or C-13) writes log entries and findings to C-10.

---

## Interface Definitions

### C-01 — IMessage
```
summary:    str    # plain-language, always present
detail:     str    # technically precise, always present
structured: dict   # machine-readable fields
render(verbosity: Verbosity) → str
```
*Covers: FR-070, FR-071, FR-072, FR-073*

All user-facing output in every component is an IMessage. No component emits raw strings to the user. Plugin-contributed messages implement the same interface.

---

### C-02 — IContextStore
```
store(key, value, type: SensitiveType) → ContextRef
value(ref: ContextRef) → RawValue        # RESTRICTED — C-07 only; type error for all other callers
ref(key) → ContextRef                    # opaque handle for all other consumers
release(ref: ContextRef)                 # overwrites value in memory
release_all()                            # called by C-10.close() on session termination
apply_redaction(policy: RedactionPolicy) → RedactedExport
encrypt_at_rest(key: SessionKey) → EncryptedStore
```
*Covers: FR-004, FR-038, FR-039, FR-074, FR-075*

`value()` is enforced at the component boundary — callers outside C-07 receive a type error at call time, not at runtime.

---

### C-03 — IProtocolDefinition
```
parse(buffer: bytes) → ParseResult
parse_all(buffer: bytes) → List[ParseResult]   # for ambiguous buffers; FR-023
build(fields: FieldMap) → bytes
validate(buffer: bytes, expected?: FieldMap) → ValidationResult
sequences() → List[SequenceDefinition]
schema() → ProtocolSchema
```
*Covers: FR-010, FR-011, FR-015, FR-016, FR-017, FR-018, FR-023, FR-067*

`parse_all()` returns all structurally valid interpretations when the buffer is ambiguous under the loaded definition. C-06 presents alternatives to the user when `len(parse_all()) > 1`.

---

### C-04 — IProtocolRegistry
```
load(source: FilePath | RegistryID) → IProtocolDefinition
register(definition: IProtocolDefinition)
lookup(hint: TargetHint) → List[IProtocolDefinition]
versions(name) → List[VersionRef]
```
*Covers: FR-012, FR-013, FR-014, FR-068*

Outbound registry calls route through U-01 (NetworkClient) for TLS enforcement.

---

### C-05 — ISource
```
next() → bytes | FieldMap
reset()
is_exhausted() → bool
bind(definition: IProtocolDefinition)
validate_against(definition: IProtocolDefinition) → ValidationResult
config() → SourceConfig                  # serializable; stored in session by C-10
```
*Covers: FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036*

---

### C-06 — IBufferRenderer
```
render(buffer: bytes, definition?: IProtocolDefinition) → RenderResult
correlate(field: FieldRef) → ByteRange
```
*Covers: FR-019, FR-020, FR-021, FR-022, FR-024*

`RenderResult` contains both high-level and low-level views plus the correlation map. When `C-03.parse_all()` returns multiple results, `render()` includes all interpretations and the caller presents a selection prompt. Satisfies FR-023 jointly with C-03.

---

### C-07 — ISequenceEngine
```
configure(node: SequenceNodeConfig) → SequenceNode
execute(node: SequenceNode, context: IContextStore) → ExecutionResult
```
*Covers: FR-025, FR-026, FR-027, FR-028, FR-029, FR-037, FR-038, FR-039, FR-040, FR-041, FR-042, FR-043, FR-044, FR-045*

`SequenceNode` encapsulates: role (INITIATOR | RESPONDER), state machine instance, bound source, protocol definition. `ExecutionResult` contains `List[LogEntry]` and `List[Finding]` — callers (C-09 or C-13) write these to C-10 via `record()`. C-07 never writes to C-10 directly (no dependency).

---

### C-08 — IProxyEngine
```
start(config: ProxyConfig) → ProxySession
stop(session: ProxySession) → List[LogEntry]   # returns captured exchanges as log entries
add_rule(session: ProxySession, rule: InterceptionRule)
provision_tls(hostnames: List[str]) → CertificateBundle
```
*Covers: FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055*

`stop()` returns all captured and intercepted exchanges as `LogEntry` objects. The caller (C-13) writes these to C-10 via `record()`. C-08 does not depend on C-10 directly.

---

### C-09 — ISuiteOrchestrator
```
run(suite: SuiteDefinition, session: Session) → SuiteResult
```
*Covers: FR-063, FR-064, FR-065, FR-066, FR-069*

`SuiteDefinition` specifies sequences, sources, order, pass/fail criteria, execution mode. After each sequence execution, C-09 calls `C-10.record()` with the `ExecutionResult` log entries and findings. Prefect flows are an internal implementation detail — not exposed at this interface.

---

### C-10 — ISessionManager
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
*Covers: FR-001, FR-002, FR-003, FR-003a, FR-005, FR-006, FR-007, FR-008, FR-009, FR-074, FR-075, FR-076*

`generate_key()` is called internally during `create()` — the session key is passed to `C-02.encrypt_at_rest()` at session initialization. `close()` calls `C-02.release_all()` to satisfy FR-075.

---

### C-11 — IReportGenerator
```
generate(session: Session) → Report
```
*Covers: FR-056, FR-057, FR-058, FR-059, FR-061*

`Report` contains `List[Finding]`, each as a structured `Finding` type with `IMessage` at summary/detail levels, protocol context, and a `ContextRef` to raw evidence. C-11 reads findings from the session log — it never calls `C-02.value()`.

---

### C-12 — IPluginManager
```
load(path: PluginPath) → Plugin
validate(plugin: Plugin) → ValidationResult
onboard(plugin: Plugin) → OnboardedPlugin    # triggers LLM description generation; FR-057a
sandbox(plugin: Plugin) → SandboxedPlugin
```
*Covers: FR-034, FR-072, FR-078, FR-079*

Outbound plugin download calls route through U-01 (NetworkClient) for TLS enforcement (FR-077).

---

### C-13 — ILibraryAPI
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
*Covers: FR-009, FR-060, FR-062*

C-13 is the execution log handoff coordinator for non-suite paths: after `C-07.execute()` returns `ExecutionResult`, C-13 calls `C-10.record()`. After `C-08.stop()` returns captured exchanges, C-13 calls `C-10.record()`. Exit codes (FR-060) and non-interactive mode (FR-062) are determined at C-13/C-14 boundary.

---

### C-14 — CLI Layer
*Covers: FR-060, FR-062, FR-073*

Thin shell over C-13. Responsible for: argument parsing, command routing, exit code emission, suppressing human-readable output in non-interactive mode, and rendering structured JSON messages in pipeline mode.

---

### U-01 — NetworkClient (Shared Utility)
```
get(url, headers?) → Response
post(url, body, headers?) → Response
```
*Covers: FR-077*

All outbound HTTP/S calls from C-04 (registry lookups) and C-12 (plugin downloads) route through this utility. TLS certificate validation is enforced unconditionally — connections with invalid or untrusted certificates are refused and raise a typed error. Not a full component; a shared utility with no state.

---

## Dependency Graph

```
C-14 CLI Layer
  └→ C-13 Library API
        ├→ C-10 Session Manager
        │     ├→ C-02 Context Store
        │     │     └→ C-01 Message Content Model
        │     └→ C-01 Message Content Model
        ├→ C-04 Protocol Registry
        │     ├→ C-03 Protocol Definition Engine
        │     │     ├→ [Construct OSS]
        │     │     ├→ [OpenAPI parsers OSS]
        │     │     └→ C-01 Message Content Model
        │     ├→ C-12 Plugin Manager
        │     │     ├→ [U-01 NetworkClient]
        │     │     └→ C-01 Message Content Model
        │     └→ [U-01 NetworkClient]
        ├→ C-06 Buffer Renderer
        │     ├→ C-03 Protocol Definition Engine
        │     ├→ [tshark subprocess]
        │     └→ C-01 Message Content Model
        ├→ C-07 Sequence Engine
        │     ├→ C-03 Protocol Definition Engine
        │     ├→ C-05 Provider/Source Framework
        │     │     ├→ C-03 Protocol Definition Engine
        │     │     ├→ [Boofuzz primitives OSS]
        │     │     ├→ [Hypothesis OSS]
        │     │     └→ C-01 Message Content Model
        │     ├→ C-02 Context Store
        │     ├→ [transitions OSS]
        │     └→ C-01 Message Content Model
        ├→ C-08 Proxy Engine
        │     ├→ C-03 Protocol Definition Engine
        │     ├→ C-06 Buffer Renderer
        │     ├→ C-07 Sequence Engine
        │     ├→ C-02 Context Store
        │     ├→ [mitmproxy OSS]
        │     ├→ [mkcert subprocess]
        │     └→ C-01 Message Content Model
        ├→ C-09 Suite Orchestrator
        │     ├→ C-07 Sequence Engine
        │     ├→ C-10 Session Manager
        │     ├→ [Prefect OSS]
        │     └→ C-01 Message Content Model
        └→ C-11 Report Generator
              ├→ C-10 Session Manager
              ├→ C-02 Context Store  (refs only — never calls value())
              └→ C-01 Message Content Model
```

No circular dependencies. C-01 and C-02 remain the foundation. U-01 (NetworkClient) is a leaf — no internal dependencies.

**Execution log write path (resolved):** C-07 and C-08 return log entries and findings in their return types. C-09 and C-13 write these to C-10 via `record()`. Neither C-07 nor C-08 depends on C-10 directly.

---

## OSS Integration Seams

| OSS Candidate | Seam Location | Component | Mode | Covers (FRs) |
|---|---|---|---|---|
| Construct | Binary parse/build backend | C-03 | Library import | FR-010, FR-011, FR-015, FR-016 |
| OpenAPI parsers | REST definition import | C-03 | Library import | FR-067, FR-068, FR-010 |
| transitions | FSM engine | C-07 | Library import | FR-025, FR-026, FR-027, FR-028, FR-029 |
| mitmproxy | HTTP/HTTPS proxy | C-08 | Library import | FR-046, FR-047, FR-051, FR-054, FR-055 |
| Boofuzz primitives | Mutation-based Source | C-05 | Library import | FR-030, FR-035, FR-036 |
| Hypothesis | Parameterized template Source | C-05 | Library import | FR-030, FR-036 |
| Prefect v3 | Suite flow/task execution | C-09 | Library import | FR-063, FR-065, FR-066, FR-069 |
| tshark | Protocol dissection | C-06 | Subprocess | FR-019, FR-020, FR-021, FR-047 |
| mkcert | TLS provisioning | C-08 | Subprocess | FR-048, FR-049, FR-050 |
| jwt-tool | JWT mutation Source | C-05 | Plugin (first-party) | FR-030, FR-051 |
| CORScanner | CORS check | C-05 | Plugin (first-party) | FR-030, FR-046 |
| Arjun | Parameter discovery | C-04 | Subprocess (discovery) | FR-068 |
| Dredd | Contract validation | C-03 | Subprocess (optional) | FR-017, FR-018 |

---

## Plugin API Surface (Product-Facing)

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
IPluginMessageRegistry     →  contributes IMessage definitions for finding types,
                               protocol elements, error conditions (C-01)
```

A plugin cannot:
- Call `IContextStore.value()` directly
- Register hooks outside declared manifest capabilities
- Access other plugins' state

**Versioning commitment:** Plugin interface v1 published only after HTTP/REST seed plugin validates the contract. Breaking changes require a new interface version; old versions supported for a defined window.

---

## First Protocol: HTTP/REST Plugin (Seed)

Ships bundled. Validates the plugin model before the public API is committed.

- `IPluginProtocolDefinition` — HTTP/HTTPS structures; OpenAPI import pipeline
- `IPluginSource` implementations — JWT mutation (jwt-tool), CORS check (CORScanner), HTTP replay
- `IPluginMessageRegistry` — structured messages for all HTTP-specific findings
- Sequence definitions — S-01 through S-07 test scenarios from D4

---

## UI Layer Boundary

Interactive UI decision (TUI vs local web UI) remains deferred. C-13 Library API is the boundary. Any UI layer is a new consumer of C-13 — no internal components are exposed or modified.

---

## Gap Resolution Record

| Gap | FR(s) | Resolution |
|---|---|---|
| No outbound TLS owner | FR-077 | Added U-01 NetworkClient utility; C-04 and C-12 route all outbound calls through it |
| Ambiguous parse interface | FR-023 | Added `parse_all()` to IProtocolDefinition (C-03); C-06 uses it to present alternatives |
| Execution log write path | FR-040–044 | C-07 returns LogEntry list in ExecutionResult; C-09/C-13 write to C-10.record() |
| Proxy exchange persistence | FR-052 | C-08.stop() returns LogEntry list; C-13 writes to C-10.record() |
| Session key management | FR-074, FR-076 | Added generate_key() and signing_key() to ISessionManager (C-10); called at create() |
| Session termination hook | FR-075 | Added close() to ISessionManager; calls C-02.release_all() |
| Interactive placeholder fill | FR-008 | Added fill_placeholder() to ISessionManager (C-10) |
| Finding data model undefined | FR-043 | Defined Finding as a named shared data type |

---

## D5 Success Criteria Check

| Criterion | Status |
|---|---|
| Each component owns a cohesive responsibility | ✓ |
| Interfaces are narrow and explicit | ✓ |
| No circular dependencies | ✓ |
| OSS components slot into named seams with FR coverage | ✓ |
| Each component independently testable via interface injection | ✓ |
| All FRs traced to at least one component | ✓ |
| Plugin interface is product-facing with explicit commitment model | ✓ |

**Carried to D6:** Plugin interface v1 publication timing.

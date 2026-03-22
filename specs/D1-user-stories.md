# D1 — User Story Catalog

## Personas

| Persona | Role |
|---|---|
| **[DE] Domain Engineer** | **Primary — tradeoff authority** |
| [SR] Security Researcher | Specialist |
| [PD] Protocol Developer | Specialist |
| [RTO] Red Team Operator | Specialist |
| [AP] Automation Pipeline | Non-human consumer |

### Primary Persona Detail — Domain Engineer
An engineer with a CS degree and strong practical depth in one or two technical domains (e.g. backend, networking, embedded) but without formal security training. Capable of understanding complex multi-layer problems when context is surfaced — the gap is not comprehension, it's knowing where to look and what to look for.

When tradeoffs conflict, this persona's needs take priority.

**Key requirement pressures:**
- Context must travel with results (output explains significance, not just facts)
- Guided entry points — opinionated starting paths, not blank canvas
- Progressive disclosure — summary first, raw detail behind a drill-down
- Vocabulary bridging — security terms defined inline or mapped to known domain concepts

---

## Stories

### Test Discovery & Guided Entry

**US-01** `[DE]`
As a Domain Engineer, I want the tool to suggest relevant test categories when I point it at an application endpoint, so that I can start a meaningful test run without knowing the security testing vocabulary in advance.

**US-02** `[DE]`
As a Domain Engineer, I want test results to explain what was found and why it matters in terms of application behavior, so that I can act on findings without having to separately research each vulnerability class.

---

### Protocol Visualization

**US-03** `[DE]`
As a Domain Engineer, I want to see my application's protocol exchanges in a human-readable key/value format alongside the raw bytes, so that I can understand what's happening at both semantic and wire levels without switching tools.

**US-04** `[PD]`
As a Protocol Developer, I want to inspect raw hex buffers with per-field annotations for a specific protocol, so that I can verify my implementation produces correctly structured messages.

**US-05** `[SR]`
As a Security Researcher, I want to correlate decoded high-level fields with their exact byte positions in the stream, so that I can identify parsing discrepancies that may indicate exploitable edge cases.

---

### Simulation Test Bench

**US-06** `[DE]`
As a Domain Engineer, I want to run my application against a simulated protocol peer without needing a live external service, so that I can test security behavior in a controlled, reproducible environment.

**US-07** `[PD]`
As a Protocol Developer, I want to define a protocol harness that validates the structure and sequencing of request/response exchanges, so that I can catch malformed or out-of-order messages early in development.

**US-08** `[RTO]`
As a Red Team Operator, I want to replay captured traffic and inject mutations at specified fields, so that I can test how the application handles unexpected or malformed inputs at the protocol level.

---

### Scripted Workflows

**US-09** `[DE]`
As a Domain Engineer, I want to run a named test suite against my application with a single invocation and receive a prioritized summary report, so that I can integrate security checks into my development workflow without manual orchestration.

**US-10** `[RTO]`
As a Red Team Operator, I want to script a multi-step attack chain that sequences protocol interactions with branching logic, so that I can automate complex scenarios that depend on stateful exchanges.

**US-11** `[AP]`
As an Automation Pipeline, I want to execute a scripted test suite and receive structured output (pass/fail with traceable detail), so that I can gate deployments on security test results without human interpretation.

---

### Conditional Sequences & Context Extraction

**US-12** `[DE]`
As a Domain Engineer, I want the tool to extract tokens or session values from application responses and automatically use them in subsequent requests, so that I can test authenticated workflows without manually managing session state.

**US-13** `[SR]`
As a Security Researcher, I want to define conditional branching in a test sequence based on response content or status, so that I can probe different application code paths depending on how the target responds.

**US-14** `[PD]`
As a Protocol Developer, I want to simulate a stateful protocol peer that responds based on what the application under test sends, so that I can validate my implementation against realistic, context-aware server behavior.

---

### Reporting & Output

**US-15** `[DE]`
As a Domain Engineer, I want a summary view that surfaces actionable findings first with drill-down to technical detail, so that I can assess what needs attention without being confronted with raw protocol output as the default.

---

### MITM / Proxy

**US-16** `[DE]`
As a Domain Engineer, I want to route my application's traffic through a transparent proxy so I can observe real protocol exchanges before writing any tests, so that I can discover what my application actually does rather than guessing at what to target.

**US-17** `[DE]`
As a Domain Engineer, I want the tool to handle TLS certificate setup for local development automatically, so that Chrome and other clients can communicate through the proxy without manual certificate management or browser warnings.

**US-18** `[SR]`
As a Security Researcher, I want to intercept live requests between a client and server, modify them in flight, and observe the application's response, so that I can probe behavior interactively before committing it to a scripted test sequence.

---

### Protocol Definition

**US-19** `[PD]`
As a Protocol Developer, I want to define a protocol as a structured configuration — specifying data structures, field types, static and parameterized values, validation constraints, and formats — so that the tool can parse, analyze, generate, and validate messages for that protocol without requiring changes to the tool's core.

**US-20** `[PD]`
As a Protocol Developer, I want to define a stateful interaction sequence as a flowchart with parameterized decision points and context extraction steps, so that the tool can automate multi-step protocol exchanges where each step depends on what the previous response contained.

**US-21** `[DE]`
As a Domain Engineer, I want to load an existing protocol definition and immediately begin testing my application against it, so that I can benefit from contributed protocol knowledge without needing to understand the protocol internals first.

**US-22** `[SR]`
As a Security Researcher, I want to define automated request and response transformations within a protocol definition, so that the proxy layer can modify in-flight traffic according to protocol-aware rules rather than raw byte offsets.

---

### Session Persistence

**US-23** `[DE]`
As a Domain Engineer, I want to save my complete test session — configuration, active state, findings, and extracted context — as a portable artifact, so that I can resume it later or share it without losing progress or reconstructing it manually.

**US-24** `[DE]`
As a Domain Engineer, I want the tool to identify and flag potentially sensitive values in my session before export — credentials, tokens, captured secrets — and require confirmation before including them, so that I don't inadvertently share confidential data.

**US-25** `[RTO]`
As a Red Team Operator, I want to export a completed test session as a fully reproducible artifact, so that I can replay or adapt the sequence in a different environment without reconstructing it from memory.

---

### Provider / Source Abstraction

**US-26** `[SR]`
As a Security Researcher, I want to configure a sequence step to use a generative data source — producing protocol-valid inputs automatically via mutation or grammar-based strategies — so that I can explore edge cases without manually crafting each payload.

**US-27** `[DE]`
As a Domain Engineer, I want to swap the data source for a sequence step without rewriting the sequence definition, so that I can run the same test flow against captured traffic, generated inputs, or static fixtures interchangeably.

**US-28** `[PD]`
As a Protocol Developer, I want to define a custom data provider that generates field values according to protocol-specific domain rules, so that generated test inputs respect the semantic constraints of the protocol and produce meaningful results rather than noise.

---

### State Machine Sequence Model

**US-29** `[PD]`
As a Protocol Developer, I want to define protocol participants as state machines with named states, transitions, and triggering events, so that the tool can model and automate either side of a protocol exchange from a single definition.

**US-30** `[SR]`
As a Security Researcher, I want to assign a sequence node to an initiator or responder role using a shared state machine definition, so that I can simulate either side of a protocol exchange without maintaining separate implementations for each.

**US-31** `[DE]`
As a Domain Engineer, I want to run my application against a simulated counterpart whose behavior is driven by the same state machine model as a real peer, so that the simulation produces realistic, state-aware responses rather than static scripted ones.

---

### CLI / Pipeline Interface

**US-32** `[AP]`
As an Automation Pipeline, I want the tool's CLI to emit structured output (JSON, exit codes) in addition to human-readable output, so that I can consume results programmatically without parsing formatted text.

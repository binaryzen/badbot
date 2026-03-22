# badbot — Specification Index

This directory contains the complete specification for badbot, an interactive local CLI tool for orchestrated ad-hoc networked application vulnerability testing.

The spec was produced in a structured sequence: personas and user stories first, then use cases, then functional and architectural requirements, then OSS analysis and component design, with a master spec synthesizing everything at the end. Each document carries upstream traceability pointers to the document(s) that motivated it.

---

## Start Here

**[D7 — Master Spec](D7-master-spec.md)** is the single authoritative reference. It is self-contained — you can read it without consulting any other document. All other documents exist as the working record of how decisions were reached and provide full detail where D7 summarizes.

---

## Documents

| # | File | Contents | Key Outputs |
|---|---|---|---|
| D1 | [D1-user-stories.md](D1-user-stories.md) | Personas, 32 user stories across 11 capability areas | Primary persona definition (Domain Engineer); story catalog with acceptance signals |
| D2 | [D2-use-cases.md](D2-use-cases.md) | 15 technical use cases derived from D1; full nominal/alternate/exception flows | Use case coverage map; error path inventory |
| D3 | [D3-functional-requirements.md](D3-functional-requirements.md) | 80 functional requirements (61 Must / 16 Should / 3 Could) derived from D2 | FR catalog; redaction policy model; structured messaging model; tool security posture |
| D4 | [D4-oss-landscape.md](D4-oss-landscape.md) | OSS analysis across 7 functional areas; 8 API security test scenarios | OSS verdict matrix; license risk summary; build vs. leverage decisions |
| D5 | [D5-modularization.md](D5-modularization.md) | 14 components + 1 utility; interface definitions; dependency graph; OSS seams | Component model; shared data types; plugin API surface; gap resolution record |
| D6 | [D6-architectural-requirements.md](D6-architectural-requirements.md) | 13 architectural requirements; 9 constraints with rationale, cost, and tradeoff | Performance envelope; portability; testability rules; constraint/FR consistency check |
| D7 | [D7-master-spec.md](D7-master-spec.md) | Authoritative synthesis of D1–D6 | Full traceability chain; resolved open items; scope boundaries; deferred decisions |

---

## Dependency Order

```
D1 (Stories)
  └→ D2 (Use Cases)
        └→ D3 (Functional Requirements)
              ├→ D4 (OSS Landscape)        ← informs build/leverage decisions
              ├→ D5 (Modularization)        ← component model satisfying FRs
              └→ D6 (Architectural Req's)   ← non-functional constraints on the above
                    └→ D7 (Master Spec)     ← authoritative synthesis
```

---

## Scope Summary

**In scope for v1:** HTTP/REST protocol testing (bundled seed plugin), local proxy/MITM with automatic TLS provisioning, state-machine-based sequence execution with context extraction, suite orchestration (serial and parallel), session persistence with redaction policy, CLI with JSON output.

**Out of scope for v1 (with defined addition paths):** Binary protocols, WebSocket, gRPC, interactive TUI/web UI, public plugin API commitment. All are addable without core changes once the HTTP/REST seed plugin validates the component model.

**Implementation language:** Python 3.10+, pip-installable, no server infrastructure required, runs on Windows 10+, macOS 12+, and mainstream Linux distributions.

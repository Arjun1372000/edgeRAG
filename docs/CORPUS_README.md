# EdgeRAG Corpus v2

This is the synthetic maintenance knowledge corpus for the EdgeRAG project.

## Purpose

Corpus v2 is designed to test more realistic RAG behavior than the original five-SOP smoke-test corpus.

It deliberately contains:
- Failure-specific SOPs.
- Diagnostic procedures that overlap multiple fault modes.
- Safety procedures that are relevant across multiple failures.
- Maintenance guides that support individual fault procedures.
- Restart and post-failure verification procedures.
- Cross-document information that may require the retriever to return more than one document category.

## Structure

- `sops/` — primary failure response procedures.
- `diagnostics/` — symptom and diagnostic interpretation.
- `safety/` — safety and isolation guidance.
- `maintenance/` — supporting maintenance procedures.
- `restart/` — return-to-service requirements.

## Important

These documents are synthetic project artifacts created for RAG development and evaluation. They are not real manufacturer procedures, regulatory guidance, or safe operating instructions for physical machinery. Any real deployment would need approved site/manufacturer documentation and safety validation.

## Intended RAG behavior

For a PWF event, retrieval should not only return `SOP-004`; it should be capable of finding supporting documents such as:
- Electrical diagnostics.
- Electrical isolation.
- Inverter maintenance.
- Controlled restart.

The same principle applies to HDF, TWF, and OSF.

## Suggested evaluation questions

Examples:
1. What should be checked when process temperature exceeds 310 K?
2. Which checks distinguish gradual tool degradation from mechanical overstrain?
3. What should happen before restarting after a power fault?
4. What evidence should be preserved for an unexplained failure?
5. Which safety procedure applies before electrical inspection?
6. What should be verified after replacing a worn tool?
7. When should a machine be escalated rather than repeatedly restarted?

The project should eventually evaluate both retrieval quality and final SLM answer quality.

# Screenshot step verification

Each UI change that a user can see must be proven with a screenshot of the **live** surface, not a mock.

## Live load gate (mandatory)

The product must **boot** after every API/UI copy. Fail if:

- `http://2.28.106.22:8642/health` does not return 200 within 8s
- `http://2.28.106.22:9012/?license=…&site=…` stays on “Comprobando pedido” or a white `#root`
- A pod file was overwritten with a workspace module that is missing live imports (`get_job`, `record_job`, …)

Restore from the running image if health dies. Then capture the step.

## Required per step
- One PNG of the actual screen after the action.
- Caption: what was clicked / typed, and the result.
- Pass / fail.

## Where files go
- Images: `_bmad-output/evidence/screenshots/`
- Illustrated write-up: `_bmad-output/solution/` (same epic note)

## How to capture
- Prefer the live URL (here: http://2.28.106.22:9012/).
- Hash routes are allowed (`#wizard`, `#google`, `#packs`, `#connectors`).
- A single idle screenshot is not enough — exercise the control (submit, tab change, write/verify).

## Naming
`NN-short-name.png` in visit order (01, 02, …).

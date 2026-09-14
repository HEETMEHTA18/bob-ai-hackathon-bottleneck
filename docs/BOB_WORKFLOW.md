# IBM Bob Workflow — GridShield AI

## Required principle
Bob IDE is a core engineering tool, not merely a code generator.

## Project setup
1. Open the official submission repository.
2. Verify the hackathon Bob account.
3. Use `/init`.
4. Load `AGENTS.md`, `CONTEXT.md`, `PRD.md`, `TRD.md`, `MODEL.md`.
5. Confirm Bob is operating on the hackathon account.

## Per-feature workflow

PLAN
→ inspect files
→ create plan
→ review

IMPLEMENT
→ modify only required files

TEST
→ run targeted tests

REVIEW
→ code review
→ security check
→ contract check

COMMIT
→ focused commit

## Bob task style
Prefer large coherent engineering tasks.
Avoid dozens of tiny edits.

## Context discipline
Use targeted context mentions for files and directories.
Do not repeatedly paste the entire repository into prompts.

## Team workflow
Each member keeps Bob tasks associated with their workstream.
Export relevant Bob task histories and consumption screenshots into `bob_sessions/`.

## Suggested Bob tasks
### Architecture
"Read @CONTEXT.md @PRD.md @TRD.md. Propose the architecture without modifying code."

### ML
"Implement @MODEL.md for the data structures in @src/contracts/. Run tests and report metrics."

### Backend
"Implement the public API contract in @INTEGRATION.md. Do not change the response schemas."

### Frontend
"Build the Command Center against the API contract. Do not hardcode production data."

### AI
"Implement grounded Copilot using only the structured context returned by the backend."

## Security
Before Bob session export:
- remove secrets
- inspect diffs
- inspect `.env`
- inspect git status

The final repository must not contain credentials.

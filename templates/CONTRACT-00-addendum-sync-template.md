# CONTRACT-00 Addendum — Synchronous Orchestration via spawn-once-send-sync

**Date:** {DATE}
**Status:** {VALIDATION_STATUS}
**Supersedes:** R5 (polling), R15 (auto-announce processing)

---

> Replace all `{PLACEHOLDER}` tokens with your project-specific values before use.

## Discovery

| Primitive | Blocks tool call? | Notes |
|-----------|:-:|-------|
| `sessions_spawn(mode="run")` | ❌ | Fire-and-forget + auto-announce |
| `sessions_spawn(mode="session")` | ❌ | Requires `thread=true` (unavailable on Telegram) |
| `sessions_send(timeoutSeconds=N)` | ✅ | **Synchronous.** Blocks until agent replies or timeout. |

**Key finding:** A `mode="run"` session survives after the initial run completes. It can be reused via `sessions_send` for synchronous sequential tasks.

---

## Pattern: spawn-once-send-sync

```
Phase 0 — Bootstrap worker
  sessions_spawn(mode="run", task="You are a pipeline worker. Acknowledge.", model={WORKER_MODEL}, label="pipeline-worker-v{N}")
  → Creates worker session (async, auto-announce ignored)
  → Save sessionKey to pipeline-state.json

Phase 1..N — Sequential agent dispatch
  For each agent in spawn-matrix:
    1. Build task string from CONTRACT + inputs + agent spec
    2. sessions_send(sessionKey=worker, message=task, timeoutSeconds=agent.timeout)
       → BLOCKS until agent replies
    3. Parse reply → extract output path + status
    4. Run R10a (mechanical validation script)
    5. Do R10b (narrative review — orchestrator LLM)
    6. Update pipeline-state.json (checkpoint)
    7. git commit + push
    8. If FAIL → R4 recovery (re-send to same worker with refined task)
    9. Proceed to next agent

Phase Z — Cleanup
  Pipeline complete → archive worker session
```

---

## Updated Rules

### R3-v2. Sequential Dispatch — Synchronous Send
- ~~Spawn Agent N → wait for completion~~ → **Send task to worker → tool call blocks → receive reply**
- Each `sessions_send` is atomic: task in → result out
- No auto-announce processing needed (R15 deprecated for pipeline context)
- Single worker session handles all agents sequentially (context accumulates in worker if desired)

### R5-v2. Timeout Discipline — Built-in
- `timeoutSeconds` on `sessions_send` replaces polling
- No poll interval, no max polls — the primitive handles it
- If timeout: reply is error → follow R4 recovery

### R15-v2. Auto-Announce — Residual Only
- `sessions_send` still generates auto-announce as side effect (`delivery.mode: "announce"`)
- These are **residual** — the orchestrator already has the reply from the synchronous call
- Orchestrator MUST ignore inter-session messages from the worker sessionKey during pipeline execution
- Filter: if `sourceSession` matches `pipeline-state.json.workerSessionKey` → skip

---

## Anti-compaction Protocol

If the orchestrator session compacts mid-pipeline:

1. **Read** `pipeline-state.json` → find current step, worker sessionKey
2. **Verify** worker session still exists: `sessions_send(sessionKey, "ping", timeoutSeconds=10)`
3. **If alive:** Resume from current step (re-send task or advance to next)
4. **If dead:** Bootstrap new worker → resume from current step
5. **State file is the single source of truth** — not orchestrator memory

---

## Worker Session Considerations

### Single worker vs multiple workers
- **Default: single worker** — simpler, less overhead, sequential by nature
- Worker context accumulates (it "remembers" previous tasks)
- If context bloat is a concern: spawn fresh worker mid-pipeline (state file has checkpoint)

### Model per agent
- The worker uses whatever model was set at spawn time
- To use different models per agent: spawn separate workers per model tier
- Alternative: single Codex worker for all (each task is self-contained with full contract)

### Worker sandbox
- Worker runs in same sandbox as orchestrator
- Has access to repo filesystem (reads inputs, writes outputs)
- Each task must specify input/output paths explicitly

---

## Validation

Test pipeline ({DATE}):
- 5 steps: Echo → Math → File → Chain → Validator
- Single worker session, reused via `sessions_send`
- All synchronous, all passed
- Validator confirmed: 3/3 checks, all_pass: true
- Commit: `{VALIDATION_COMMIT}`

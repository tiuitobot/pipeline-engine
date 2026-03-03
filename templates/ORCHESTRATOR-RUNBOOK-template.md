# Orchestrator Runbook — Synchronous Pipeline Execution

**For:** {ORCHESTRATOR_MODEL} main session (the orchestrator)
**Pattern:** spawn-once-send-sync (CONTRACT-00 addendum)

---

> Replace all `{PLACEHOLDER}` tokens with your project-specific values before use.

## Pre-flight

```
1. Verify inputs exist:
   python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v{N} --init

2. Bootstrap worker:
   sessions_spawn(mode="run", task="You are a pipeline worker for {PROJECT_NAME} v{N}. You will receive tasks sequentially. For each task, execute it fully, write output to the specified path, then reply with JSON: {status, output_path, summary}. Acknowledge.", model={WORKER_MODEL}, label="pipeline-worker-v{N}")

3. Save worker session:
   python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v{N} --set-worker <sessionKey>

4. Commit: "pipeline-v{N}: initialized + worker bootstrapped"
```

## Dispatch Loop

```
WHILE pipeline not complete:

  1. GET NEXT:
     python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v{N} --dispatch
     → Returns JSON with {task, workerSessionKey, agent_number, agent_name}

  2. SEND TO WORKER (synchronous):
     sessions_send(sessionKey=workerSessionKey, message=task, timeoutSeconds=agent.timeout*60)
     → BLOCKS until reply

  3. PARSE REPLY:
     Extract {status, output_path, summary} from reply

  4. RECORD COMPLETION:
     python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v{N} --record-completion --agent-number N --result done --output-path <path>

  5. R10a (mechanical):
     python3 scripts/validate_r10a.py --plugin {R10_PLUGIN} --agent-output <path> --reference-data <path> --agent-number N --output <path>
     python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v{N} --record-r10a --agent-number N --r10a-path <path>

  6. R10b (narrative — orchestrator LLM):
     Read review file, assess quality, write binding directives if needed

  7. COMMIT:
     git add + commit "pipeline-v{N}: Agent {N} {name} done, R10 passed"
     git push

  8. If an Agent 0 code-pause gate exists in your project contract: record the decision in pipeline state before proceeding
```

## Error Recovery

```
IF sessions_send returns timeout:
  1. Check if output file exists on disk (agent may have written before timeout)
  2. If exists → record-completion as done, proceed
  3. If not → re-send task with simplified instructions (R4)
  4. If 3rd failure → mark agent as failed, assess pipeline viability

IF orchestrator compacts:
  1. Read pipeline-state.json → get current_step, workerSessionKey
  2. sessions_send(workerSessionKey, "ping", timeoutSeconds=10)
  3. If alive → resume from current step
  4. If dead → spawn new worker, --set-worker, resume
```

## Post-pipeline

```
1. Verify pipeline-state.json shows "completed"
2. Generate PDF
3. Update key-info.json
4. Commit: "pipeline-v{N}: completed, PDF delivered"
5. Notify {PROJECT_OWNER}
```

## Ignoring Residual Auto-announces

During pipeline execution, auto-announce messages from the worker session will arrive.
These are residual (we already have the reply from sessions_send).
Action: respond with minimal acknowledgment, do NOT re-process.
Filter: sourceSession matches workerSessionKey → skip.

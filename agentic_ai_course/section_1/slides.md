---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #0f172a
color: #f8fafc
style: |
  section {
    font-family: 'Inter', system-ui, sans-serif;
    color: #f8fafc;
  }
  h1 {
    color: #38bdf8;
  }
  h2 {
    color: #fbbf24;
  }
  code {
    background-color: #1e293b;
    color: #34d399;
  }
  pre {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
  }
---

# Agentic AI & Autonomous Coding
## Section 1: The Core Execution Engine

**Joyful School Engineering Masterclass**
Production Architecture for Multi-Agent Systems

---

## Lecture 1.1: Why Copilots Fail at Multi-Step Tasks

### The Single-Turn Asymptotic Ceiling

```
Input: Prompt + Buffer ──► LLM ──► Predicted Code Block
                                         │
                                         ▼
                                 Unverified Output
```

* **Blind Execution:** No awareness of compiler, linter, or runtime exceptions.
* **Context Smearing:** Inability to maintain consistency across 10+ interrelated files.
* **Premature Completion:** Declares victory before unit tests run.

---

## Attention Dilution & "Lost in the Middle"

### U-Shaped Attention Recall Curve

* **Top of Prompt (0 - 5k tokens):** 98% Recall (System Rules)
* **Middle of Prompt (20k - 80k tokens):** **< 45% Recall** (Architectural constraints ignored!)
* **End of Prompt (Recent 5k tokens):** 95% Recall (Immediate turn)

> **Key Rule:** Dumps of entire codebases degrade reasoning accuracy.

---

## The 4 Fundamental Failure Modes of Naive AI Coding

1. **Tool Argument Hallucination:** Inventing non-existent parameters or flags.
2. **State Drift:** Forgetting edge cases from Step 1 by the time Step 4 arrives.
3. **Ungrounded Assumptions:** Assuming libraries exist without inspecting manifests.
4. **Silent Regressions:** Fixing module A while breaking interfaces in module B.

---

## The Solution: Agentic State Machine

```
Input Task ──► [ Planner ] ──► [ Executor ] ──► [ Environment/Tool ]
                                      ▲                  │
                                      │                  ▼
                                      └── [ Verification Gate ]
                                           (Tests / Linters)
```

* **Grounding:** Every action produces concrete stdout/stderr feedback.
* **Deterministic Halting:** Only finishes when programmatic verification passes 100%.

---

## Production Case Study: `img2threejs`

### Autonomous Procedural Three.js Generation Pipeline

```
[ Reference Image ] ──► [ Intake Spec ] ──► [ Staged Code Sculpt ]
                                                    │
                                                    ▼
[ 100% Verified ] ◄── [ Verification Gate ] ◄── [ Playwright Runtime ]
  (Emitted Code)        (SSIM > 0.95 & AST)       (Headless 4-Angle View)
```

* **Zero Binary Bloat:** Emits native TypeScript `THREE.Group` code (4 KB vs 18 MB GLB).
* **Vision-in-the-Loop:** Uses headless Playwright to capture rendered viewports and detect geometry drift.
* **Closed-Loop Self-Healing:** Discrepancies trigger autonomous code revisions before human signoff.

---

## Lecture 1.2: Anatomizing the Core Execution Engine

### The Formal Agent Policy

$$\pi: \mathcal{H}_t \times \mathcal{O}_t \to \mathcal{A}_t$$

* $\mathcal{H}_t$: Execution history (prior message transcript & decisions)
* $\mathcal{O}_t$: Concrete observation from environment (stdout, stderr, exit codes)
* $\mathcal{A}_t$: Action chosen (structured tool call OR final completion)

---

## The 5 Phases of the ReAct Engine

1. **Ingestion:** Compile system rules, available tools, and current history.
2. **Inference:** Foundation model emits structured `tool_calls`.
3. **Validation:** Schema validation intercepts malformed parameters.
4. **Execution:** Dispatch tool against the host OS / isolated sandbox.
5. **Observation Feedback:** Append raw result as `tool` message and loop.

---

## Standard Four-Role Message Hierarchy

```
[System Message]     ──► Immutable core constraints & tool contracts
[User Message]       ──► Goal specification / user instructions
[Assistant Message]  ──► Reasoning trace + tool_calls: [{id, name, args}]
[Tool Message]       ──► Matching tool_call_id + stdout/stderr result
```

> **Strict Rule:** `tool_call_id` must match 1:1, or frontier APIs return HTTP 400.

---

## Halting Mechanics & Guardrails

To prevent infinite loops and runaway billing:

* **Hard Step Limit:** Cap turns (e.g. `max_steps = 12`).
* **Cycle Detection:** Hash tool actions; kill run if identical call repeats 3x.
* **Timeout Budgets:** Strict 30s ceiling on subprocess executions.
* **Error Threshold:** Abort if 3 consecutive tools throw fatal runtime exceptions.

---

## Lecture 1.3: Context Decay & Token Budgeting

### The Quadratic Token Expansion Problem

* Turn 1: `3.5k tokens`
* Turn 2: `5.5k tokens`
* Turn 5: `18.0k tokens`
* Turn 10: `42.0k tokens`

$$\text{Billed Tokens} = \sum_{i=1}^{N} \text{Prefix}_i = \mathcal{O}(N^2 \cdot L)$$

---

## The 3 Memory Tiers of Production Agents

1. **Ephemeral Buffer (Short-Term):**
   * Raw build logs, grep outputs.
   * *Lifetime:* 1 turn. Pruned or truncated immediately.
2. **Working Trajectory (Mid-Term):**
   * Core state: files modified, test status, pending blockers.
   * *Lifetime:* Full task. Stored as dense bullet vectors.
3. **External Artifacts (Long-Term):**
   * Source files, git diffs, reports.
   * *Lifetime:* Persistent on disk. Referenced by path, never in memory.

---

## Deterministic Pruning Techniques

### 1. Head/Tail Log Truncation
* Keep first 30 lines (invocations & root error).
* Keep last 30 lines (exit code & summary).
* Discard middle 5,000 lines of repetitive stack traces.

### 2. Micro-Compaction Threshold
* When context reaches 60% of limit:
* Background compaction collapses turns into:
  `Completed: [X, Y]. Current blocker: [Z]. Next action: [W].`

---

## Lecture 1.4: Hands-on Implementation (`agent.py`)

### The 3 Core Modules of Our Engine

```
┌────────────────────────────────────────────────────────┐
│                      agent.py                          │
│                                                        │
│  [Tool Registry]                                       │
│   ├── read_file(path)                                  │
│   ├── write_file(path, content)                        │
│   └── run_bash(command)                                │
│                                                        │
│  [Execution Engine]                                    │
│   ├── dispatch_tool(name, args)                        │
│   └── run_agent_loop(goal, max_steps=12)               │
└────────────────────────────────────────────────────────┘
```

---

## Run the Lab

```bash
# 1. Navigate to Section 1
cd agentic_ai_course/section_1

# 2. Run the Autonomous Agent
python agent.py "Create math_utils.py with fibonacci and write a pytest"
```

* Zero dependencies beyond standard Python and the model client.
* Real deterministic execution with live cycle detection.

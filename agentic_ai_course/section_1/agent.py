#!/usr/bin/env python3
"""
Section 1: The Core Execution Engine
Lecture 1.4 Hands-on Lab: Zero-Dependency Autonomous Coding Agent
A clean, minimal, production-pattern implementation of a ReAct agentic loop.
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List

# Anthropic Python SDK (or swap with any OpenAI-compatible client)
try:
    from anthropic import Anthropic
except ImportError:
    print("Please install anthropic: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# Ensure ANTHROPIC_API_KEY is present
if not os.environ.get("ANTHROPIC_API_KEY"):
    # Fallback placeholder for demonstration
    pass

client = Anthropic()

# 1. TOOL DECLARATIONS (Anthropic JSON Schema standard)
TOOLS: List[Dict[str, Any]] = [
    {
        "name": "read_file",
        "description": "Read file contents from disk given an absolute or relative path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or overwrite content to a file on disk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Destination file path"},
                "content": {"type": "string", "description": "Complete text content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "run_bash",
        "description": "Execute a shell command in the local environment and capture stdout/stderr.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"}
            },
            "required": ["command"]
        }
    }
]

# 2. DETERMINISTIC TOOL DISPATCHER
def dispatch_tool(name: str, args: Dict[str, Any]) -> str:
    """Safely executes the requested tool and returns truncated string output."""
    try:
        if name == "read_file":
            path = args["path"]
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist."
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                return content[:6000] if len(content) > 6000 else content

        elif name == "write_file":
            path = args["path"]
            content = args["content"]
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Success: Wrote {len(content)} bytes to '{path}'."

        elif name == "run_bash":
            cmd = args["command"]
            res = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = (res.stdout + res.stderr).strip()
            # Truncate large outputs to protect context window
            if len(output) > 4000:
                output = output[:2000] + "\n...[TRUNCATED OUTPUT]...\n" + output[-2000:]
            return output or "(Command executed with no output, exit code: 0)"

        return f"Error: Unknown tool '{name}'."

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Tool Execution Error: {type(e).__name__}: {str(e)}"

# 3. CORE REACT EXECUTION ENGINE
def run_agent_loop(goal: str, max_steps: int = 12) -> None:
    """Executes the autonomous reasoning and action loop until completion."""
    print("=" * 70)
    print(f"[*] Autonomous Agent Initialized")
    print(f"[*] Goal: {goal}")
    print("=" * 70)

    system_prompt = (
        "You are an autonomous senior software engineering agent. "
        "You have direct access to read files, write files, and execute shell commands. "
        "Solve the user's task step-by-step. "
        "Always verify your changes by running tests or shell verification before declaring completion. "
        "When finished, summarize your changes and state that the goal is complete."
    )

    messages: List[Dict[str, Any]] = [
        {"role": "user", "content": goal}
    ]

    action_history_hashes = []

    for step in range(max_steps):
        print(f"\n--- [Cycle {step + 1}/{max_steps}] Querying Model ---")

        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )

        # Check if the model is done (no more tool calls)
        if response.stop_reason != "tool_use":
            print("\n" + "=" * 70)
            print("🎉 TASK COMPLETED BY AGENT")
            print("=" * 70)
            for block in response.content:
                if hasattr(block, "text"):
                    print(block.text)
            return

        # Append assistant reasoning + tool request to history
        messages.append({"role": "assistant", "content": response.content})

        # Process all tool calls emitted in this turn
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[*] Executing Tool: {block.name}")
                print(f"    Arguments: {json.dumps(block.input)}")

                # Cycle detection guardrail
                action_hash = f"{block.name}:{json.dumps(block.input, sort_keys=True)}"
                if action_history_hashes.count(action_hash) >= 3:
                    out = "Error: Repeated action detected 3 times. Stopping repetitive loop."
                else:
                    action_history_hashes.append(action_hash)
                    out = dispatch_tool(block.name, block.input)

                preview = out[:120].replace("\n", " ") + "..." if len(out) > 120 else out
                print(f"    Observation: {preview}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(out)
                })

        # Append tool observations as the user response
        messages.append({"role": "user", "content": tool_results})

    print(f"\n[!] Warning: Agent reached maximum step ceiling ({max_steps}) without terminating.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_goal = " ".join(sys.argv[1:])
    else:
        user_goal = "Create a python script called 'math_utils.py' with a fibonacci function, and verify it with a pytest test."

    run_agent_loop(user_goal)

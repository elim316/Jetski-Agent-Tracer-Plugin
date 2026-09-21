# Jetski Agent Tracer Plugin

![Building Trust Through AI Transparency](assets/hero.png)

A dynamic, LangGraph-style trajectory visualizer for Jetski. This UI plugin renders an agent's real-time workflow as an interactive timeline across three distinct architectural swimlanes:
- **🏃 Actions (Trigger):** User inputs and macro-goals.
- **🧠 Multi-Agent Workflow:** Agent thought processes and routing logic.
- **🔧 Tools & Functions:** Tool executions and subagent invocations.

## ✨ Features

**Reading the trace**
- **Complete coverage:** Renders every step type in the transcript — user prompts (`👤 USER REQUEST`), agent reasoning (`🧠 MAIN AGENT (ROUTER)`), final user-facing answers (`💬 AGENT REPLY` in emerald green), tool calls, subagent delegations, errors, system notices and context checkpoints. Nothing is silently dropped.
- **Plain-English inspector:** Click any node for a human-readable summary of what happened. User prompts are stripped of internal XML envelopes (`<ADDITIONAL_METADATA>`, `<CONTEXT_SUMMARY>`) with an attachment badge (`📎 Attached N image(s)`), and tool parameters render as a labelled list with raw JSON tucked behind an expandable toggle.
- **Result summaries:** Every tool result opens with a one-line answer to "what came back?" plus stat chips (lines read, matching lines/files, user answers, exit status). The raw output stays one click away instead of filling the panel.
- **Timing & bottleneck browser:** Each call shows how long it took, read from the result's own timestamps. Anything over 10s gets a `🐢` badge on the graph, and clicking **Slow (>10s)** in the Session Overview (or pressing `s`) opens a ranked **🐢 Slowest Tool Calls** list so you can jump straight to the slowest steps.
- **Browsable failures:** Failed calls turn red, in-flight calls show amber and dashed, and clicking **⚠ Issues** (or the **Failed** tile in the Overview) opens a **⛔ Failures** panel listing every error with its request number and cause. Failure detection reads each tool's actual status headers (non-zero exit codes, permission denials, no-op edits) rather than naive keyword matching.
- **Truncation honesty:** Content abbreviated in the compact log is flagged, with a one-click "Load full version" that pulls from `transcript_full.jsonl`.

**Navigating**
- **Goal bar:** A sticky strip under the toolbar that always names the request you're looking at — "Request 12 of 63" plus what the agent set out to do — with `‹` `›` steppers and a dropdown to jump to any request.
- **Decluttered timeline scrubber:** A checkpoint pin per user request that automatically slims down on 60+ request traces so pins never fuse together, paired with upper-rim red failure ticks and a top-framed blue viewport window that stays visible over dense clusters.
- **Long gaps marked:** When a session resumes hours or days later, the graph inserts an explicit `⏸ N hours/days later` marker instead of running two different days together.
- **Search with match browser:** Filter by tool name, prompt or thought text; non-matches dim. Step through hits with `‹` `›`, see your position as `7 / 42`, and click the counter to open `🔎 MATCHES` with surrounding context snippets.
- **Keyboard shortcuts:** `←`/`→` move between requests, `/` focuses search, `Enter`/`Shift+Enter` step through matches, `Esc` clears search, `n` jumps to the next failure, `s` opens slowest tool calls, `o` opens the overview, and `?` (or the `⌨` button) opens the in-app shortcut legend.
- **Real-Time Auto-Follow:** Pans to track the newest nodes as the agent works, and backs off automatically when you scroll into history.
- **Jump to Start / End**, zoom controls with Y-axis locking, and **adaptive swimlanes** that dynamically fit the panel height so the top lane is never hidden under the sticky Goal Bar.

**Views**
- **Interactive session overview:** With nothing selected, the side panel reports the whole run — requests, tool calls, clickable **Failed** and **Slow (>10s)** drill-down tiles, total working time, elapsed span, and top tools used.
- **Copy request:** Exports the current request to the clipboard as markdown — what was asked, the agent's plan, every tool call with its duration and outcome, and the agent's final **Answer** — ready to paste into a doc or review.
- **Simple View:** Hides empty router nodes and system/context noise for a clean narrative — ideal for demos. Toggle off to inspect every model round-trip.
- **Macro Summaries:** Contextual grouping boxes summarizing each request turn.
- **Preferences persist** across reloads, and colours follow the host's light or dark theme.


## 🚀 Installation

Because this is packaged as a native Jetski UI Plugin, installation is seamless:

1. Clone this repository into your Jetski plugins configuration directory:
   ```bash
   mkdir -p ~/.gemini/config/plugins
   git clone https://github.com/elim316/Jetski-Agent-Tracer-Plugin.git ~/.gemini/config/plugins/agent-tracer
   ```
   
2. Open your Jetski interface and navigate to the **Settings** menu (or Plugins Marketplace).
3. Click on **Plugins** and look for **agent-tracer-plugin**.
4. Click the toggle switch to turn it **ON**. Jetski will automatically integrate it.
5. In any active conversation, click the **+ (Extensions)** button securely tucked in the chat header, and open **Agent Tracer**!

## 🧪 Architecture

*   **Frontend**: Native HTML/JS heavily extending `vis-network` (Vis.js) to enforce hierarchical physics constraints and programmatic camera movement. Uses `marked.js` to render live agent thought streams.
*   **Bridge**: Uses the native Jetski `preload.js` bridge structure to auto-detect its active host conversation dynamically. Allows developers to swap active IDE chat tabs while seamlessly switching the graphed context.
*   **Backend**: Python local server polling dynamic JSONL workspace transcripts.

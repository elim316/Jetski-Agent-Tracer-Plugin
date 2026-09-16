# Jetski Agent Tracer Plugin

![Building Trust Through AI Transparency](assets/hero.png)

A dynamic, LangGraph-style trajectory visualizer for Jetski. This UI plugin renders an agent's real-time workflow as an interactive timeline across three distinct architectural swimlanes:
- **🏃 Actions (Trigger):** User inputs and macro-goals.
- **🧠 Multi-Agent Workflow:** Agent thought processes and routing logic.
- **🔧 Tools & Functions:** Tool executions and subagent invocations.

## ✨ Features

**Reading the trace**
- **Complete coverage:** Renders every step type in the transcript — user prompts, agent reasoning, tool calls, errors, system notices and context checkpoints. Nothing is silently dropped.
- **Plain-English inspector:** Click any node for a human-readable summary of what happened, with parameters as a labelled list and the raw JSON tucked behind an "Advanced" toggle.
- **Tool results inline:** Each tool node shows not just what was called, but what came back.
- **Errors surfaced:** Failed calls turn red, in-flight calls show amber and dashed, and an **⚠ Issues** button cycles straight through every failure in the trace.
- **Truncation honesty:** Content abbreviated in the compact log is flagged, with a one-click "Load full version" that pulls from `transcript_full.jsonl`.

**Navigating**
- **Timeline scrubber:** A checkpoint pin per user request — click to jump, hover for the prompt text. A blue band shows your current position in the overall trace.
- **Search:** Filter by tool name, prompt or thought text; non-matches dim, and Enter steps through hits.
- **Real-Time Auto-Follow:** Pans to track the newest nodes as the agent works, and backs off automatically when you scroll into history.
- **Jump to Start / End** plus zoom controls with strict Y-axis locking.

**Views**
- **Simple View:** Hides empty router nodes and system/context noise for a clean narrative — ideal for demos. Toggle off to inspect every model round-trip.
- **Macro Summaries:** Contextual grouping boxes summarizing large blocks of related work.
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

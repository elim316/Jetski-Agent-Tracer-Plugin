# Jetski Agent Tracer Plugin

A dynamic, LangGraph-style trajectory visualizer for Jetski. This UI plugin renders an agent's real-time workflow as an interactive timeline across three distinct architectural swimlanes:
- **🏃 Actions (Trigger):** User inputs and macro-goals.
- **🧠 Multi-Agent Workflow:** Agent thought processes and routing logic.
- **🔧 Tools & Functions:** Tool executions and subagent invocations.

## ✨ Features
- **Real-Time Auto-Follow:** Automatically pans the timeline view to track the newest nodes natively as the agent executes them.
- **Interactive Node Inspector:** Click any timeline node to view a beautifully formatted, Markdown-rendered output of the agent's internal thoughts, actions, and raw parameter payloads.
- **Zoom & Panning Controls:** Fully horizontally scrollable with strict Y-axis locking and adjustable zoom slider.
- **Macro Summaries:** Contextual grouping boxes that dynamically calculate bounds to generate high-level summaries of large blocks of related work.

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

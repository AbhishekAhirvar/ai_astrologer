# AI Astrologer - System Architecture

## 1. System Overview

The **AI Astrologer** is a Python-based web application that combines precise Vedic astrology calculations with Generative AI interpretation. It generates industry-standard North Indian charts, detailed planetary tables, and conversational insights.

### High-Level Data Flow

```mermaid
graph TD
    User([User Input]) -->|Name, DOB, Time, Location| UI[Frontend (Gradio)]
    
    subgraph "Core Engine"
        UI -->|Input Data| Controller[app.py Logic]
        Controller -->|Calc Request| Astro[Astrology Engine<br>(backend/astrology.py)]
        Astro -->|SwissEph| Lib[Swiss Ephemeris Lib]
        Lib -->|Planetary Positions| Astro
        Astro -->|Chart Data JSON| Controller
    end

    subgraph "Visualization Layer"
        Controller -->|Chart Data| Renderer[Chart Renderer<br>(backend/chart_renderer.py)]
        Renderer -->|Matplotlib| Images[Chart Images (PNG)]
        Images -->|Display| UI
    end

    subgraph "Intelligence Layer"
        User -->|Chat Query| UI
        UI -->|Query + Chart Ctx| AI[AI Service<br>(backend/ai.py)]
        AI -->|Responses API| OAI[OpenAI GPT-5.2<br>(2026 API)]
        OAI -->|Streamed Prediction| AI
        AI -->|Real-time Response| UI
    end
```

## 2. Component Architecture

### A. Frontend / Controller (`app.py`)
-   **Technology**: [Gradio](https://www.gradio.app/) with customized CSS/Theme.
-   **Role**: Handles user input validation, orchestrates backend calls, manages session state (chart data), and displays results (Images + Chatbot).
-   **Key Features**:
    -   Responsive Tabbed Layout (Birth Chart, Planetary Info, D10, etc.).
    -   "Grounding" logic to keep AI chat focused on astrology.

### B. Astrology Logic (`backend/astrology.py`)
-   **Technology**: [pyswisseph](https://pypi.org/project/pyswisseph/) (Python bindings for Swiss Ephemeris).
-   **Role**: Performs high-precision astronomical calculations.
-   **Key Calculations**:
    -   Exact planetary degrees (Sidereal Zodiac / Lahiri Ayanamsa).
    -   House division (Whole Sign system).
    -   Divisional Charts (Vargas: D9, D10, etc.).
    -   Chara Karakas (Jaimini system).

### C. Visualization Engine (`backend/chart_renderer.py`)
-   **Technology**: `matplotlib` + `PIL` (Python Imaging Library).
-   **Role**: Generates static PNG images of charts.
-   **Design**:
    -   **North Indian Style**: Diamond chart layout.
    -   **Custom Logic**: Algorithms to prevent text overlap (Rashi numbers vs Planets).
    -   **Output**: High-DPI images saved to `generated_charts/`.

### D. AI Intelligence (`backend/ai.py`)
-   **Technology**: OpenAI Responses API (2026 Version).
-   **Model**: `gpt-5.2` (or latest).
-   **Role**: Interprets JSON chart data with streaming conversation history.
-   **Strategy**:
    -   **Responses SDK**: Uses `client.responses.create` with explicit block formatting (`input_text`/`output_text`).
    -   **History Support**: Maintains context by parsing previous content blocks into plain text for re-submission.
    -   **Strict Constraints**: Prompt engineering to force responses under 60 words and first-person suggestions.

---

## 3. Architecture Trade-offs & Comparisons

### 🖥️ Frontend: Gradio vs. React/Next.js

| Feature | **Current: Gradio** | **Alternative: React + FastAPI** | **Trade-off Analysis** |
| :--- | :--- | :--- | :--- |
| **Dev Speed** | 🚀 **Very Fast** | 🐢 Slower (Boilerplate) | Gradio allows rapid prototyping in pure Python. React requires separate frontend/backend codebases. |
| **Customization** | ⚠️ Limited | 🎨 **Unlimited** | Gradio is rigid with layout. React allows pixel-perfect custom designs and interactive JS animations. |
| **Interactivity** | 🔄 Refresh Required | ⚡ **Real-time** | React allows dynamic D3.js interactive charts. Gradio renders static images (server-side). |
| **Maintenance** | ✅ **Low** | ❌ High | One Python file vs full stack ecosystem. |

**Verdict**: Gradio is the correct choice for a data-science/algorithm-heavy MVP where accuracy > fancy UI animations.

### 🌌 Logic: Swiss Ephemeris vs. APIs

| Feature | **Current: SwissEph (Local Lib)** | **Alternative: 3rd Party API (AstrologyAPI)** | **Trade-off Analysis** |
| :--- | :--- | :--- | :--- |
| **Cost** | 💸 **Free** | 💰 Expensive ($$/req) | SwissEph is open source (GPL). APIs charge per chart. |
| **Latency** | ⚡ **Microseconds** | 🐢 Network Latency | Local calculation is instant. APIs require HTTP round-trips. |
| **Reliability** | ✅ **100% Offline** | ⚠️ Internet Dependent | No downtime risk with local libs. |
| **Accuracy** | 🎯 **NASA Std** | ❓ Varies | SwissEph is the gold standard used by professionals. |

**Verdict**: Local SwissEph is superior in every technical aspect (speed, cost, control) compared to using a SaaS API.

### 🧠 AI: OpenAI GPT-5.2 vs. Hugging Face / Ollama

| Feature | **Current: OpenAI GPT-5.2 (2026)** | **Alternative: HF / Ollama** | **Trade-off Analysis** |
| :--- | :--- | :--- | :--- |
| **Reasoning** | 🧠 **Built-in (Reasoning Effort)** | ⚠️ Standard Completion | OpenAI 2026 API allows native reasoning effort control (low/med/high). |
| **Streaming** | ⚡ **Native Block Stream** | 🔄 Server-Sent Events | OpenAI's Responses API provides complex event types (deltas, part_done) for robust UIs. |
| **Cost** | 💰 Pay-per-token (discounted cache) | 💸 Free (HF) / Hardware (Ollama) | OpenAI is paid but offers superior quality and zero infra management. |
| **Latency** | ⚡ **Fastest Streaming** | 🐢 Variable (Inference API) | OpenAI's global infra provides lower TTFT (Time To First Token). |

**Verdict**: OpenAI GPT-5.2's 2026 SDK is the current choice for industry-grade reliability and reasoning capabilities.

### 📊 Visualization: Matplotlib vs. D3.js

| Feature | **Current: Matplotlib (Backend)** | **Alternative: D3.js / Canvas (Frontend)** | **Trade-off Analysis** |
| :--- | :--- | :--- | :--- |
| **Implementation** | 🐍 **Python Native** | 🕸️ Javascript Complex | Keeps all logic in Python. D3.js requires complex JS calculations for coordinates. |
| **Quality** | 🖼️ Static Image | 🖱️ **Interactive** | D3 allows hovering to see degrees, zooming, etc. Matplotlib is just a PNG. |
| **Compatibility** | ✅ Universal (Image) | ⚠️ Browser Dependent | Images work everywhere (emails, reports). JS charts need a browser engine. |

**Verdict**: Matplotlib aligns with the Python-centric architecture. Moving to D3.js would require rewriting the rendering engine in JavaScript.

# 🚚 AI Logistics Dispatch Copilot

> **An Autonomous, Voice-First Dispatch Platform powered by Google Gemini, Deepgram Voice Agent (Nova-3 & Aura), Google OR-Tools, and Supabase PostgreSQL with an ElevenLabs-Inspired Operational Dashboard.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Deepgram](https://img.shields.io/badge/Deepgram-Nova--3_%2B_Aura-13EF93?style=flat&logo=deepgram&logoColor=black)](https://deepgram.com)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-Flash_Latest-8E75B2?style=flat&logo=googlegemini&logoColor=white)](https://aistudio.google.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL_15+-3FCF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Mapbox](https://img.shields.io/badge/Mapbox_GL_JS-v3-000000?style=flat&logo=mapbox&logoColor=white)](https://mapbox.com)

---

## 📌 Executive Summary

Modern logistics dispatch centers struggle under extreme cognitive load: dispatchers juggle dozens of emergency orders, fluctuating driver hours, vehicle volume and payload limits, strict delivery time windows, and urban traffic. Manual dispatching often results in suboptimal fuel usage, delayed deliveries, and exhausted drivers.

**AI Logistics Dispatch Copilot** is a next-generation dispatch operations platform that pairs human dispatchers with an **autonomous multimodal AI copilot**. Through **real-time bi-directional voice** (Deepgram Nova-3 Speech-to-Text and Aura Text-to-Speech) or conversational chat, dispatchers issue high-level instructions (e.g. *"Assign high-priority medical deliveries in Scarborough to Marcus Vance and optimize his route"*). 

The Copilot parses dispatcher intent using **Google Gemini**, queries live fleet telematics via the **Model Context Protocol (MCP)**, executes mathematical Vehicle Routing Problem (VRP) optimization with **Google OR-Tools** and **OSRM**, persists state in **Supabase PostgreSQL**, and renders actionable recommendation cards alongside interactive **Mapbox GL JS** route visualizations.

---

## 🏗️ System Architecture

The platform follows an event-driven, service-oriented architecture designed around decoupled domain layers, asynchronous voice/LLM pipelines, and resilient database pooling:

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React 19 + TypeScript + Vite)"]
        UI["ElevenLabs Warm Dark Interface"]
        VoiceIn["Deepgram Nova-3 Microphone Capture"]
        VoiceOut["Deepgram Aura TTS Audio Playback"]
        Map["Mapbox GL JS Geospatial Canvas"]
        Cards["Actionable Recommendation Cards"]
    end

    subgraph Backend["FastAPI Backend (Python 3.12+)"]
        MW["Middleware Onion (CORS -> ApiKey -> AgentRequestLog)"]
        Routes["REST & Voice API Router (/api/v1)"]
        
        subgraph AI["Intelligent Agent Layer"]
            VoiceSvc["Deepgram Voice Service (Nova-3 + Aura)"]
            IntentRouter["Intent Classifier & State Engine"]
            Gemini["Google Gemini Reasoner (gemini-flash-latest)"]
            MCP["MCP Tool Registry (Model Context Protocol)"]
        end

        subgraph CoreEngine["Operations & Optimization Engine"]
            BizOrders["Orders & Import Service (Upsert & Batch)"]
            BizPlan["Dispatch Planning Service"]
            BizRec["Recommendation Engine"]
            ORTools["Google OR-Tools VRP Solver"]
            OSRM["OSRM Distance & ETA Matrix Engine"]
        end
        
        subgraph DataLayer["Persistence & Storage"]
            SQLAlchemy["SQLAlchemy 2.0 ORM (Pool Pre-Ping & Recycle)"]
        end
    end

    subgraph External["External Cloud Infrastructure"]
        SupaDB[("Supabase PostgreSQL Database")]
        DeepgramCloud["Deepgram Cloud (Nova-3 STT / Aura TTS)"]
        GeminiCloud["Google AI Studio API"]
        MapboxTiles["Mapbox Vector Tile Services"]
    end

    UI -->|"User Commands / Chat"| Routes
    VoiceIn -->|"Audio Streams / Speech"| Routes
    Routes --> MW
    MW --> Routes
    Routes --> VoiceSvc
    VoiceSvc <--> DeepgramCloud
    Routes --> IntentRouter
    IntentRouter --> Gemini
    Gemini <--> GeminiCloud
    Gemini -->|"Tool Execution"| MCP
    MCP --> BizOrders & BizPlan & BizRec
    BizPlan --> ORTools & OSRM
    BizOrders & BizPlan --> SQLAlchemy
    SQLAlchemy <--> SupaDB
    Routes -->|"TTS Audio Buffer"| VoiceOut
    Routes -->|"Real-time State / GeoJSON"| Map
    Routes -->|"Recommendation Payload"| Cards
    Map <--> MapboxTiles
```

---

## 🎙️ Bi-Directional Voice Pipeline Architecture

The platform integrates Deepgram's cutting-edge speech models to achieve near-instantaneous voice dispatch operations:

```mermaid
sequenceDiagram
    autonumber
    actor Dispatcher
    participant Browser as React Audio Recorder
    participant VoiceAPI as FastAPI /voice Route
    participant Deepgram as Deepgram Cloud (Nova-3 & Aura)
    participant Copilot as Gemini Agent & MCP Tools
    participant AudioPlayer as Web Audio Player

    Dispatcher->>Browser: Speaks command: "Assign order ORD-2001 to Marcus Vance"
    Browser->>VoiceAPI: POST /api/v1/voice/transcribe (Audio Blob)
    VoiceAPI->>Deepgram: Nova-3 General Speech-to-Text API
    Deepgram-->>VoiceAPI: Transcribed Text: "Assign order ORD-2001 to Marcus Vance"
    VoiceAPI->>Copilot: Dispatch intent & invoke MCP tools
    Copilot->>Copilot: Execute assign_orders_to_driver & check capacity
    Copilot-->>VoiceAPI: Copilot response text & updated route cards
    VoiceAPI->>Deepgram: Aura Text-to-Speech API (aura-asteria-en)
    Deepgram-->>VoiceAPI: Synthesized MP3 Audio Stream
    VoiceAPI-->>Browser: Audio Stream + JSON Cards Payload
    Browser->>AudioPlayer: Plays natural voice response with animated waveform
    Browser->>Dispatcher: "Assigned order ORD-2001 to Marcus Vance. Van payload is at 45% capacity."
```

---

## ⚙️ Technology Stack Breakdown

| Domain | Technology | Version | Purpose / Architecture Role |
| :--- | :--- | :--- | :--- |
| **Frontend UI/UX** | **React** | `19.0.0` | Ultra-modern concurrent UI rendering |
| | **TypeScript** | `5.7.2` | End-to-end type safety for orders, drivers, and recommendations |
| | **Vite** | `6.2.0` | Fast HMR development and production asset bundling |
| | **Tailwind CSS** | `3.4.17` | ElevenLabs-inspired aesthetic: warm dark ink (`#0c0a09`), atmospheric pastel glow orbs, hairline borders |
| | **Lucide React** | `0.475.0` | High-fidelity iconography for logistics operations |
| | **Framer Motion** | `12.4.7` | Smooth layout transitions, slide-over modals, and activity timelines |
| | **Mapbox GL JS** | `3.10.0` | Interactive WebGL vector map with custom driver markers, stops, and route polylines |
| **Backend Framework** | **FastAPI** | `0.115.8` | High-performance asynchronous REST API framework |
| | **Python** | `3.12+ / 3.13` | Modern Python with static typing and asynchronous coroutines |
| | **Uvicorn** | `0.34.0` | Production ASGI web server |
| **Voice AI & Speech** | **Deepgram Nova-3** | `v1` | Industry-leading speech-to-text with logistics domain accuracy |
| | **Deepgram Aura** | `aura-asteria-en` | Human-like, natural expressive voice synthesis |
| **Large Language Model** | **Google Gemini** | `gemini-flash-latest` | Ultra-low latency reasoning, intent classification, and MCP tool generation |
| **Database & ORM** | **Supabase PostgreSQL** | `15+` | Scalable cloud relational database with native UUID and JSONB support |
| | **SQLAlchemy** | `2.0.38` | Modern declarative ORM with connection pooling, recycling, and pre-ping |
| | **Psycopg** | `3.2.4` | High-performance asynchronous and binary PostgreSQL driver |
| **Mathematical Optimization** | **Google OR-Tools** | `9.12` | Constraint-satisfaction Vehicle Routing Problem (VRP) solver |
| | **OSRM** | `v1` | Open Source Routing Machine for real-world driving distance and ETA calculation |
| **Data Ingestion** | **OpenPyXL** | `3.1.5` | High-throughput Excel (.xlsx) parsing |
| | **Python CSV Engine** | Standard Lib | UTF-8-BOM compliant, streaming CSV batch reader with upsert idempotency |

---

## 🔄 End-to-End User Flow

```mermaid
graph TD
    A[1. Ingestion: Drag & Drop CSV / Excel] --> B[2. Spatial Clustering: Orders Plotted on Mapbox]
    B --> C[3. Voice / Natural Language Prompting]
    C --> D[4. Gemini Agent Intent Analysis & MCP Tool Selection]
    D --> E[5. Capacity & Time Window Constraint Validation]
    E --> F[6. Google OR-Tools Route Optimization]
    F --> G[7. Interactive Recommendation Cards Rendered]
    G --> H[8. Dispatcher Accepts / Modifies Plan]
    H --> I[9. Route Polylines Updated & Deepgram Speaks Confirmation]
```

### 1. Ingestion & Order Intake
- Dispatcher uploads a CSV or Excel batch file (e.g., `sample_orders.csv`).
- **Upsert Idempotency**: If external order IDs already exist, the backend updates payloads and stop coordinates rather than crashing with duplicate key errors.
- Both pickup and drop-off coordinates, volume ($m^3$), weight ($kg$), time windows, and white-glove/curbside requirements are parsed and stored.

### 2. Fleet Telemetry & Geospatial Clustering
- Active drivers (e.g. Marcus Vance, Sarah Chen, David Ross) display live vehicle assignments (Cargo Van, Box Truck, Electric Sprinter) with real-time remaining capacities.
- **Mapbox GL JS** plots pickup nodes (emerald markers), drop-off destinations (sky markers), and driver positions (amber badges) across the Greater Toronto Area (or configured operational region).

### 3. Voice Interaction via Deepgram
- Dispatcher clicks the microphone or uses hands-free voice input.
- Speech is streamed to **Deepgram Nova-3**, transcribed with sub-second latency, and routed to the Copilot.
- Alternatively, dispatchers type freeform natural language prompts like:
  - *"Show me all unassigned high priority medical orders."*
  - *"Assign ORD-2001 and ORD-2002 to Marcus Vance and minimize driving time."*
  - *"Optimize routes for today considering vehicle weight limits."*

### 4. Autonomous Reasoning & Tool Calling (MCP)
- The Gemini Copilot dynamically selects from a rich registry of dispatch tools:
  - `list_orders`: Inspects current orders and filter criteria.
  - `assign_orders_to_driver`: Validates vehicle qualification and assigns orders.
  - `optimize_routes`: Invokes Google OR-Tools to solve the VRP with pickup/delivery constraints.
  - `generate_recommendations`: Analyzes route bottlenecks and proposes efficiency trade-offs.

### 5. Interactive Cards & Human-in-the-Loop Oversight
- Rather than opaque text, the copilot presents structured **Interactive Cards**:
  - **Route Cards**: Showing order sequence, total travel distance (km), estimated completion time (ETA), and vehicle capacity utilization bar.
  - **Recommendation Cards**: Actionable suggestions with "Accept" and "Undo" buttons.
  - **Summary Cards**: Visual statistics highlighting cost savings and delivery time reductions.

### 6. Natural Voice Response (Deepgram Aura)
- Deepgram Aura generates spoken audio feedback (e.g., *"Assigned 2 orders to Marcus Vance. Route travel time is approximately 42 minutes."*).
- An animated ElevenLabs-style audio waveform activates during speech playback.

---

## 🗄️ Database Schema & Data Models

The relational database architecture is hosted on **Supabase PostgreSQL** and structured around clean relational foreign keys:

```mermaid
erDiagram
    DRIVERS ||--o{ DRIVER_VEHICLE_ASSIGNMENTS : has
    VEHICLES ||--o{ DRIVER_VEHICLE_ASSIGNMENTS : assigned_to
    DRIVERS ||--o{ DRIVER_DELIVERY_TYPES : qualifies_for
    DELIVERY_TYPES ||--o{ DRIVER_DELIVERY_TYPES : requires
    DELIVERY_TYPES ||--o{ ORDERS : specifies
    ORDER_IMPORTS ||--o{ ORDERS : contains
    ORDERS ||--o{ STOPS : includes
    DISPATCH_SESSIONS ||--o{ ROUTES : owns
    DRIVERS ||--o{ ROUTES : drives
    VEHICLES ||--o{ ROUTES : operates
    ROUTES ||--o{ ROUTE_STOPS : executes
    ORDERS ||--o{ ROUTE_STOPS : fulfills
    DISPATCH_SESSIONS ||--o{ RECOMMENDATIONS : evaluates

    DRIVERS {
        uuid id PK
        text full_name
        text phone
        driver_status status
        numeric current_latitude
        numeric current_longitude
    }

    VEHICLES {
        uuid id PK
        text label
        vehicle_status status
        numeric capacity_weight_kg
        numeric capacity_volume_m3
    }

    ORDERS {
        uuid id PK
        text external_order_id UK
        uuid import_id FK
        uuid delivery_type_id FK
        order_status status
        int priority
        text customer_name
        numeric required_weight_kg
        numeric required_volume_m3
    }

    STOPS {
        uuid id PK
        uuid order_id FK
        stop_kind kind
        text address_line1
        text city
        numeric latitude
        numeric longitude
    }

    ROUTES {
        uuid id PK
        uuid session_id FK
        uuid driver_id FK
        uuid vehicle_id FK
        route_status status
        numeric total_distance_km
        numeric total_duration_minutes
    }
```

---

## 📡 API Reference & Voice Agent Endpoints

### Voice Endpoints (`/api/v1/voice`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/voice/status` | Verifies Deepgram API connectivity and configured models (`nova-3-general`, `aura-asteria-en`). |
| `GET` | `/api/v1/voice/tools` | Returns JSON schema of all MCP dispatch tools exposed to voice calling. |
| `POST` | `/api/v1/voice/transcribe` | Ingests audio files/blobs and returns high-accuracy Nova-3 transcription. |
| `POST` | `/api/v1/voice/speak` | Synthesizes input text into high-fidelity Aura MP3 audio stream. |
| `POST` | `/api/v1/voice/chat` | End-to-end voice loop: accepts dispatcher audio, transcribes, invokes Gemini, runs MCP tools, and returns both synthesized speech audio and response payload. |

### Core Dispatch Endpoints (`/api/v1`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/{session_id}` | Returns real-time aggregate fleet telemetry, active orders, drivers, and routes. |
| `POST` | `/api/v1/chat` | Main conversational copilot endpoint: processes natural language requests with Gemini. |
| `POST` | `/api/v1/orders/import` | High-throughput CSV/Excel batch order ingestion with upsert idempotency. |
| `POST` | `/api/v1/recommendations/{id}/accept` | One-click application of AI-generated optimization recommendations. |
| `POST` | `/api/v1/sessions/{id}/reset` | Restores workspace state to fresh dispatch baseline. |

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- **Python**: `3.12` or `3.13`
- **Node.js**: `v20+` or `v22+` with `npm`
- **Supabase Account**: With a PostgreSQL database instance
- **Google AI Studio API Key**: For Gemini LLM
- **Deepgram API Key**: For Nova-3 STT and Aura TTS
- **Mapbox Public Token**: For WebGL map tiles

---

### 1. Repository Setup

```bash
git clone https://github.com/Meenu565/logisticsGDC.git
cd logisticsGDC
```

---

### 2. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd apps/api
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # macOS / Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Configure environment variables (`apps/api/.env`):
   ```env
   APP_NAME="Smart Dispatcher Chatbot API"
   ENVIRONMENT=local
   API_V1_PREFIX="/api/v1"

   # Supabase Database Connection URI
   DATABASE_URL="postgresql+psycopg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

   # CORS Allowed Origins
   BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
   LOG_LEVEL=INFO

   # Google Gemini API
   GEMINI_API_KEY="your-gemini-api-key"
   GEMINI_MODEL="gemini-flash-latest"

   # Deepgram Voice Agent
   DEEPGRAM_API_KEY="your-deepgram-api-key"
   DEEPGRAM_VOICE_MODEL="aura-asteria-en"
   DEEPGRAM_STT_MODEL="nova-3-general"
   ```

5. Run database migrations & seed baseline drivers:
   ```bash
   python -m scripts.migrate
   ```

6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *Interactive API Swagger Docs: `http://localhost:8000/docs`*

---

### 3. Frontend Setup (React 19 + Vite)

1. In a new terminal, navigate to the frontend directory:
   ```bash
   cd apps/web
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Configure environment variables (`apps/web/.env`):
   ```env
   VITE_API_BASE_URL="http://localhost:8000/api/v1"
   VITE_MAPBOX_TOKEN="your_mapbox_public_token"
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser.*

---

## 🧪 Testing the End-to-End Pipeline

1. **Upload Orders**: Drag and drop `sample_orders.csv` (included at root) into the chat area. The copilot automatically loads 6 realistic orders across Toronto, Etobicoke, and Scarborough.
2. **Explore Mapbox**: Watch pickup points, delivery locations, and driver positions populate on the map.
3. **Voice Command**: Click the microphone icon in the chat input and say:
   > *"What orders are currently pending, and which driver has the most available capacity?"*
4. **Autonomous Route Generation**: Type or speak:
   > *"Assign high priority orders to Marcus Vance and optimize the route for fastest delivery."*
5. **Accept Recommendations**: Click **"Accept"** on the generated interactive card to apply the optimized dispatch plan directly to the database.

---

## 🛡️ Production Resilience & Engineering Highlights

- **Starlette Middleware Onion & CORS Hardening**: Built with an outermost `CORSMiddleware` layer and global exception catching, ensuring that even unhandled exceptions return standard JSON payloads with full CORS headers to prevent browser fetch blocking.
- **Supabase Cloud Connection Resilience**: SQLAlchemy engine initialized with `pool_pre_ping=True`, `pool_recycle=300`, and connection pool sizing to prevent dropped connections over remote cloud boundaries.
- **Idempotent Ingestion**: Handles duplicate external order IDs gracefully with safe transaction rollbacks and upsert semantics.
- **Model Context Protocol (MCP)**: Implements structured, typed tool specifications enabling Gemini to plan, query, assign, and optimize deterministically without hallucinations.

---

## 👩‍💻 Author & Acknowledgements

- **Repository**: [https://github.com/Meenu565/logisticsGDC](https://github.com/Meenu565/logisticsGDC)
- **Built for**: Google Developer Competition / Advanced AI Logistics Evaluation
- **Inspired by**: ElevenLabs Design System (`awesome-design-md`)

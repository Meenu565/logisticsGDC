# 🚚 AI Logistics Dispatch Copilot

An AI-powered logistics dispatch platform that streamlines order planning, driver assignment, and route optimization through a conversational interface. By combining Large Language Models (LLMs), optimization algorithms, and geospatial routing, the system assists dispatchers in making faster, data-driven operational decisions while maintaining full control over the final dispatch plan.

---

## 📌 Overview

Modern logistics operations require balancing multiple constraints including delivery priorities, vehicle capacities, driver availability, shift schedules, and travel times. Manual dispatch planning can quickly become inefficient as operational complexity grows.

AI Logistics Dispatch Copilot is designed to simplify this process through an intelligent conversational interface that understands natural language requests, generates optimized dispatch plans, and presents actionable recommendations to dispatchers.

The platform integrates conversational AI with mathematical optimization to automate planning while ensuring flexibility, transparency, and human oversight throughout the decision-making process.

---

## ✨ Key Features

- 🤖 AI-powered conversational dispatch assistant
- 🚚 Intelligent driver and vehicle assignment
- 🗺️ Route optimization using Google OR-Tools
- 📍 Distance and ETA estimation using OSRM
- 📦 CSV & Excel order import
- 💡 AI-generated dispatch recommendations
- 📊 Interactive dispatch dashboard
- 🗂️ Session and conversation management
- 🔄 Modular AI tool orchestration using the Model Context Protocol (MCP)

---

# 🏗️ System Architecture

```text
                           Dispatcher
                                │
                                ▼
                  React + TypeScript Frontend
                                │
                         REST API Requests
                                │
                                ▼
                        FastAPI Backend
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       Gemini AI Agent    Planning Engine    PostgreSQL
              │
              ▼
         MCP Tool Layer
              │
              ▼
     Business Services & Repositories
              │
              ▼
 Google OR-Tools + OSRM Routing Engine
```

---

# 🤖 AI Workflow

```text
Dispatcher Request
        │
        ▼
Intent Detection
        │
        ▼
Google Gemini
        │
        ▼
MCP Tool Selection
        │
        ▼
Business Services
        │
        ▼
Optimization Engine
        │
        ▼
Dispatch Plan + Recommendations
        │
        ▼
Dashboard & Chat Response
```

The AI assistant interprets dispatcher requests, identifies the appropriate operational workflow, invokes the required MCP tools, and coordinates backend services to generate optimized dispatch plans and recommendations.

---

# 🚚 Route Optimization Workflow

```text
Imported Orders
       │
       ▼
Planning Service
       │
       ▼
Dispatch Strategy Selection
(Fastest / Shortest / Balanced)
       │
       ▼
Capacity Validation
       │
       ▼
Shift & Time Window Validation
       │
       ▼
Google OR-Tools Optimization
       │
       ▼
OSRM Route Estimation
       │
       ▼
Optimized Dispatch Plan
       │
       ▼
Recommendation Engine
```

---

# ⚙️ Technology Stack

| Layer | Technologies |
|--------|--------------|
| **Frontend** | React, TypeScript, Tailwind CSS, Vite |
| **Backend** | FastAPI, Python |
| **Database** | PostgreSQL, SQLAlchemy |
| **Artificial Intelligence** | Google Gemini, Model Context Protocol (MCP) |
| **Optimization** | Google OR-Tools |
| **Routing** | Open Source Routing Machine (OSRM) |
| **Deployment** | Docker |

---

# 📂 Project Structure

```text
AI-Logistics-Dispatch-Copilot
│
├── apps
│   ├── api
│   │   ├── agent
│   │   ├── api
│   │   ├── services
│   │   ├── repositories
│   │   ├── optimization
│   │   ├── mcp
│   │   └── models
│   │
│   └── web
│       ├── components
│       ├── pages
│       ├── hooks
│       └── services
│
├── database
├── infra
├── scripts
└── README.md
```

---

# 🧠 Core Components

### AI Agent

Handles conversational interactions, intent recognition, tool orchestration, and response generation using Google Gemini.

### MCP Tool Layer

Acts as the bridge between the AI model and backend capabilities by exposing operational tools such as order management, planning, recommendation generation, and dispatch utilities.

### Planning Engine

Generates optimized dispatch plans while considering:

- Delivery priorities
- Vehicle capacities
- Driver availability
- Shift schedules
- Time windows
- Operational constraints

### Recommendation Engine

Compares alternative dispatch plans and generates actionable recommendations to improve operational efficiency.

---

# 🚀 Getting Started

## Backend

```bash
cd apps/api

pip install -r requirements.txt

uvicorn app.main:app --reload
```

## Frontend

```bash
cd apps/web

npm install

npm run dev
```

---

# 🔮 Future Enhancements

- Live traffic-aware routing
- Real-time GPS driver tracking
- Multi-depot fleet optimization
- Predictive dispatch recommendations
- Fleet performance analytics
- AI-powered delivery delay prediction
- Enhanced operational dashboards

---

# 📖 Design Principles

The project follows a modular service-oriented architecture to improve maintainability, scalability, and separation of concerns.

Key architectural principles include:

- Repository Pattern for database abstraction
- Service Layer for business logic
- Modular API design using FastAPI
- Model Context Protocol (MCP) for AI tool orchestration
- Clear separation between frontend, backend, AI, and optimization services

---

# 👩‍💻 Author

**Srushti Madalgi**

AI & Machine Learning Engineering Student

GitHub: https://github.com/srushtimadalgi

---

## ⭐ Project Goal

This project explores the intersection of Artificial Intelligence, route optimization, and modern logistics systems by combining conversational AI with optimization algorithms to build an intelligent dispatch assistant capable of supporting real-world logistics operations.

# Smart Dispatch Copilot

AI-first dispatch copilot with a React/Vite frontend, FastAPI backend, PostgreSQL database, Gemini orchestration, MCP tools, and Mapbox maps.

## What You Need

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 or Docker
- A Gemini API key
- A Mapbox public access token

## Required Keys And Tokens

Backend:

- `GEMINI_API_KEY` is required for real AI chat responses.
- `DATABASE_URL` is required so FastAPI can connect to PostgreSQL.
- `BACKEND_API_KEY` is optional. Leave it empty unless you want API-key protection.

Frontend:

- `VITE_API_BASE_URL` should point to the backend API.
- `VITE_MAPBOX_TOKEN` is required for the map to render fully.
- `VITE_API_KEY` is optional. Only set it if `BACKEND_API_KEY` is enabled.

Create `apps/web/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_MAPBOX_TOKEN=your_mapbox_public_token_here
```

Check `apps/api/.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/smart_dispatcher
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
BACKEND_API_KEY=
```

Do not commit real API keys.

## Run With Docker

Use this if Docker is installed.

```powershell
docker compose -f infra\docker-compose.yml up -d postgres
```

Apply the database schema:

```powershell
psql "postgresql://postgres:postgres@localhost:5432/smart_dispatcher" -f database\migrations\001_initial_schema.sql
```

Start the backend:

```powershell
cd apps\api
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
cd apps\web
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Run Without Docker

1. Start PostgreSQL locally.
2. Create a database named `smart_dispatcher`.
3. Apply the schema:

```powershell
psql "postgresql://postgres:postgres@localhost:5432/smart_dispatcher" -f database\migrations\001_initial_schema.sql
```

4. Install and run the API:

```powershell
cd apps\api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

5. Install and run the frontend:

```powershell
cd apps\web
npm install
npm run dev
```

## Verify It Works

Backend health:

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/health -UseBasicParsing
```

Frontend:

```text
http://localhost:5173
```

The UI starts without hardcoded sample dispatch data. Import real orders or ask the copilot a question after the backend and database are running.

## Import CSV/Excel Orders

Use the frontend import button, or call the backend endpoint:

```text
POST http://localhost:8000/api/v1/orders/import?session_id=<session_id>
```

Expected CSV/Excel columns include:

- `external_order_id`
- `customer_name`
- `delivery_type`
- `priority`
- `required_weight_kg`
- `required_volume_m3`
- `pickup_address_line1`
- `pickup_city`
- `pickup_latitude`
- `pickup_longitude`
- `dropoff_address_line1`
- `dropoff_city`
- `dropoff_latitude`
- `dropoff_longitude`

Coordinates are needed for map markers. Optimized route geometry is needed for route lines.

## File Structure

Root:

- `.gitignore`: ignored local files such as `.env`, virtualenvs, caches, and Python bytecode.
- `README.md`: this run guide and file-structure reference.
- `apps/`: frontend and backend applications.
- `database/`: database migrations.
- `infra/`: Docker Compose infrastructure.
- `scripts/`: placeholder for future utility scripts.

Infrastructure and database:

- `infra/docker-compose.yml`: starts PostgreSQL, API, and web containers.
- `database/migrations/001_initial_schema.sql`: PostgreSQL schema for sessions, orders, drivers, routes, recommendations, memory, and events.
- `scripts/.gitkeep`: keeps the empty scripts folder in the project.

Backend root:

- `apps/api/.env`: local backend environment variables.
- `apps/api/.gitkeep`: keeps the API folder present.
- `apps/api/Dockerfile`: container image definition for the FastAPI backend.
- `apps/api/pyproject.toml`: Python package metadata and backend dependencies.
- `apps/api/app/__init__.py`: marks the backend app package.
- `apps/api/app/main.py`: FastAPI application entrypoint.

Backend API layer:

- `apps/api/app/api/__init__.py`: API package marker.
- `apps/api/app/api/v1/__init__.py`: v1 API package marker.
- `apps/api/app/api/v1/dependencies.py`: builds shared service dependencies for API routes.
- `apps/api/app/api/v1/router.py`: registers all v1 route modules.
- `apps/api/app/api/v1/routes/__init__.py`: route package marker.
- `apps/api/app/api/v1/routes/chat.py`: chat endpoint.
- `apps/api/app/api/v1/routes/dashboard.py`: dashboard/session state endpoint.
- `apps/api/app/api/v1/routes/drivers.py`: driver endpoints.
- `apps/api/app/api/v1/routes/health.py`: health check endpoint.
- `apps/api/app/api/v1/routes/orders.py`: order list/import/update/cancel endpoints.
- `apps/api/app/api/v1/routes/plans.py`: route optimization and plan summary endpoints.
- `apps/api/app/api/v1/routes/recommendations.py`: recommendation list/accept/apply/reject/undo endpoints.
- `apps/api/app/api/v1/routes/sessions.py`: dispatch session creation endpoint.
- `apps/api/app/api/v1/routes/timeline.py`: dispatch event timeline endpoint.

Backend core and database:

- `apps/api/app/core/__init__.py`: core package marker.
- `apps/api/app/core/auth.py`: backend API key handling.
- `apps/api/app/core/config.py`: application settings loaded from environment.
- `apps/api/app/core/logging.py`: logging configuration.
- `apps/api/app/core/middleware.py`: FastAPI middleware setup.
- `apps/api/app/db/__init__.py`: database package marker.
- `apps/api/app/db/base.py`: SQLAlchemy base model.
- `apps/api/app/db/session.py`: database engine and session factory.

Backend models and schemas:

- `apps/api/app/models/__init__.py`: exports database models.
- `apps/api/app/models/entities.py`: SQLAlchemy entities for drivers, orders, sessions, routes, recommendations, messages, and events.
- `apps/api/app/models/enums.py`: shared enum values.
- `apps/api/app/schemas/__init__.py`: schema package marker.
- `apps/api/app/schemas/chat.py`: Pydantic chat request/response schemas.

Backend repositories:

- `apps/api/app/repositories/__init__.py`: repository exports.
- `apps/api/app/repositories/base.py`: generic repository base class.
- `apps/api/app/repositories/drivers.py`: driver and vehicle data access.
- `apps/api/app/repositories/events.py`: dispatch event data access.
- `apps/api/app/repositories/memory.py`: conversation and memory snapshot data access.
- `apps/api/app/repositories/orders.py`: order, stop, delivery type, and import data access.
- `apps/api/app/repositories/recommendations.py`: recommendation data access.
- `apps/api/app/repositories/routes.py`: plan, route, route stop, and assignment data access.
- `apps/api/app/repositories/sessions.py`: dispatch session data access.

Backend services:

- `apps/api/app/services/__init__.py`: service package marker.
- `apps/api/app/services/business/__init__.py`: business service exports.
- `apps/api/app/services/business/assignments.py`: assignment business logic.
- `apps/api/app/services/business/dashboard.py`: builds dashboard state.
- `apps/api/app/services/business/drivers.py`: driver business logic.
- `apps/api/app/services/business/eta.py`: ETA business logic.
- `apps/api/app/services/business/events.py`: dispatch event recording.
- `apps/api/app/services/business/orders.py`: order import/update/cancel logic.
- `apps/api/app/services/business/planning.py`: optimization planning workflow.
- `apps/api/app/services/business/recommendations.py`: recommendation business actions.
- `apps/api/app/services/business/routes.py`: route and plan summaries.
- `apps/api/app/services/business/sessions.py`: dispatch session creation.

Backend AI, MCP, memory, optimization, and providers:

- `apps/api/app/agent/__init__.py`: agent package marker.
- `apps/api/app/agent/gemini.py`: Gemini orchestration client.
- `apps/api/app/agent/prompt_loader.py`: loads prompt markdown files.
- `apps/api/app/agent/types.py`: agent data types.
- `apps/api/app/agent/prompts/final_response.md`: final response prompt.
- `apps/api/app/agent/prompts/recommendation.md`: recommendation prompt.
- `apps/api/app/agent/prompts/system.md`: system prompt.
- `apps/api/app/agent/prompts/tool_selection.md`: tool selection prompt.
- `apps/api/app/conversation/__init__.py`: conversation package marker.
- `apps/api/app/conversation/orchestrator.py`: main chat orchestration flow.
- `apps/api/app/intent/__init__.py`: intent package marker.
- `apps/api/app/intent/router.py`: intent classification and tool routing.
- `apps/api/app/memory/__init__.py`: memory package marker.
- `apps/api/app/memory/service.py`: conversation memory service.
- `apps/api/app/mcp/client.py`: MCP client helper.
- `apps/api/app/mcp/dependencies.py`: MCP service dependency builder.
- `apps/api/app/mcp/logging.py`: MCP logging helpers.
- `apps/api/app/mcp/registry.py`: MCP tool registry and execution.
- `apps/api/app/mcp/responses.py`: MCP response helpers.
- `apps/api/app/mcp/serializers.py`: serialization helpers.
- `apps/api/app/mcp/server.py`: MCP server registration.
- `apps/api/app/mcp/tools/__init__.py`: MCP tools package marker.
- `apps/api/app/mcp/tools/drivers.py`: driver MCP tools.
- `apps/api/app/mcp/tools/eta.py`: ETA MCP tools.
- `apps/api/app/mcp/tools/health.py`: health MCP tool.
- `apps/api/app/mcp/tools/memory.py`: memory MCP tools.
- `apps/api/app/mcp/tools/orders.py`: order MCP tools.
- `apps/api/app/mcp/tools/planning.py`: planning MCP tools.
- `apps/api/app/mcp/tools/recommendations.py`: recommendation MCP tools.
- `apps/api/app/optimization/__init__.py`: optimization package marker.
- `apps/api/app/optimization/solver.py`: route optimization solver.
- `apps/api/app/optimization/types.py`: optimization data types.
- `apps/api/app/providers/__init__.py`: provider package marker.
- `apps/api/app/providers/types.py`: shared provider types.
- `apps/api/app/providers/geocoding/__init__.py`: geocoding provider package marker.
- `apps/api/app/providers/geocoding/base.py`: geocoding provider interface.
- `apps/api/app/providers/geocoding/null.py`: no-op geocoding provider.
- `apps/api/app/providers/routing/__init__.py`: routing provider package marker.
- `apps/api/app/providers/routing/base.py`: routing provider interface.
- `apps/api/app/providers/routing/osrm.py`: OSRM routing provider.
- `apps/api/app/providers/traffic/__init__.py`: traffic provider package marker.
- `apps/api/app/providers/traffic/base.py`: traffic provider interface.
- `apps/api/app/providers/traffic/null.py`: no-op traffic provider.
- `apps/api/app/recommendations/__init__.py`: recommendation package exports.
- `apps/api/app/recommendations/engine.py`: recommendation generation/decision engine.
- `apps/api/app/recommendations/types.py`: recommendation engine data types.

Frontend root:

- `apps/web/.gitkeep`: keeps the web folder present.
- `apps/web/Dockerfile`: container image definition for the frontend.
- `apps/web/index.html`: Vite HTML entrypoint.
- `apps/web/package.json`: frontend dependencies and scripts.
- `apps/web/package-lock.json`: locked npm dependency versions.
- `apps/web/postcss.config.js`: PostCSS configuration for Tailwind.
- `apps/web/tailwind.config.ts`: Tailwind theme and content config.
- `apps/web/tsconfig.json`: frontend TypeScript config.
- `apps/web/tsconfig.node.json`: TypeScript config for Vite config/runtime files.
- `apps/web/node_modules/`: installed npm dependencies; generated by `npm install`.

Frontend source:

- `apps/web/src/vite-env.d.ts`: Vite TypeScript environment definitions.
- `apps/web/src/main.tsx`: React app bootstrap.
- `apps/web/src/app/App.tsx`: top-level app component.
- `apps/web/src/pages/DispatchWorkspace.tsx`: one-page dispatch copilot layout.
- `apps/web/src/providers/AppProviders.tsx`: TanStack Query provider setup.
- `apps/web/src/services/dispatchApi.ts`: frontend API service layer.
- `apps/web/src/store/useDispatchStore.ts`: Zustand UI synchronization state.
- `apps/web/src/types/dispatch.ts`: frontend dispatch domain types.
- `apps/web/src/lib/utils.ts`: shared frontend utility functions.
- `apps/web/src/styles/globals.css`: global CSS, Tailwind layers, Mapbox marker styles.

Frontend components:

- `apps/web/src/components/chat/ChatCard.tsx`: rich message card rendering.
- `apps/web/src/components/chat/ChatInput.tsx`: chat input, voice input, and file picker.
- `apps/web/src/components/chat/ChatShell.tsx`: chat conversation shell and activity timeline.
- `apps/web/src/components/chat/MessageBubble.tsx`: individual chat message rendering.
- `apps/web/src/components/map/DispatchMap.tsx`: Mapbox map, markers, route layers, and map synchronization.
- `apps/web/src/components/panels/ContextPanel.tsx`: right-side contextual intelligence panel.
- `apps/web/src/components/ui/avatar.tsx`: avatar UI primitive.
- `apps/web/src/components/ui/badge.tsx`: badge UI primitive.
- `apps/web/src/components/ui/button.tsx`: button UI primitive.
- `apps/web/src/components/ui/card.tsx`: card UI primitive.
- `apps/web/src/features/recommendations/RecommendationActions.tsx`: accept/apply/reject/view/undo recommendation actions.

Generated or local-only folders:

- `apps/api/.venv/`: local Python virtual environment; generated locally.
- `.git/`: Git repository metadata.
- `.agents/`: local Codex/agent metadata.

## Common Problems

If the UI loads but chat/dashboard does not work, check PostgreSQL first:

```powershell
Test-NetConnection localhost -Port 5432
```

If this fails, the backend cannot fully work because sessions and chat memory need the database.

If the map area does not render a real map, add `VITE_MAPBOX_TOKEN` to `apps/web/.env` and restart `npm run dev`.

If the backend health endpoint works but session/dashboard requests hang, PostgreSQL is not reachable or the schema has not been applied.

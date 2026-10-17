from fastapi import APIRouter

from app.api.v1.routes import chat, dashboard, drivers, health, orders, plans, recommendations, sessions, timeline, voice

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(voice.router, tags=["voice"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(orders.router, tags=["orders"])
api_router.include_router(drivers.router, tags=["drivers"])
api_router.include_router(plans.router, tags=["plans"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(timeline.router, tags=["timeline"])

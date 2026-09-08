from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, calls, claims, complaints, couriers, dashboard, installations, item_master, market, orders, projects, roles, serials, services, users

app = FastAPI(title="Indcool CRM API", version="0.1.0")
settings.resolved_upload_dir.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(dashboard.router)
app.include_router(complaints.router)
app.include_router(installations.router)
app.include_router(calls.router)
app.include_router(serials.router)
app.include_router(projects.router)
app.include_router(item_master.router)
app.include_router(couriers.router)
app.include_router(orders.router)
app.include_router(claims.router)
app.include_router(market.router)
app.include_router(services.router)
app.mount("/uploads", StaticFiles(directory=str(settings.resolved_upload_dir)), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}

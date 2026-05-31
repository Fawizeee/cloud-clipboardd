from fastapi import APIRouter

from api.v1.auth.login import router as login_router
from api.v1.auth.register import router as register_router
from api.v1.auth.password_reset import router as password_reset_router
from api.v1.auth.refresh import router as refresh_router
from api.v1.auth.verify import router as verify_router
from api.v1.clipboard.routes import router as clipboard_router
from api.v1.sync.routes import router as sync_router
from api.v1.device.routes import router as device_router
from api.v1.websocket.routes import router as websocket_router

router = APIRouter(prefix="/api/v1")

# Auth routes
router.include_router(login_router, prefix="/auth")
router.include_router(register_router, prefix="/auth")
router.include_router(password_reset_router, prefix="/auth")
router.include_router(refresh_router, prefix="/auth")
router.include_router(verify_router, prefix="/auth")

# Feature routes
router.include_router(clipboard_router)
router.include_router(sync_router)
router.include_router(device_router)

# WebSocket (no /api/v1 prefix — mounted at root /api/v1/ws by the router prefix)
router.include_router(websocket_router)

from fastapi import APIRouter
from api.v1.auth.login import router as login_router
from api.v1.auth.register import router as register_router
from api.v1.clipboard.routes import router as clipboard_router
# from api.v1.device import device  # Commented out since device module doesn't exist yet

router = APIRouter(prefix="/api/v1")
router.include_router(login_router, prefix="/auth")
router.include_router(register_router, prefix="/auth")
router.include_router(clipboard_router)
# router.include_router(device, prefix="/device", tags=["device"])

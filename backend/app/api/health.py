from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def get_health():
    """Liveness endpoint"""
    return {"status": "healthy"}

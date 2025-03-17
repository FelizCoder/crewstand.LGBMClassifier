from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
def read_health():
    """
    Check the health status of the application.

    Returns:
        dict: A dictionary containing the health status of the application.
    """
    return {"status": "ok"}

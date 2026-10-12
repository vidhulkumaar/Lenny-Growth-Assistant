from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.schemas.health import HealthStatus

router = APIRouter()

@router.get("/health", response_model=HealthStatus)
def health_check(db: Session = Depends(get_db)):
    """
    Check the health of the application and the database connection.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        # Return 503 Service Unavailable if database is down
        raise HTTPException(status_code=503, detail="Database is unavailable")
        
    return HealthStatus(status="ok", database=db_status)

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.event import UserEvent
from datetime import datetime, timedelta

SURGE_WINDOW_MINUTES = 30
SURGE_THRESHOLD = 5
MAX_SURGE_MULTIPLIER  = 2.0
SURGE_STEP = 0.1

def get_surge_multiplier(product_id : int , db : Session ) -> float:
    since  = datetime.utcnow() - timedelta(minutes = SURGE_WINDOW_MINUTES)
    recent_views = (
        db.query(func.count(UserEvent.id))
        .filter(UserEvent.event_type == "view_product")
        .filter(UserEvent.data.like(f"%product_id:{product_id}"))
        .filter(UserEvent.created_at >= since)
        .scalar()
    )

    if not recent_views or recent_views < SURGE_THRESHOLD:
        surges = recent_views // SURGE_THRESHOLD
        multiplier = 1.0 + (surges * SURGE_STEP)
        return min(multiplier, MAX_SURGE_MULTIPLIER)
def get_surge_price(base_price: float, product_id : int, db : Session) -> dict:
    multiplier = get_surge_multiplier(product_id, db)
    surge_price = round(base_price * multiplier,2)
    is_surging = multiplier > 1.0
    return {
        "base_price": base_price,
        "surge_multiplier": multiplier,
        "surge_price": surge_price,
        "is_surging": is_surging,
        "surge_percentage": round((multiplier - 1.0)* 100,1)
    }

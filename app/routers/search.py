from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_,func
from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductOut
from app.models.event import UserEvent
from app.models.user import User
from app.auth import get_current_user
from typing import List, Optional

router = APIRouter(prefix = "/search", tags = ["search"])

SMART_KEYWORDS = {
    "warm" : ["jacket","coat","wool","sweater","winter"],
    "winter" : ["jacket","coat","boots","gloves","sweater"],
    "summer" : ["shorts","tshirt","sandals","sunglass","cap"],
    "cool" : ["casual","tshirt","shirt","shorts"],
    "formal" : ["shirt","suit","blazer","tie","shoes"],
    "cheap" : ["affordable","basic"],
    "premium" : ["luxury","premium","branded","designer"],
    "comfortable" : ["cotton","casual","soft","relaxed"],
    "running" : ["shoes","track","sport","athletic","smart watch"],
    "gaming" : ["gaming pc","keyboard","playstation","mouse","gaming chair","lights"],
    "powerful" : ["laptop","processor","performance","pro"],
}

def expand_query(q:str)->List[str]:
    terms = [q.lower()]
    words = q.lower().split()
    for word in words :
        if word in SMART_KEYWORDS:
            terms.expand(SMART_KEYWORDS[word])
    return list(set(terms))


@router.get("/",response_model = List[ProductOut])
def search_product(
    q: Optional[str] = Query(None, description= "Search Term"),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("newswet", enum= ["newest", "price_low", "price_high"]),
    page: int = Query (1,ge = 1),
    limit: int = Query (1,le = 50),
    db: Session = Depends(get_db)
):
    
    query = db.query(Product)
    if q:

        expanded_terms = expand_query(q)

        filters = []
        for term in expanded_terms:
            filters.append(Product.name.ilike(f"%{term}%"))
            filters.append(Product.description.ilike(f"%{term}%"))
            filters.append(Product.category.ilike(f"%{term}%"))

        query = query.filter(or_(*filters))

        event = UserEvent(
            user_id = None,
            event_type = "search",
            data = f"query:{q},expanded:{','.join(expanded_terms)}"
        )
        db.add(event)
        db.commit()
    
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    
    if min_price is not None:
        query = query.filter(Product.price>=min_price)
    if max_price is not None:
        query = query.filter(Product.price<=max_price)
    
    if sort_by == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort_by =="price_high":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.id.desc())
    
    offset = (page-1)*limit 
    return query.offset(offset).limit(limit).all()

@router.get("/suggestions")
def search_suggestions(q:str = Query(..., min_length = 1),db : Session = Depends(get_db)):

    popular = (
        db.query(UserEvent.data, func.count(UserEvent.id).label("count"))
        .filter(UserEvent.event_type == "search")
        .filter(UserEvent.data.ilike(f"%query:{q}%"))
        .group_by(UserEvent.data)
        .order_by(func.count(UserEvent.id).desc())
        .limit(5)
        .all()

    )

    suggestions = []
    for p in popular:
        try:
            term = p.data.split("query:")[1].split(",")[0]
            if term not in suggestions:
                suggestions.append(term)
        except:
            pass
    words = q.lower().split()
    for word in words:
        if word in SMART_KEYWORDS:
            suggestions.extend(SMART_KEYWORDS[word][:3])
    return {"query":q,"suggestions":list(set(suggestions))[:8]}

@router.get("/history")
def search_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = (
        db.query(UserEvent)
        .filter(UserEvent.user_id == current_user.id)
        .filter(UserEvent.event_type == "search")
        .order_by(UserEvent.created_at.desc())
        .limit(10)
        .all()
    ) 
    results = []
    for h in history :
        try :
            term = h.data.split("query:")[1].split(",")[0]
            results.append({
                "query":term,
                "searched_at":h.created_at 
            })
        except:
            pass
        return results


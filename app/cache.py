import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(
    host = os.getenv("REDIS_HOST", "localhost"),
    port = int(os.getenv("REDIS_PORT",6379)),
    password = os.getenv("REDIS_PASSWORD",None),
    decode_responses=True
)

def set_cache(key : str, value: dict, ttl: int =60):
    try : 
        r.setex(key,ttl,json.dumps(value))
        return True
    except:
        return False

def get_cache(key:str):
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
        return None
    except:
        return None

def delete_cache(key:str):
    try:
        r.delete(key)
    except:
        pass

def clear_product_cache():
    try :
        keys = r.keys("product:*")
        if keys:
            r.delete(*keys)
    except:
        pass
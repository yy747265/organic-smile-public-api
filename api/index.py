import os
import hmac
from typing import Any, Dict, List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGODB_URI")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

client = AsyncIOMotorClient(MONGO_URI)
db = client.organic_smile


# ---------- الحماية: كل مسارات /admin محتاجة الباسورد ----------
def require_admin(x_admin_key: str = Header(default="")):
    ok = bool(ADMIN_PASSWORD) and hmac.compare_digest(
        x_admin_key.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8")
    )
    if not ok:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------- الموديلات ----------
class Product(BaseModel):
    name: str
    name_en: str = ""
    description: str = ""
    description_en: str = ""
    category: str
    sizes: List[Any] = []
    images: List[str] = []
    isActive: bool = True


class Settings(BaseModel):
    texts: Dict[str, Dict[str, str]] = {}
    ads: Dict[str, List[str]] = {}
    whatsapp: str = ""


def serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


def to_object_id(pid: str) -> ObjectId:
    try:
        return ObjectId(pid)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid product id")


# ---------- مسارات عامة (المتجر) ----------
@app.get("/")
def read_root():
    return {"status": "Public API is running"}


@app.get("/api/products")
async def get_products():
    products = []
    async for doc in db.products.find({"isActive": {"$ne": False}}):
        products.append(serialize(doc))
    return products


@app.get("/api/settings")
async def get_settings():
    doc = await db.settings.find_one({"_id": "site"}, {"_id": 0})
    return doc or {"texts": {}, "ads": {}, "whatsapp": ""}


# ---------- مسارات الأدمن (محمية) ----------
@app.get("/admin/check", dependencies=[Depends(require_admin)])
def admin_check():
    return {"ok": True}


@app.get("/admin/products", dependencies=[Depends(require_admin)])
async def admin_list_products():
    products = []
    async for doc in db.products.find({}):
        products.append(serialize(doc))
    return products


@app.post("/admin/products", dependencies=[Depends(require_admin)])
async def admin_add_product(product: Product):
    result = await db.products.insert_one(product.dict())
    return {"message": "Product added successfully", "id": str(result.inserted_id)}


@app.put("/admin/products/{pid}", dependencies=[Depends(require_admin)])
async def admin_update_product(pid: str, product: Product):
    result = await db.products.update_one({"_id": to_object_id(pid)}, {"$set": product.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}


@app.delete("/admin/products/{pid}", dependencies=[Depends(require_admin)])
async def admin_delete_product(pid: str):
    result = await db.products.delete_one({"_id": to_object_id(pid)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


@app.put("/admin/settings", dependencies=[Depends(require_admin)])
async def admin_save_settings(settings: Settings):
    await db.settings.replace_one({"_id": "site"}, {"_id": "site", **settings.dict()}, upsert=True)
    return {"message": "Settings saved"}

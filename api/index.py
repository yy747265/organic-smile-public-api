import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")

def get_db():
    if not MONGO_URI:
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        return client.organic_smile
    except Exception:
        return None

class Size(BaseModel):
    size: str
    size_en: str = ""
    price: float = None

class Product(BaseModel):
    name: str
    name_en: str = ""
    description: str = ""
    description_en: str = ""
    category: str
    sizes: list[Size] = []
    images: list[str] = []
    isActive: bool = True

class Settings(BaseModel):
    hero_title: str = ""
    hero_title_en: str = ""
    hero_main_img: str = ""
    hero_title_img: str = ""
    custom_offers: list[str] = []
    custom_offers_en: list[str] = []

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Organic Smile API is running"}

@app.get("/api/products")
def get_public_products():
    db = get_db()
    if db is None:
        return []
    try:
        return list(db.products.find({"isActive": True}, {"_id": 0}))
    except Exception:
        return []

@app.get("/api/settings")
def get_settings():
    db = get_db()
    default_settings = {
        "hero_title": "",
        "hero_title_en": "",
        "hero_main_img": "",
        "hero_title_img": "",
        "custom_offers": [],
        "custom_offers_en": []
    }
    if db is None:
        return default_settings
    try:
        settings = db.settings.find_one({}, {"_id": 0})
        return settings if settings else default_settings
    except Exception:
        return default_settings

@app.put("/api/settings")
def update_settings(settings: Settings):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection error")
    db.settings.replace_one({}, settings.dict(), upsert=True)
    return {"message": "تم حفظ الإعدادات بنجاح"}

@app.get("/admin/products")
def get_all_products():
    db = get_db()
    if db is None:
        return []
    try:
        return list(db.products.find({}, {"_id": 0}))
    except Exception:
        return []

@app.post("/admin/products")
def add_product(product: Product):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection error")
    db.products.insert_one(product.dict())
    return {"message": "تم إضافة المنتج بنجاح"}

@app.put("/admin/products/{product_name}")
def update_product(product_name: str, product: Product):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection error")
    result = db.products.replace_one({"name": product_name}, product.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"message": "تم تحديث المنتج بنجاح"}

@app.delete("/admin/products/{product_name}")
def delete_product(product_name: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection error")
    result = db.products.delete_one({"name": product_name})
    if result.deleted_count == 1:
        return {"message": "تم حذف المنتج بنجاح"}
    raise HTTPException(status_code=404, detail="المنتج غير موجود")

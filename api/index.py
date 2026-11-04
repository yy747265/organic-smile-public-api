import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

load_dotenv()

app = FastAPI()

# إعدادات CORS الشاملة لمنع حظر الطلبات
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# الاتصال بقاعدة البيانات
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client.organic_smile
products_collection = db.products
settings_collection = db.settings


# --- Pydantic Schemas ---
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


# --- Endpoints ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Organic Smile API is running"}

@app.get("/api/products")
def get_public_products():
    return list(products_collection.find({"isActive": True}, {"_id": 0}))

@app.get("/api/settings")
def get_settings():
    settings = settings_collection.find_one({}, {"_id": 0})
    if not settings:
        return {
            "hero_title": "",
            "hero_title_en": "",
            "hero_main_img": "",
            "hero_title_img": "",
            "custom_offers": [],
            "custom_offers_en": []
        }
    return settings

@app.put("/api/settings")
def update_settings(settings: Settings):
    settings_collection.replace_one({}, settings.dict(), upsert=True)
    return {"message": "تم حفظ الإعدادات بنجاح"}

@app.get("/admin/products")
def get_all_products():
    return list(products_collection.find({}, {"_id": 0}))

@app.post("/admin/products")
def add_product(product: Product):
    products_collection.insert_one(product.dict())
    return {"message": "تم إضافة المنتج بنجاح"}

@app.put("/admin/products/{product_name}")
def update_product(product_name: str, product: Product):
    result = products_collection.replace_one({"name": product_name}, product.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"message": "تم تحديث المنتج بنجاح"}

@app.delete("/admin/products/{product_name}")
def delete_product(product_name: str):
    result = products_collection.delete_one({"name": product_name})
    if result.deleted_count == 1:
        return {"message": "تم حذف المنتج بنجاح"}
    raise HTTPException(status_code=404, detail="المنتج غير موجود")

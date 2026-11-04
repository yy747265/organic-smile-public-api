import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.organic_smile


class Product(BaseModel):
    name: str
    description: str = ""
    category: str
    sizes: list
    images: list
    isActive: bool = True


@app.get("/")
def read_root():
    return {"status": "Public API is running"}


# مسار جلب المنتجات للمتجر
@app.get("/api/products")
async def get_products():
    try:
        products = []
        cursor = db.products.find({})
        async for document in cursor:
            document["_id"] = str(document["_id"])
            products.append(document)
        return products
    except Exception as e:
        return {"error": str(e)}


# مسارات التحكم للأدمن أونلاين
@app.get("/admin/products")
async def get_admin_products():
    try:
        products = []
        cursor = db.products.find({}, {"_id": 0})
        async for document in cursor:
            products.append(document)
        return products
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/products")
async def add_admin_product(product: Product):
    await db.products.insert_one(product.dict())
    return {"message": "Product added successfully"}


@app.delete("/admin/products/{product_name}")
async def delete_admin_product(product_name: str):
    result = await db.products.delete_one({"name": product_name})
    if result.deleted_count == 1:
        return {"message": "Product deleted successfully"}
    return {"message": "Product not found"}

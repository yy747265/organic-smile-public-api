import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# Enable CORS for storefront access
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


@app.get("/")
def read_root():
    return {"status": "Public API is running"}


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
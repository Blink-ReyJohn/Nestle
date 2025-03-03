from fastapi import FastAPI
from pymongo import MongoClient
from bson.json_util import dumps
import os

app = FastAPI()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17#@concentrix.txv3t.mongodb.net/?retryWrites=true&w=majority&appName=Concentrix")
client = MongoClient(MONGO_URI)
db = client["nestle"]  # Replace with your actual database name
collection = db["users"]  # Replace with your actual collection name

@app.get("/get_user_data/{user_id}")
async def get_user_data(user_id: str):
    user = collection.find_one({"user_id": user_id})
    if user:
        return dumps(user)
    return {"error": "User ID not found"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)

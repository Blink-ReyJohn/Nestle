from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
import os

# Initialize FastAPI
app = FastAPI()

# MongoDB Connection
MONGO_URI = "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17#@concentrix.txv3t.mongodb.net/nestle_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["nestle_db"]
employees_collection = db["employees"]

@app.get("/get_employee/{employee_id}")
async def get_employee(employee_id: str):
    """Fetch employee data from MongoDB"""
    employee = employees_collection.find_one({"_id": employee_id})

    if not employee:
        raise HTTPException(status_code=404, detail="Employee ID not found")

    # Convert ObjectId fields to string
    employee["_id"] = str(employee["_id"])
    return employee

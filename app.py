from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

MONGO_URI = "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17#@concentrix.txv3t.mongodb.net/?retryWrites=true&w=majority&appName=Concentrix"
client = MongoClient(MONGO_URI)
db = client["nestle_db"]
employees_collection = db["employees"]

@app.get("/")
def home():
    return {"message": "API is live"}

@app.get("/testdb")
def test_db():
    try:
        db.list_collection_names()  # Check if MongoDB is accessible
        return {"message": "Connected to MongoDB"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get_employee/{employee_id}")
def get_employee(employee_id: str):
    employee = employees_collection.find_one({"_id": employee_id})
    
    if employee:
        employee["_id"] = str(employee["_id"])  # Convert ObjectId to string
        return employee
    else:
        return {"error": "Employee not found"}

from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
client = MongoClient("mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/nestle_db?retryWrites=true&w=majority&appName=Concentrix")
db = client.nestle_db  # Database
employees = db.employees  # Collection

# Sample user ID
user_id = "20191134120"

# Sample payslip data with job position
payslip_data = {
    "month": "February",
    "year": 2025,
    "job_position": "IT Support Specialist",
    "basic_salary": 50000,
    "allowances": 5000,
    "deductions": 3000,
    "net_salary": 52000,
    "generated_at": datetime.utcnow().isoformat(),
}

# Insert payslip data under the user
result = employees.update_one(
    {"id": user_id},
    {"$set": {"Payslip": payslip_data}},
    upsert=True
)

if result.modified_count > 0 or result.upserted_id:
    print(f"Payslip added for Employee ID: {user_id}")
else:
    print(f"Failed to insert payslip data.")

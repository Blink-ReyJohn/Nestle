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

# Update the employee document with payslip data
result = employees.update_one(
    {"_id": user_id},  # Ensure we query by `_id`, not `id`
    {"$set": {"Payslip": payslip_data}},  # Embed payslip inside employee document
    upsert=False  # Ensure we don't create a new document if the employee doesn't exist
)

if result.modified_count > 0:
    print(f"Payslip added for Employee ID: {user_id}")
else:
    print(f"Failed to insert payslip data. Employee ID may not exist.")

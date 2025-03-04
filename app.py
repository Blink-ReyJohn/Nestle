from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import requests
import random
import string
from datetime import datetime
from dotenv import load_dotenv

app = FastAPI()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/nestle_db?retryWrites=true&w=majority&appName=Concentrix")
client = MongoClient(MONGO_URI)
db = client["nestle_db"]
collection = db["employees"]
hr_requests_collection = db["hr_requests"]

# Load environment variables
load_dotenv()

DEFAULT_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json; charset=utf-8",  # Ensure UTF-8 encoding
}

@app.get("/")
def root():
    return {"message": "API is live"}

@app.get("/testdb")
def test_db():
    try:
        client.admin.command('ping')
        return {"message": "Connected to MongoDB"}
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")

@app.get("/check_employee/{employee_id}")
def check_employee(employee_id: str):
    """Check if an employee exists in MongoDB."""
    try:
        employee = collection.find_one({"_id": employee_id})
        if employee:
            return {"message": "Employee found", "name": employee.get("name", "Unknown")}
        else:
            return {"message": "Employee not found"}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Function to generate a 10-character alphanumeric ID
def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

@app.get("/send_payslip/{employee_id}")
def send_payslip(employee_id: str, apiKey: str = Query(...), category: str = Query(...), details: str = Query(...)):
    """Fetch payslip data, send email, and create HR request under employee's HR_Requests field."""
    
    # Fetch employee data
    employee = collection.find_one({"_id": employee_id}, {"_id": 0, "name": 1, "email": 1, "Payslip": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="No employee found")
    
    if "Payslip" not in employee or not employee["Payslip"]:
        raise HTTPException(status_code=404, detail="No payslip found")

    # Extract employee and payslip details
    recipient = employee["email"]
    employee_name = employee["name"]
    payslip = employee["Payslip"]
    
    # Email content
    month = payslip.get("month", "Unknown")
    year = payslip.get("year", "Unknown")
    subject = f"Your Payslip for {month} {year}"
    body = f"""Dear {employee_name},

    We are pleased to provide you with your payslip for {month} {year}.

    Employee Details:
    - Name: {employee_name}
    - Position: {payslip.get("job_position", "Unknown")}
    - Employee ID: {employee_id}

    Salary Breakdown:
    - Basic Salary: PHP {payslip.get("basic_salary", 0):,.2f}
    - Allowances: PHP {payslip.get("allowances", 0):,.2f}
    - Deductions: PHP {payslip.get("deductions", 0):,.2f}

    Net Salary (Take-Home Pay): PHP {payslip.get("net_salary", 0):,.2f}

    Best regards,  
    HR Team  
    Nestlé Philippines
    """

    # Send email using Brevo API
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        payload = {
            "sender": {"name": "Nestlé HR Team", "email": "reyjohnandraje2002@gmail.com"},
            "to": [{"email": recipient, "name": employee_name}],
            "subject": subject,
            "htmlContent": f"<pre>{body}</pre>"
        }
        headers = DEFAULT_HEADERS
        headers["api-key"] = apiKey
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            # After successfully sending email, create HR request and update employee
            # Generate a new HR request ID
            new_request_id = generate_id()

            # HR request data structure
            new_request = {
                new_request_id: {
                    "category": category,  # Category passed as query parameter
                    "details": details,    # Details passed as query parameter
                    "status": "Completed",  # Set the status as "Completed"
                    "created_at": datetime.utcnow(),  # Timestamp of when the request was created
                    "updated_at": datetime.utcnow()   # Timestamp of the last update
                }
            }

            # Update the employee's HR_Requests field with the new HR request
            collection.update_one(
                {"_id": employee_id},  # Filter by employee ID
                {"$set": {f"HR_Requests.{new_request_id}": new_request[new_request_id]}}  # Add the new HR request to HR_Requests
            )

            # Update the employee's last query and timestamp
            collection.update_one(
                {"_id": employee_id},
                {"$set": {
                    "lastQuery": details,
                    "timestamp": datetime.utcnow()
                }}
            )

            return {"message": f"Payslip email sent to {recipient}. HR request created."}
        else:
            raise HTTPException(status_code=400, detail="Failed to send email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

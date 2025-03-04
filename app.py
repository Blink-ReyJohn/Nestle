from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import smtplib
from email.mime.text import MIMEText
import traceback
import requests
from dotenv import load_dotenv

app = FastAPI()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/nestle_db?retryWrites=true&w=majority&appName=Concentrix")
client = MongoClient(MONGO_URI)
db = client["nestle_db"]
collection = db["employees"]

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

@app.post("/send_payslip/{employee_id}")
def send_payslip(employee_id: str, apiKey: str = Query(...)):
    """Fetch payslip data and send an email via Brevo API."""
    
    # Use the provided API key in the query parameter
    api_key = apiKey
    
    # Fetch employee data from the collection
    employee = collection.find_one({"_id": employee_id}, {"_id": 0, "name": 1, "email": 1, "Payslip": 1})

    # Check if employee exists
    if not employee:
        raise HTTPException(status_code=404, detail="No employee found")
    
    # Check if payslip exists for the employee
    if "Payslip" not in employee or not employee["Payslip"]:
        raise HTTPException(status_code=404, detail="No payslip found")

    # Extract employee and payslip details
    recipient = employee["email"]
    employee_name = employee["name"]
    payslip = employee["Payslip"]

    # Payslip details (same as your current code)
    month = payslip.get("month", "Unknown")
    year = payslip.get("year", "Unknown")
    job_position = payslip.get("job_position", "Unknown")
    basic_salary = payslip.get("basic_salary", 0)
    allowances = payslip.get("allowances", 0)
    deductions = payslip.get("deductions", 0)
    net_salary = payslip.get("net_salary", 0)

    # Email content (UTF-8 encoded)
    subject = f"Your Payslip for {month} {year}"
    body = f"""Dear {employee_name},

    We are pleased to provide you with your payslip for {month} {year}.

    Employee Details:
    - Name: {employee_name}
    - Position: {job_position}
    - Employee ID: {employee_id}

    Salary Breakdown:
    - Basic Salary: PHP {basic_salary:,.2f}
    - Allowances: PHP {allowances:,.2f}
    - Deductions: PHP {deductions:,.2f}

    Net Salary (Take-Home Pay): PHP {net_salary:,.2f}

    Your salary has been processed and credited to your registered bank account. If you have any questions, feel free to reach out.

    Best regards,  
    HR Team  
    Nestlé Philippines
    """

    try:
        url = "https://api.brevo.com/v3/smtp/email"
        payload = {
            "sender": {"name": "Nestlé HR Team", "email": "reyjohnandraje2002@gmail.com"},
            "to": [{"email": recipient, "name": employee_name}],
            "subject": subject,
            "htmlContent": f"<pre>{body}</pre>"  # Keeps formatting
        }

        # Set the API key in the header for the request
        headers = DEFAULT_HEADERS
        headers["api-key"] = api_key

        # Send the email using the API
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return {"success": f"Payslip email sent to {recipient}"}
        else:
            return {"error": response.json()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

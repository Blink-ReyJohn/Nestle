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

# Function to generate a 10-character alphanumeric ID
def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_hr_request(employee_id: str, category: str, details: str, status: str = "Completed"):
    """Create a new HR request for Payroll & Payslip Issues after sending email."""

    # Generate a new 10-character alphanumeric ID
    new_request_id = generate_id()

    # Current timestamp
    current_timestamp = datetime.utcnow()

    # Structure of the HR request
    hr_request = {
        "_id": new_request_id,                      # Use generated ID
        "category": category,                        # Use the category passed as parameter
        "details": details,                          # Use the details passed as parameter
        "status": status,                            # Set the status as Completed
        "created_at": current_timestamp,            # Current timestamp for created_at
        "updated_at": current_timestamp,            # Current timestamp for updated_at
        "employee_id": employee_id                   # Add the employee ID
    }

    try:
        # Insert the new request into the HR requests collection
        result = hr_requests_collection.insert_one(hr_request)
        return {"message": f"HR request created with ID {new_request_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating HR request: {str(e)}")

def update_employee_last_query(employee_id: str, last_query: str):
    """Update the employee's last query and timestamp."""

    # Current timestamp
    current_timestamp = datetime.utcnow()

    # Update the employee's record with the new query and timestamp
    try:
        result = collection.update_one(
            {"_id": employee_id},
            {"$set": {
                "lastQuery": last_query,
                "timestamp": current_timestamp
            }}
        )
        return result.modified_count > 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating employee: {str(e)}")

# After sending payslip email, call this function
def send_payslip_and_create_request(employee_id: str, category: str, details: str):
    # Get the employee's last query (e.g., "Requested VPN access for remote work")
    last_query = details  # Use the provided details as the lastQuery

    # Call the send_payslip_email function (assuming it's already defined)
    email_response = send_payslip(employee_id, apiKey='your_api_key_here')  # Call your email function
    
    if "success" in email_response:
        # If the email is sent successfully, create the HR request and update employee
        hr_request_response = create_hr_request(employee_id, category, details, status="Completed")

        # Update the employee's last query and timestamp
        if update_employee_last_query(employee_id, last_query):
            return {"email_response": email_response, "hr_request_response": hr_request_response}
        else:
            return {"email_response": email_response, "error": "Failed to update employee's last query"}
    else:
        # If email sending failed, do not proceed with HR request creation or employee update
        return {"email_response": email_response}

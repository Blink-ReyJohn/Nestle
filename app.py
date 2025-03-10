from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import requests
import random
import string
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel

app = FastAPI()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/nestle_db?retryWrites=true&w=majority&appName=Concentrix")
client = MongoClient(MONGO_URI)
db = client["nestle_db"]
employees_collection = db["employees"]
hr_requests_collection = db["hr_requests"]
payslips_collection = db["payslips"]
recruitment_collection = db["recruitment"]
finance_requests_collection = db["finance_requests"]
onboarding_collection = db["on-boarding"]
procurement_requests_collection = db["procurement_requests"]

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

# Function to generate a 10-character alphanumeric ID
def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Function to generate a valid 11-digit employee_id
def generate_employee_id():
    return str(random.randint(10000000000, 99999999999))

@app.get("/add_employee")
def add_employee(
    name: str = Query(...),
    job_title: str = Query(...),
    starting_date: str = Query(...)
):
    """Add a new employee with a generated employee_id."""

    try:
        # Generate a unique employee ID
        employee_id = generate_employee_id()

        # Ensure the generated ID is unique
        while employees_collection.find_one({"_id": employee_id}):
            employee_id = generate_employee_id()

        # Check if the employee already exists
        existing_employee = employees_collection.find_one({"name": name})
        if existing_employee:
            raise HTTPException(status_code=400, detail="Employee already exists.")

        # Insert employee data
        employee_data = {
            "_id": employee_id,
            "name": name,
            "job_title": job_title,
            "starting_date": starting_date,
            "created_at": datetime.utcnow()
        }

        employees_collection.insert_one(employee_data)
        return {"message": "Employee added successfully.", "employee_id": employee_id}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@app.get("/check_employee/{employee_id}")
def check_employee(employee_id: str):
    """Check if an employee exists in MongoDB."""
    try:
        employee = employees_collection.find_one({"_id": employee_id})
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
    
    # Store API key in a variable
    api_key_variable = apiKey

    # Fetch employee data
    employee = employees_collection.find_one({"_id": employee_id}, {"_id": 0, "name": 1, "email": 1, "Payslip": 1})
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
        headers["api-key"] = api_key_variable  # Use the apiKey passed in the query param
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
            employees_collection.update_one(
                {"_id": employee_id},  # Filter by employee ID
                {"$set": {f"HR_Requests.{new_request_id}": new_request[new_request_id]}}  # Add the new HR request to HR_Requests
            )

            # Update the employee's last query and timestamp
            employees_collection.update_one(
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

payslip_data = [
    {"month": "February", "year": 2025, "job_position": "IT Support Specialist", "basic_salary": 45000, "allowances": 3000, "deductions": 1200, "net_salary": 45000 + 3000 - 1200},
    {"month": "January", "year": 2025, "job_position": "IT Support Specialist", "basic_salary": 45000, "allowances": 3200, "deductions": 1300, "net_salary": 45000 + 3200 - 1300},
    {"month": "December", "year": 2024, "job_position": "IT Support Specialist", "basic_salary": 45000, "allowances": 3100, "deductions": 1250, "net_salary": 45000 + 3100 - 1250},
    {"month": "November", "year": 2024, "job_position": "IT Support Specialist", "basic_salary": 45000, "allowances": 2800, "deductions": 1150, "net_salary": 45000 + 2800 - 1150},
    {"month": "October", "year": 2024, "job_position": "IT Support Specialist", "basic_salary": 45000, "allowances": 2900, "deductions": 1200, "net_salary": 45000 + 2900 - 1200},
    {"month": "September", "year": 2024, "job_position": "IT Support Specialist", "basic_salary": 45000, "allowances": 3100, "deductions": 1350, "net_salary": 45000 + 3100 - 1350},
]

# Function to delete the existing "Payslip" field from an employee document in the 'employees' collection
def delete_existing_payslip(employee_id: str):
    employees_collection.update_one(
        {"_id": employee_id},
        {"$unset": {"Payslip": ""}}  # Remove the "Payslip" field if it exists
    )
    print(f"Payslip field removed from employee {employee_id}.")

# Function to add new payslips to the 'payslips' collection for a specific employee
def add_payslips_to_new_collection(employee_id: str):
    # Check if the employee exists
    employee = employees_collection.find_one({"_id": employee_id})
    
    if employee:
        # Loop through the payslip data and insert into 'payslips' collection
        for payslip in payslip_data:
            payslip_record = payslip.copy()
            payslip_record["generated_at"] = datetime.utcnow().isoformat()
            payslip_record["employee_id"] = employee_id
            payslip_record["employee_name"] = employee.get("name", "Unknown")  # Add employee name to payslip
            payslips_collection.insert_one(payslip_record)
        print(f"Payslips added to the payslips collection for employee {employee_id}.")
    else:
        print(f"Employee with ID {employee_id} not found. No payslips added.")

# FastAPI route to trigger the deletion of the old payslip field and insertion of new payslip records
@app.post("/add_payslips/{employee_id}")
def add_payslips(employee_id: str, apiKey: str = Query(...)):
    # Store API key in a variable
    api_key_variable = apiKey

    # Check if the employee exists before processing
    employee = employees_collection.find_one({"_id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    try:
        # Delete existing payslip data from the employee document (if any)
        delete_existing_payslip(employee_id)
        # Add the new payslips to the 'payslips' collection
        add_payslips_to_new_collection(employee_id)
        return {"message": f"Payslips added for employee ID {employee_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/check_payslip_month/{employee_id}")
def check_payslip_month(employee_id: str, month: str = Query(...), year: int = Query(...)):
    """Check if a payslip for the given month and year exists for the employee."""
    try:
        # Ensure the month is case-insensitive by converting it to title case
        month = month.strip().capitalize()

        # Find the payslips for the employee and filter by the month and year
        payslip = payslips_collection.find_one(
            {"employee_id": employee_id, "month": month, "year": year}
        )

        if payslip:
            return {"message": f"Payslip found for {month} {year}."}
        else:
            return {"message": f"No payslip found for {month} {year}."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apply_leave/{employee_id}")
def apply_leave(employee_id: str, leave: str = Query(...), leave_starting_date: str = Query(...), leave_ending_date: str = Query(...), category: str = Query(...), details: str = Query(...)):
    """Apply for leave and add the request to HR requests collection."""
    
    # Fetch employee data to ensure the employee exists
    employee = employees_collection.find_one({"_id": employee_id}, {"_id": 0, "name": 1, "email": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Validate the leave parameters
    try:
        # Convert the string dates into datetime objects (DD/MM/YYYY format)
        leave_start = datetime.strptime(leave_starting_date, "%d/%m/%Y")
        leave_end = datetime.strptime(leave_ending_date, "%d/%m/%Y")
        
        # Ensure that the end date is not earlier than the start date
        if leave_end < leave_start:
            raise ValueError("End date cannot be earlier than the start date.")
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    
    # Generate a new HR request ID for the leave request using the provided generate_id function
    new_id = generate_id()  # This will generate the unique document ID for MongoDB
    
    # Convert the leave dates to "Month Day, Year" format
    leave_start_formatted = leave_start.strftime("%B %d, %Y")
    leave_end_formatted = leave_end.strftime("%B %d, %Y")
    
    # Leave application details
    leave_request = {
        "_id": new_id,                 # Generated ID used as the _id for the MongoDB document
        "employee_id": employee_id,    # The employee ID requesting the leave
        "leave_type": leave,           # Type of leave (e.g., vacation, sick, etc.)
        "leave_start": leave_start_formatted,  # Starting date of the leave
        "leave_end": leave_end_formatted,    # Ending date of the leave
        "category": category,          # Category gathered from parameter
        "details": details,            # Details gathered from parameter
        "status": "Submitted",         # Status is set to "Submitted"
        "created_at": datetime.utcnow(),  # Timestamp of when the leave request was created
        "updated_at": datetime.utcnow()   # Timestamp of the last update
    }
    
    # Insert the leave request into the hr_requests collection with custom generated _id
    try:
        # Insert the document with the generated _id
        hr_requests_collection.insert_one(leave_request)
        return {"message": f"Leave request for {leave} from {leave_start_formatted} to {leave_end_formatted} has been submitted."}
    
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/create_onboarding_request")
def create_onboarding_request(
    employee_id: str = Query(...),
    required_access: str = Query("")
):
    """Create an onboarding request for an employee, ensuring no duplicates."""

    try:
        # Ensure 'on-boarding' collection exists
        if "on-boarding" not in db.list_collection_names():
            db.create_collection("on-boarding")

        # Check if the employee exists
        employee = employees_collection.find_one({"_id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found.")

        # Check if an onboarding request already exists for this employee_id
        existing_request = onboarding_collection.find_one({"employee_id": employee_id})
        if existing_request:
            raise HTTPException(status_code=400, detail="Onboarding request already exists for this employee.")

        # Generate a unique onboarding request ID
        onboarding_id = generate_id()

        # Ensure the generated _id is unique
        while onboarding_collection.find_one({"_id": onboarding_id}):
            onboarding_id = generate_id()

        # Insert onboarding request
        onboarding_request = {
            "_id": onboarding_id,
            "employee_id": employee_id,
            "required_access": required_access,
            "status": "Pending",
            "created_at": datetime.utcnow()
        }

        onboarding_collection.insert_one(onboarding_request)
        return {"message": "Onboarding request created successfully.", "onboarding_id": onboarding_id}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")

@app.get("/check_onboarding_status")
def check_onboarding_status(employee_id: str = Query(...)):
    """Check if an employee's onboarding request is completed."""

    try:
        # Find the onboarding request by employee_id
        onboarding_request = onboarding_collection.find_one({"employee_id": employee_id})

        # If no request exists, return an error
        if not onboarding_request:
            raise HTTPException(status_code=404, detail="Onboarding request not found.")

        # Check the status
        status = onboarding_request.get("status", "Pending")

        if status.lower() == "completed":
            return {"message": "Onboarding process is completed.", "status": status}
        else:
            raise HTTPException(status_code=400, detail=f"Onboarding status is not completed. Current status: {status}")

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")

# Check if an employee exists
def check_employee(employee_id: str):
    """Check if an employee exists in MongoDB."""
    try:
        return employees_collection.find_one({"_id": employee_id}) is not None
    except errors.PyMongoError:
        return False

@app.post("/add_reimbursement")
def add_reimbursement(employee_id: str = Query(...), expense_type: str = Query(...), expense_amount: float = Query(...), expense_date: str = Query(...)):
    """Add an expense reimbursement request after validating the employee exists."""
    
    try:
        # Check if employee exists
        employee = employees_collection.find_one({"_id": employee_id})
        if not employee:
            print(f"Employee ID {employee_id} not found.")
            raise HTTPException(status_code=400, detail="Employee not found.")

        # Ensure the finance_requests collection exists
        if "finance_requests" not in db.list_collection_names():
            db.create_collection("finance_requests")
            print("Created finance_requests collection.")

        # Insert reimbursement data
        reimbursement_data = {
            "_id": generate_id(),
            "employee_id": employee_id,
            "employee_name": employee.get("name", "Unknown"),
            "expense_type": expense_type,
            "expense_amount": expense_amount,
            "expense_date": expense_date,
            "status": "Pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        print(f"Inserting reimbursement for employee {employee_id}...")
        finance_requests_collection.insert_one(reimbursement_data)
        print("Reimbursement request added successfully.")

        return {"message": "Reimbursement request added successfully.", "request_id": reimbursement_data["_id"]}

    except PyMongoError as e:
        print(f"MongoDB Error: {str(e)}")  # Log database errors
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

    except Exception as e:
        print(f"General Error: {str(e)}")  # Log general errors
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")

@app.get("/check_reimbursement")
def check_reimbursement(employee_id: str = Query(...)):
    """Check all reimbursement requests for a specific employee."""
    
    try:
        # Find reimbursement requests for the given employee ID
        reimbursements = list(finance_requests_collection.find({"employee_id": employee_id}))

        # If no reimbursement requests exist, return an error
        if not reimbursements:
            raise HTTPException(status_code=404, detail="No reimbursement requests found for this employee.")

        # Convert _id to string before returning
        for reimbursement in reimbursements:
            reimbursement["_id"] = str(reimbursement["_id"])

        return {
            "message": "Reimbursement requests found.",
            "reimbursements": reimbursements
        }

    except PyMongoError as e:
        print(f"MongoDB Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

    except Exception as e:
        print(f"General Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")

@app.get("/add_procurement_request")
def add_procurement_request(
    employee_id: str = Query(...), 
    item_name: str = Query(...), 
    quantity: int = Query(...), 
    reason: str = Query(...)
):
    """Add a new procurement request after validating the employee exists."""

    try:
        # Check if employee exists
        employee = employees_collection.find_one({"_id": employee_id})
        if not employee:
            print(f"Employee ID {employee_id} not found.")
            raise HTTPException(status_code=400, detail="Employee not found.")

        # Ensure the procurement_requests collection exists
        if "procurement_requests" not in db.list_collection_names():
            db.create_collection("procurement_requests")
            print("Created procurement_requests collection.")

        # Insert procurement request data
        procurement_data = {
            "_id": generate_id(),
            "employee_id": employee_id,
            "employee_name": employee.get("name", "Unknown"),
            "item_name": item_name,
            "quantity": quantity,
            "reason": reason,
            "status": "Pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        print(f"Inserting procurement request for employee {employee_id}...")
        procurement_requests_collection.insert_one(procurement_data)
        print("Procurement request added successfully.")

        return {"message": "Procurement request added successfully.", "request_id": procurement_data["_id"]}

    except PyMongoError as e:
        print(f"MongoDB Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

    except Exception as e:
        print(f"General Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")

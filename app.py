from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import smtplib
from email.mime.text import MIMEText

app = FastAPI()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/nestle_db?retryWrites=true&w=majority&appName=Concentrix")
client = MongoClient(MONGO_URI)
db = client["nestle_db"]
collection = db["employees"]

# Email Credentials (Use environment variables for security)
SMTP_USER = "reyjohnandraje16@gmail.com"
SMTP_PASS = "tmxx fxjg akcb rcsi"  # Use an App Password instead of your actual password

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

def send_payslip_email(employee_id: str):
    """Fetch payslip data and send an email."""

    try:
        # Fetch employee data
        employee = collection.find_one({"_id": employee_id}, {"_id": 0, "name": 1, "email": 1, "Payslip": 1})

        if not employee or "Payslip" not in employee:
            return {"error": "Payslip not found for this employee."}

        # Extract details
        recipient = employee["email"]
        employee_name = employee["name"]
        payslip = employee["Payslip"]
        
        # Payslip details
        month = payslip.get("month", "Unknown")
        year = payslip.get("year", "Unknown")
        job_position = payslip.get("job_position", "Unknown")
        basic_salary = payslip.get("basic_salary", 0)
        allowances = payslip.get("allowances", 0)
        bonuses = payslip.get("bonuses", 0)
        deductions = payslip.get("deductions", 0)
        tax = payslip.get("tax", 0)
        net_salary = payslip.get("net_salary", 0)

        # Email content
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
- Bonuses: PHP {bonuses:,.2f}
- Deductions: PHP {deductions:,.2f}
- Tax Deducted: PHP {tax:,.2f}

Net Salary (Take-Home Pay): PHP {net_salary:,.2f}

Your salary has been processed and credited to your registered bank account. If you have any questions, feel free to reach out.

Best regards,  
HR Team  
Nestlé Philippines
"""

        # Send email via SMTP
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = recipient

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())

        return {"success": f"Payslip email sent to {recipient}"}

    except PyMongoError as db_error:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
    except smtplib.SMTPException as email_error:
        raise HTTPException(status_code=500, detail=f"Email error: {str(email_error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/send_payslip/{employee_id}")
def send_payslip(employee_id: str):
    """API endpoint to send payslip email by employee ID."""
    return send_payslip_email(employee_id)
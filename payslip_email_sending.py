import smtplib
from pymongo import MongoClient
from datetime import datetime
from email.mime.text import MIMEText

# MongoDB connection
client = MongoClient("mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/nestle_db?retryWrites=true&w=majority&appName=Concentrix")
db = client.nestle_db  # Database
employees = db.employees  # Collection

def send_payslip_email(user_id):
    """Fetch payslip data from MongoDB and send a detailed email."""

    # Fetch employee data
    employee = employees.find_one({"id": user_id}, {"_id": 0, "name": 1, "email": 1, "Payslip": 1})

    if not employee or "Payslip" not in employee:
        print(f"Payslip not found for Employee ID: {user_id}")
        return {"error": "Payslip not found for this employee."}

    # Extract necessary details
    recipient = employee["email"]
    employee_name = employee["name"]
    payslip = employee["Payslip"]
    
    # Payslip details
    month = payslip['month']
    year = payslip['year']
    job_position = payslip['job_position']
    basic_salary = payslip['basic_salary']
    allowances = payslip['allowances']
    bonuses = payslip['bonuses']
    deductions = payslip['deductions']
    tax = payslip['tax']
    net_salary = payslip['net_salary']

    # Email content
    subject = f"Your Payslip for {month} {year}"
    body = f"""Dear {employee_name},

We are pleased to provide you with your payslip for {month} {year}.

Employee Details:
- Name: {employee_name}
- Position: {job_position}
- Employee ID: {user_id}

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

    # Prepare email
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "hr@company.com"
    msg["To"] = recipient

    # Send email via SMTP
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("your-email@gmail.com", "your-email-password")  # Replace with valid credentials
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        
        print(f"Payslip email successfully sent to {recipient}")
        return {"success": f"Payslip email sent to {recipient}"}

    except Exception as e:
        print(f"Failed to send email: {e}")
        return {"error": str(e)}

# Example usage
send_payslip_email("20191134120")

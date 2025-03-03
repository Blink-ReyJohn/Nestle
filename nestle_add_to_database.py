from pymongo import MongoClient
import random
import string
from datetime import datetime

# MongoDB Atlas Connection (Replace with your actual connection string)
mongo_uri = "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/?retryWrites=true&w=majority&appName=Concentrix"
client = MongoClient(mongo_uri)

# Select Database and Collection
db = client["nestle_db"]  # Change this to your preferred database name
collection = db["employees"]  # Collection to store user data

# Function to generate a 10-character alphanumeric ID
def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# User ID
user_id = "20191134120"  # Your user ID

# Generate current timestamp
current_time = datetime.utcnow().isoformat()

# Generate unique request IDs
hr_request_id = generate_id()
it_request_id = generate_id()
finance_request_id = generate_id()

# Data Structure for MongoDB Atlas
user_data = {
    "_id": user_id,  # Using user_id as the document ID
    "name": "Rey John C. Andraje",
    "email": "reyjohnandraje@nestle.com",
    "employee_id": "EMP123456",
    "department": "IT Support",
    "lastQuery": "Requested VPN access for remote work",
    "timestamp": current_time,
    "HR_Requests": {
        hr_request_id: {
            "category": "Benefits Inquiry",
            "sub_category": "Health Insurance",
            "details": "Need clarification on health insurance coverage for dependents.",
            "status": "Pending",
            "created_at": current_time,
            "updated_at": current_time
        }
    },
    "IT_Requests": {
        it_request_id: {
            "issue_type": "VPN Access",
            "system": "Corporate Network",
            "details": "Unable to connect to VPN due to authentication failure.",
            "status": "Resolved",
            "resolution_notes": "IT reset user authentication settings, and VPN access was restored.",
            "created_at": current_time,
            "updated_at": current_time
        }
    },
    "Finance_Requests": {
        finance_request_id: {
            "category": "Payroll Discrepancy",
            "invoiceNumber": "INV567890",
            "amount": 1500.00,
            "currency": "PHP",
            "status": "Processing",
            "approval_status": "Pending HR Verification",
            "created_at": current_time,
            "updated_at": current_time
        }
    }
}

# Insert Data into MongoDB Atlas
try:
    collection.insert_one(user_data)
    print(f"Data for user {user_id} successfully added to MongoDB Atlas!")
    print(f"HR Request ID: {hr_request_id}")
    print(f"IT Request ID: {it_request_id}")
    print(f"Finance Request ID: {finance_request_id}")
except Exception as e:
    print(f"Error adding data: {e}")

# Close the MongoDB connection
client.close()

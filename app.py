from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB Atlas Connection
mongo_uri = "mongodb+srv://reyjohnandraje2002:ReyjohnAndraje17%23@concentrix.txv3t.mongodb.net/?retryWrites=true&w=majority&appName=Concentrix"
client = MongoClient(mongo_uri)

# Select Database and Collection
db = client["nestle_db"]  # Your Database Name
collection = db["nestle"]  # Your Collection Name

@app.route('/get_user_data/<user_id>', methods=['GET'])
def get_user_data(user_id):
    try:
        # Fetch document from MongoDB
        user = collection.find_one({"_id": user_id})
        
        if user:
            # Remove MongoDB ObjectId from the response
            user['_id'] = str(user['_id'])
            return jsonify(user), 200
        else:
            return jsonify({"error": "User ID not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import os

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("Real.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://aristatracker-default-rtdb.firebaseio.com/'
})

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/fetch-data', methods=['GET'])
def fetch_data():
    ref = db.reference('trackers_detail')  # Replace with your database path
    data = ref.get()
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'No data found'}), 404

if __name__ == '__main__':
    app.run(debug=True)

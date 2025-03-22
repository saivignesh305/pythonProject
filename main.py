from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import os

app = Flask(__name__)

try:
    cred = credentials.Certificate("Real.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://aristatracker-default-rtdb.firebaseio.com/'
    })
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit(1)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/fetch-data', methods=['GET'])
def fetch_data():
    try:
        ref = db.reference('trackers_detail')
        data = ref.get()
        return jsonify(data if data else {'error': 'No data found'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
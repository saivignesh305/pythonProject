import time

from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__)

def initialize_firebase(max_retries=3, retry_delay=5):
    retries = 0
    while retries < max_retries:
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("Real.json")
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://aristatracker-default-rtdb.firebaseio.com/'
                })
                print("Firebase initialized successfully")
            return True
        except Exception as e:
            retries += 1
            print(f"Error initializing Firebase (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Failed to initialize Firebase after maximum retries")
                return False

if not initialize_firebase():
    print("Application will continue with limited functionality")
    app.config['FIREBASE_AVAILABLE'] = False
else:
    app.config['FIREBASE_AVAILABLE'] = True


@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/users')
def users():
    return render_template('users.html')
@app.route('/analytics')
def analytics():
    return render_template('analytics.html')


@app.route('/download-data', methods=['GET'])
def download_data():
    try:
        # Get all data from Firebase
        trackers_ref = db.reference('trackers_detail')
        trackers_data = trackers_ref.get()

        users_ref = db.reference('users')
        users_data = users_ref.get()

        # Combine the data
        combined_data = {
            'trackers_detail': trackers_data or {},
            'users': users_data or {}
        }

        # Add timestamp to filename
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"aristavault_data_{current_time}.json"

        # Create a response with the JSON data
        response = jsonify(combined_data)
        response.headers.set('Content-Disposition', f'attachment; filename={filename}')
        response.headers.set('Content-Type', 'application/json')

        return response
    except firebase_admin.exceptions.FirebaseError as fe:
        app.logger.error(f"Firebase error: {fe}")
        return jsonify({'error': f'Database error: {str(fe)}'}), 503
    except Exception as e:
        app.logger.error(f"Error downloading data: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/fetch-data', methods=['GET'])
def fetch_data():
    try:
        trackers_ref = db.reference('trackers_detail')
        trackers_data = trackers_ref.get()

        users_ref = db.reference('users')
        users_data = users_ref.get()

        combined_data = {}

        if trackers_data:
            combined_data.update(trackers_data)

        if users_data:
            for user_id, user_info in users_data.items():
                if user_id not in combined_data:
                    combined_data[user_id] = {
                        'userName': user_info.get('name', 'Unknown'),
                        'userEmail': user_info.get('email', ''),
                        'userPhone': user_info.get('phone', ''),  # Add phone number extraction
                        'devices': {}
                    }

                    if 'deviceType' in user_info and 'deviceUniqueId' in user_info:
                        device_id = user_info['deviceUniqueId']
                        combined_data[user_id]['devices'][device_id] = {
                            'deviceType': user_info['deviceType'],
                            'appVersion': user_info.get('appVersionCurrent', 'Unknown'),
                            'createdAt': user_info.get('createdAt', ''),
                            'lastConnectionTime': user_info.get('lastLogin', ''),
                            'connectedCount': 0,
                            'disconnectedCount': 0,
                            'mobileAlarmCount': 0,
                            'startAlarmCount': 0,
                            'stopAlarmCount': 0,
                            'markAsLostCount': 0,
                            'revokeMarkAsLostCount': 0
                        }

        if combined_data:
            enhanced_data = enhance_tracker_data(combined_data)
            return jsonify(enhanced_data), 200
        else:
            app.logger.warning("No data found in Firebase")
            return jsonify({'error': 'No data found'}), 404
    except firebase_admin.exceptions.FirebaseError as fe:
        app.logger.error(f"Firebase error: {fe}")
        return jsonify({'error': f'Database error: {str(fe)}'}), 503
    except Exception as e:
        app.logger.error(f"Error fetching data: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


def enhance_tracker_data(data):
    enhanced_data = {}

    for user_id, user_data in data.items():
        # Copy over user data
        enhanced_data[user_id] = user_data.copy() if isinstance(user_data, dict) else {}

        # Ensure devices object exists
        if 'devices' not in enhanced_data[user_id]:
            enhanced_data[user_id]['devices'] = {}

        # Ensure we have phone number field
        if 'userPhone' not in enhanced_data[user_id]:
            enhanced_data[user_id]['userPhone'] = 'N/A'

            # Try to extract phone from email domain if it looks like a phone number
            if 'userEmail' in enhanced_data[user_id]:
                email = enhanced_data[user_id]['userEmail']
                domain = email.split('@')[-1] if '@' in email else ''
                if domain.replace('.', '').isdigit() and len(domain.replace('.', '')) >= 10:
                    enhanced_data[user_id]['userPhone'] = domain.replace('.', '')


        if 'devices' in user_data and isinstance(user_data['devices'], dict):
            for device_id, device_data in user_data['devices'].items():

                enhanced_device = device_data.copy() if isinstance(device_data, dict) else {}


                if 'deviceType' in enhanced_device:
                    if enhanced_device['deviceType'].lower() == 'ios':
                        enhanced_device['platform'] = 'iOS'
                    elif enhanced_device['deviceType'].lower() == 'android':
                        enhanced_device['platform'] = 'Android'
                    else:
                        enhanced_device['platform'] = 'Other'

                # Handle missing createdAt
                if 'createdAt' in enhanced_device and not enhanced_device.get('createdAt'):
                    enhanced_device['createdAt'] = datetime.now().isoformat()

                # Handle missing lastConnectionTime
                if 'lastConnectionTime' not in enhanced_device:
                    if 'updatedAt' in enhanced_device:
                        enhanced_device['lastConnectionTime'] = enhanced_device['updatedAt']
                    elif 'createdAt' in enhanced_device:
                        enhanced_device['lastConnectionTime'] = enhanced_device['createdAt']
                    else:
                        enhanced_device['lastConnectionTime'] = datetime.now().isoformat()

                # Handle average connection time calculation
                if 'avgConnectionTime' not in enhanced_device:
                    connected_count = enhanced_device.get('connectedCount', 0)

                    if connected_count > 0 and 'totalUsageTime' in enhanced_device:
                        enhanced_device['avgConnectionTime'] = enhanced_device['totalUsageTime'] / connected_count
                    else:
                        # Provide reasonable defaults
                        if connected_count > 20:
                            enhanced_device['avgConnectionTime'] = 15  # 15 minutes avg for power users
                        else:
                            enhanced_device['avgConnectionTime'] = 25  # 25 minutes for casual users

                # Store enhanced device data
                enhanced_data[user_id]['devices'][device_id] = enhanced_device

        # Set up name field if not present
        if 'userName' in user_data:
            enhanced_data[user_id]['name'] = user_data['userName']
        elif 'userEmail' in user_data:
            # Use email if name not available
            enhanced_data[user_id]['name'] = user_data['userEmail'].split('@')[0]


        if 'userEmail' in user_data:
            enhanced_data[user_id]['email'] = user_data['userEmail']


        if 'userPhone' in user_data:
            enhanced_data[user_id]['phoneNumber'] = user_data['userPhone']

    return enhanced_data

    return enhanced_data
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
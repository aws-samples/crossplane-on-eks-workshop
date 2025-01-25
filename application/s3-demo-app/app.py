import os
import boto3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Set up the S3 client
s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/items', methods=['GET'])
def get_items():
    try:
        # List all objects in the S3 bucket
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        items = [{'name': obj['Key'], 'content': s3.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])['Body'].read().decode('utf-8')} for obj in response.get('Contents', [])]
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items', methods=['POST'])
def add_item():
    try:
        data = request.get_json()
        file_name = data['name']
        file_content = data['content']

        # Upload the file to S3
        s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=file_content.encode('utf-8'))
        return jsonify({'message': 'Item added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<filename>', methods=['DELETE'])
def delete_item(filename):
    try:
        # Delete the file from S3
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
        return jsonify({'message': 'Item deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check if we can list objects in the S3 bucket
        s3.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1)
        return jsonify({'status': 'healthy', 'message': 'Application is running and can connect to S3'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'message': f'Error connecting to S3: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
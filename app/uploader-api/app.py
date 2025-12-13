from flask import Flask, request, jsonify
import boto3
import os
import uuid 

app = Flask(__name__)

# Получение имени S3-бакета из переменных окружения
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'devops-test-bucket') 
s3_client = boto3.client('s3') 

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "service": "uploader-api"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        try:
            # Загрузка файла в S3
            s3_client.upload_fileobj(
                file,
                S3_BUCKET,
                unique_filename,
                ExtraArgs={'ContentType': file.content_type}
            )
            return jsonify({
                "message": "File uploaded successfully",
                "filename": unique_filename,
                "bucket": S3_BUCKET
            }), 201
        except Exception as e:
            app.logger.error(f"S3 Upload Error: {e}")
            return jsonify({"error": "Failed to upload to S3"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify
import boto3
import os
import uuid

app = Flask(__name__)

S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'devops-test-bucket')
s3_client = boto3.client('s3')

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'json', 'xml', 'zip'}


@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "service": "uploader-api"}), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    name_parts = file.filename.rsplit('.', 1)
    if len(name_parts) != 2:
        return jsonify({"error": "File must have an extension"}), 400

    extension = name_parts[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"File type '.{extension}' not allowed"}), 415

    content = file.read()
    if len(content) > MAX_FILE_SIZE:
        return jsonify({"error": f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB"}), 413

    unique_filename = f"{uuid.uuid4()}.{extension}"

    try:
        import io
        s3_client.upload_fileobj(
            io.BytesIO(content),
            S3_BUCKET,
            unique_filename,
            ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
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

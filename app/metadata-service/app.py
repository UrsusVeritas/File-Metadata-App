from flask import Flask, request, jsonify
from datetime import datetime, timezone

app = Flask(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "service": "metadata-service"}), 200


@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    content = file.read()
    if len(content) > MAX_FILE_SIZE:
        return jsonify({"error": f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB"}), 413

    name_parts = file.filename.rsplit('.', 1)
    extension = name_parts[1].lower() if len(name_parts) == 2 else 'unknown'

    metadata = {
        "filename": file.filename,
        "extension": extension,
        "size_bytes": len(content),
        "content_type": file.content_type or "application/octet-stream",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "service": "metadata-service",
    }

    return jsonify(metadata), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

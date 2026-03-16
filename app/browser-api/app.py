from flask import Flask, request, jsonify
import boto3
import os

app = Flask(__name__)

S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'devops-test-bucket')


@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "service": "browser-api"}), 200


@app.route('/list', methods=['GET'])
def list_files():
    prefix = request.args.get('prefix', '')
    max_keys = min(int(request.args.get('max_keys', 50)), 200)

    try:
        s3_client = boto3.client('s3')
        kwargs = {'Bucket': S3_BUCKET, 'MaxKeys': max_keys}
        if prefix:
            kwargs['Prefix'] = prefix

        response = s3_client.list_objects_v2(**kwargs)

        files = [
            {
                "key": obj['Key'],
                "size_bytes": obj['Size'],
                "last_modified": obj['LastModified'].isoformat(),
                "etag": obj['ETag'].strip('"'),
            }
            for obj in response.get('Contents', [])
        ]

        return jsonify({"bucket": S3_BUCKET, "count": len(files), "files": files}), 200

    except Exception as e:
        app.logger.error(f"S3 list error: {e}")
        return jsonify({"error": "Failed to list files from S3"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

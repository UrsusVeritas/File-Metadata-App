from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "service": "metadata-service"}), 200

@app.route('/process', methods=['POST'])
def process_file():
    
    return jsonify({"message": "Processing simulated", "service": "metadata-service"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
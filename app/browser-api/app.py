from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "service": "browser-api"}), 200

@app.route('/list', methods=['GET'])
def list_files():
    
    return jsonify({"files": [], "message": "List retrieval simulated", "service": "browser-api"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "Webhook server is alive."})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook received:", data)
    return jsonify({"status": "received", "data": data})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


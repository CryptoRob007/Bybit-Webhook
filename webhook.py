from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "Webhook server is alive."})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("Webhook received:", data)
        return jsonify({"status": "received", "data": data})
    except Exception as e:
        print("Error handling webhook:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


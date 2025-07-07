# Bybit Webhook Server (Python Flask)
# This receives webhook alerts from TradingView and sends signed orders to Bybit.

from flask import Flask, request, jsonify
import time
import hmac
import hashlib
import requests
import json
import os

app = Flask(__name__)

# === CONFIG ===
API_KEY = 'YOUR_BYBIT_API_KEY'
API_SECRET = 'YOUR_BYBIT_API_SECRET'
BYBIT_URL = 'https://api.bybit.com/v5/order/create'  # Inverse or Unified Mainnet URL

# === HELPER: Create signature ===
def create_signature(secret, params):
    sorted_params = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(secret.encode(), sorted_params.encode(), hashlib.sha256).hexdigest()

# === HELPER: Send signed order ===
def send_order_to_bybit(side, symbol, qty):
    timestamp = str(int(time.time() * 1000))
    order_data = {
        "apiKey": API_KEY,
        "timestamp": timestamp,
        "recvWindow": "5000",
        "category": "inverse",  # or 'linear' if you're using USDT contracts
        "symbol": symbol,
        "side": side.capitalize(),  # Buy or Sell
        "orderType": "Market",
        "qty": qty,
        "timeInForce": "IOC",
        "positionIdx": 0,
    }
    
    sign = create_signature(API_SECRET, order_data)
    headers = {"Content-Type": "application/json"}
    order_data["sign"] = sign

    response = requests.post(BYBIT_URL, headers=headers, json=order_data)
    try:
        data = response.json()
        return data
    except:
        return {"error": "Could not parse response", "raw": response.text}

# === MAIN ROUTE ===
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        content = request.data.decode()
        print("Received:", content)
        
        if "|" not in content:
            return jsonify({"error": "Invalid format. Use BUY|BTCUSD.P|0.005"}), 400

        side, symbol, qty = content.split("|")
        result = send_order_to_bybit(side.strip().lower(), symbol.strip(), qty.strip())
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === RUN ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

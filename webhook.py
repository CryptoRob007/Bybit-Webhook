from flask import Flask, request, jsonify
from pybit.unified_trading import HTTP
import os

app = Flask(__name__)

# === Bybit API Credentials ===
API_KEY = os.environ.get("BYBIT_API_KEY") or "your-api-key"
API_SECRET = os.environ.get("BYBIT_API_SECRET") or "your-api-secret"

# === Bybit Client ===
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    testnet=False  # Set to True for testnet
)

# === Instrument Symbol ===
SYMBOL = "BTCUSD"
CATEGORY = "linear"  # For BTCUSD inverse perpetual use 'linear'

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "Webhook server is alive."})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Received webhook:", data)

    try:
        order_type = data.get("type")
        qty = float(data.get("qty"))
        avg_entry = float(data.get("avg_entry", 0))
        tp_price = float(data.get("tp_price", 0))

        # Convert BTC qty to USD contracts (1 contract = $1)
        ticker = session.get_ticker(category=CATEGORY, symbol=SYMBOL)
        market_price = float(ticker["result"]["list"][0]["lastPrice"])
        contracts = round(qty * market_price)

        if order_type == "entry":
            print("Placing market entry order...")
            session.place_order(
                category=CATEGORY,
                symbol=SYMBOL,
                side="Buy",
                order_type="Market",
                qty=contracts,
                time_in_force="GoodTillCancel"
            )

            if tp_price > 0:
                session.place_order(
                    category=CATEGORY,
                    symbol=SYMBOL,
                    side="Sell",
                    order_type="Limit",
                    qty=contracts,
                    price=tp_price,
                    time_in_force="GoodTillCancel",
                    reduce_only=True
                )

        elif order_type == "safety":
            print("Placing safety limit buy order...")
            session.place_order(
                category=CATEGORY,
                symbol=SYMBOL,
                side="Buy",
                order_type="Limit",
                qty=contracts,
                price=avg_entry * (1 - 0.01),  # 1% discount
                time_in_force="GoodTillCancel"
            )

            if tp_price > 0:
                session.place_order(
                    category=CATEGORY,
                    symbol=SYMBOL,
                    side="Sell",
                    order_type="Limit",
                    qty=contracts,
                    price=tp_price,
                    time_in_force="GoodTillCancel",
                    reduce_only=True
                )

        elif order_type == "exit":
            print("Placing take-profit limit sell order...")
            session.place_order(
                category=CATEGORY,
                symbol=SYMBOL,
                side="Sell",
                order_type="Limit",
                qty=contracts,
                price=tp_price,
                time_in_force="GoodTillCancel",
                reduce_only=True
            )

        else:
            return jsonify({"status": "error", "message": "Unknown order type."}), 400

        return jsonify({"status": "ok", "message": "Order placed"})

    except Exception as e:
        print("Webhook error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

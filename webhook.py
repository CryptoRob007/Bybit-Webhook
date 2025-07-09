from flask import Flask, request, jsonify
from pybit.unified_trading import HTTP
import os

# === Flask setup ===
app = Flask(__name__)

# === Bybit API setup ===
api_key = os.environ.get("BYBIT_API_KEY")
api_secret = os.environ.get("BYBIT_API_SECRET")

session = HTTP(
    api_key=api_key,
    api_secret=api_secret,
    testnet=False  # Change to True if testing on testnet
)

symbol = "BTCUSD"  # Inverse Perpetual

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "Webhook server is alive."})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("Webhook received:", data)

        order_type = data.get("type")
        qty = float(data.get("qty", 0))
        avg_entry = float(data.get("avg_entry", 0))
        tp_price = float(data.get("tp_price", 0))

        if order_type == "entry":
            # Place market entry
            entry_order = session.place_order(
                category="inverse",
                symbol=symbol,
                side="Buy",
                order_type="Market",
                qty=qty,
                time_in_force="GoodTillCancel"
            )
            print("Market entry order:", entry_order)

            # Place take profit limit order
            if tp_price > 0:
                tp_order = session.place_order(
                    category="inverse",
                    symbol=symbol,
                    side="Sell",
                    order_type="Limit",
                    price=tp_price,
                    qty=qty,
                    time_in_force="GoodTillCancel",
                    reduce_only=True
                )
                print("Take Profit order:", tp_order)

        elif order_type == "safety":
            # Place safety limit buy
            safety_order = session.place_order(
                category="inverse",
                symbol=symbol,
                side="Buy",
                order_type="Limit",
                price=avg_entry,  # Safety buy at avg_entry or deeper
                qty=qty,
                time_in_force="GoodTillCancel"
            )
            print("Safety order:", safety_order)

            # Updated TP after safety — optional depending on how Pine script tracks TP

        elif order_type == "exit":
            # Close position at market
            close_order = session.place_order(
                category="inverse",
                symbol=symbol,
                side="Sell",
                order_type="Market",
                qty=qty,
                reduce_only=True,
                time_in_force="ImmediateOrCancel"
            )
            print("Exit order:", close_order)

        return jsonify({"status": "success"})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


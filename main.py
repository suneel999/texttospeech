from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Set environment variables for verification token, Graph API token, and port
WEBHOOK_VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN", "tested")  # Replace with your verification token
GRAPH_API_TOKEN = os.environ.get("GRAPH_API_TOKEN", "EAAXbZCUeswOkBOZC4tCKZC8nLikcuyCaYsIV42mbCM2ZAstdEInKdznGUyFIbqaWNN0Lv8awm7gJXZABpa3ROCcpa1zxZAJpTVL7c0AHqWr80l76McE5hC9QiH1UhNHC0TDt4AKWdbBAygsa6CCHF6tzZBzROpZAFE4cVTLJtTo7pdYr3ynLEFkWvSSfWIubhTrL3wCqC3hAi35kxaP6Psx4ZBmbgcS44guxxYmlody0c62AZD")  # Replace with your Graph API token
PORT = os.environ.get("PORT", 5000)  # Default port is 5000

# Handle incoming webhook POST requests
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    print("Incoming webhook message:", data)  # Log incoming message for debugging

    # Extract the message if it exists
    message = (data.get("entry", [{}])[0]
                   .get("changes", [{}])[0]
                   .get("value", {})
                   .get("messages", [{}])[0])

    # Check if a valid message exists and contains text
    if message and message.get("type") == "text":
        # Extract business phone number ID to send the reply from
        business_phone_number_id = (data.get("entry", [{}])[0]
                                       .get("changes", [{}])[0]
                                       .get("value", {})
                                       .get("metadata", {})
                                       .get("phone_number_id"))

        if not business_phone_number_id:
            print("No business phone number ID found in the request.")
            return jsonify({"error": "No business phone number ID found"}), 400

        # Send a reply message
        reply_url = f"https://graph.facebook.com/v20.0/{business_phone_number_id}/messages"
        reply_headers = {
            "Authorization": f"Bearer {GRAPH_API_TOKEN}",
            "Content-Type": "application/json"
        }
        reply_data = {
            "messaging_product": "whatsapp",
            "to": message.get("from"),
            "text": {"body": "Echo: " + message.get("text", {}).get("body", "")},
            "context": {
                "message_id": message.get("id")  # Reply to the original user message
            }
        }

        response = requests.post(reply_url, headers=reply_headers, json=reply_data)
        print("Reply sent response:", response.json())  # Log the response

        # Mark the incoming message as read
        mark_read_data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message.get("id")
        }
        mark_read_response = requests.post(reply_url, headers=reply_headers, json=mark_read_data)
        print("Mark read response:", mark_read_response.json())  # Log the response

    return jsonify({"status": "received"}), 200

# Handle webhook verification GET requests
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Log the received parameters for debugging
    print(f"Received mode: {mode}")
    print(f"Received token: {token}")
    print(f"Received challenge: {challenge}")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    else:
        print("Verification failed.")
        return "Forbidden", 403


@app.route("/", methods=["GET"])
def home():
    return "<pre>Nothing to see here.\nCheckout README.md to start.</pre>"

if __name__ == "__main__":
    app.run(port=PORT)

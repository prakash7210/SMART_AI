from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId
from urllib.parse import quote
import os, random, requests, dns.resolver

# ---------------- INIT ----------------
app = Flask(__name__)
CORS(app)
load_dotenv()

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]

# ---------------- ENV ----------------
DB_HOST = os.getenv("DB_HOST")
if not DB_HOST:
    raise RuntimeError("Missing DB_HOST")

# ---------------- MongoDB ----------------
client = MongoClient(DB_HOST)
db = client["GEN"]
collection = db["messages"]

# ---------------- TEXT → TEXT (GUARANTEED) ----------------
@app.route("/text-to-text", methods=["POST"])
def text_to_text():
    prompt = request.json.get("prompt", "").strip()
    if not prompt:
        return jsonify({"answer": ""})

    try:
        url = f"https://text.pollinations.ai/{quote(prompt)}"
        r = requests.get(url, timeout=30)

        if r.status_code == 200:
            return jsonify({"answer": r.text})

        return jsonify({"answer": "❌ Text service unavailable"})

    except Exception as e:
        print("TEXT ERROR:", e)
        return jsonify({"answer": "❌ AI error"})

# ---------------- TEXT → IMAGE ----------------
@app.route("/text-to-image", methods=["POST"])
def text_to_image():
    prompt = request.json.get("prompt", "")
    seed = random.randint(1, 999999)

    return jsonify({
        "image_url": f"https://image.pollinations.ai/prompt/{quote(prompt)}"
    })

# ---------------- SAVE CHAT ----------------
@app.route("/save-chat", methods=["POST"])
def save_chat():
    try:
        data = request.json or {}

        prompt = data.get("prompt", "")
        response = data.get("response", "")
        mode = data.get("mode", "text")
        chat_id = data.get("chat_id")

        if not prompt or not response:
            return jsonify({"error": "Invalid data"}), 400

        messages = [
            {"role": "user", "type": "text", "content": prompt},
            {"role": "bot", "type": mode, "content": response}
        ]

        if chat_id:
            collection.update_one(
                {"_id": ObjectId(chat_id)},
                {"$push": {"messages": {"$each": messages}}}
            )
            return jsonify({"chat_id": chat_id})

        result = collection.insert_one({
            "title": prompt[:30],
            "messages": messages,
            "created_at": datetime.utcnow()
        })

        return jsonify({"chat_id": str(result.inserted_id)})

    except Exception as e:
        print("SAVE ERROR:", e)
        return jsonify({"error": "Save failed"}), 500

# ---------------- GET CHATS ----------------
@app.route("/get-chats")
def get_chats():
    return jsonify([
        {"id": str(c["_id"]), "title": c["title"]}
        for c in collection.find().sort("created_at", -1)
    ])

@app.route("/get-chat/<chat_id>")
def get_chat(chat_id):
    try:
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        return jsonify(chat["messages"])
    except Exception:
        return jsonify([])

# ---------------- DELETE CHAT ----------------
@app.route("/delete-chat/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    collection.delete_one({"_id": ObjectId(chat_id)})
    return jsonify({"status": "deleted"})

# ---------------- HEALTH ----------------
@app.route("/")
def home():
    return {"status": "Flask API running (text guaranteed)"}

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from huggingface_hub import InferenceClient
import whisper
import os
import uuid
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
# ---------------- INIT ----------------
app = Flask(__name__)
CORS(app)
load_dotenv()
import dns.resolver

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]

# ============================
# MongoDB Connection
# ============================
client = MongoClient(os.getenv("DB_HOST"),serverSelectionTimeoutMS=5000)
db = client["GEN"]
collection = db["messages"]

UPLOADS = "uploads"
OUTPUTS = "outputs"
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

# 🔑 Hugging Face token (READ)
HF_TOKEN = os.getenv("SECRET_KEY")

# Hugging Face official client
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_TOKEN
)

image_client = InferenceClient(
    model="stabilityai/sdxl-turbo",
    token=HF_TOKEN
)

# Local Whisper (FREE)
whisper_model = whisper.load_model("base")

# ---------------------------
# TEXT → TEXT (ANY QUESTION)
# ---------------------------
@app.route("/text-to-text", methods=["POST"])
def text_to_text():
    question = request.json.get("prompt")

    completion = client.chat_completion(
        messages=[
            {"role": "user", "content": question}
        ],
        max_tokens=200
    )

    answer = completion.choices[0].message["content"]

    return jsonify({
        "question": question,
        "answer": answer
    })


# ---------------------------
# TEXT → IMAGE
# ---------------------------
from urllib.parse import quote
import random, uuid

@app.route("/text-to-image", methods=["POST"])
def text_to_image():
    prompt = request.json.get("prompt")

    try:
        # 🔹 add randomness
        seed = random.randint(1, 1_000_000)

        image = image_client.text_to_image(
            prompt,
            seed=seed   # 🔥 IMPORTANT
        )

        path = f"{OUTPUTS}/{uuid.uuid4()}.png"
        image.save(path)

        return send_file(path, mimetype="image/png")

    except Exception:
        # 🔹 encode prompt + random seed
        encoded_prompt = quote(prompt)
        seed = random.randint(1, 1_000_000)

        fallback_url = (
            f"https://image.pollinations.ai/prompt/"
            f"{encoded_prompt}?seed={seed}"
        )

        return jsonify({
            "warning": "HF busy. Using fallback.",
            "image_url": fallback_url
        })
    
# ============================
# SAVE CHAT TO DATABASE
# ============================
from bson import ObjectId

@app.route("/save-chat", methods=["POST"])
def save_chat():
    data = request.json
    chat_id = data.get("chat_id")

    message_pair = [
        {
            "role": "user",
            "type": "text",
            "content": data["prompt"]
        },
        {
            "role": "bot",
            "type": data["mode"],
            "content": data["response"]
        }
    ]

    if chat_id:
        # append to existing chat
        collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"messages": {"$each": message_pair}}}
        )
        return jsonify({"chat_id": chat_id})

    else:
        # create new chat
        chat = {
            "title": data["prompt"][:30],
            "messages": message_pair,
            "created_at": datetime.utcnow()
        }
        result = collection.insert_one(chat)
        return jsonify({"chat_id": str(result.inserted_id)})




# ============================
# GET CHAT HISTORY
# ============================
@app.route("/get-chats")
def get_chats():
    chats = []
    for c in collection.find().sort("created_at", -1):
        chats.append({
            "id": str(c["_id"]),
            "title": c["title"]
        })
    return jsonify(chats)

@app.route("/get-chat/<chat_id>")
def get_chat(chat_id):
    chat = collection.find_one({"_id": ObjectId(chat_id)})
    return jsonify(chat["messages"])

# ============================
# DELETE CHAT

@app.route("/delete-chat/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    collection.delete_one({"_id": ObjectId(chat_id)})
    return jsonify({"status": "deleted"})



# ============================
# HEALTH CHECK
# ============================
@app.route("/")
def home():
    return {"status": "Flask + MongoDB API running"}

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

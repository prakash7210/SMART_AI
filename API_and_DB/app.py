from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from huggingface_hub import InferenceClient
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId
from urllib.parse import quote
import os, uuid, random
import dns.resolver
# ---------------- INIT ----------------
app = Flask(__name__)
CORS(app)
load_dotenv()



dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]

# ---------------- MongoDB ----------------
client = MongoClient(os.getenv("DB_HOST"), serverSelectionTimeoutMS=5000)
db = client["GEN"]
collection = db["messages"]

OUTPUTS = "outputs"
os.makedirs(OUTPUTS, exist_ok=True)

HF_TOKEN = os.getenv("SECRET_KEY")



# ---------------- Lazy HF Clients ----------------
def get_text_client():
    return InferenceClient(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        token=HF_TOKEN
    )

def get_image_client():
    return InferenceClient(
        model="stabilityai/sdxl-turbo",
        token=HF_TOKEN
    )

# ---------------- TEXT → TEXT ----------------
@app.route("/text-to-text", methods=["POST"])
def text_to_text():
    question = request.json.get("prompt")

    client = get_text_client()
    completion = client.chat_completion(
        messages=[{"role": "user", "content": question}],
        max_tokens=120
    )

    return jsonify({
        "question": question,
        "answer": completion.choices[0].message["content"]
    })

# ---------------- TEXT → IMAGE ----------------
@app.route("/text-to-image", methods=["POST"])
def text_to_image():
    prompt = request.json.get("prompt")
    seed = random.randint(1, 1_000_000)

    try:
        image_client = get_image_client()
        image = image_client.text_to_image(prompt, seed=seed)

        path = f"{OUTPUTS}/{uuid.uuid4()}.png"
        image.save(path)
        return send_file(path, mimetype="image/png")

    except Exception:
        return jsonify({
            "warning": "HF busy – fallback used",
            "image_url": f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={seed}"
        })

# ---------------- SAVE CHAT ----------------
@app.route("/save-chat", methods=["POST"])
def save_chat():
    data = request.json
    chat_id = data.get("chat_id")

    messages = [
        {"role": "user", "type": "text", "content": data["prompt"]},
        {"role": "bot", "type": data["mode"], "content": data["response"]}
    ]

    if chat_id:
        collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"messages": {"$each": messages}}}
        )
        return jsonify({"chat_id": chat_id})

    result = collection.insert_one({
        "title": data["prompt"][:30],
        "messages": messages,
        "created_at": datetime.utcnow()
    })

    return jsonify({"chat_id": str(result.inserted_id)})

# ---------------- GET CHATS ----------------
@app.route("/get-chats")
def get_chats():
    return jsonify([
        {"id": str(c["_id"]), "title": c["title"]}
        for c in collection.find().sort("created_at", -1)
    ])

@app.route("/get-chat/<chat_id>")
def get_chat(chat_id):
    chat = collection.find_one({"_id": ObjectId(chat_id)})
    return jsonify(chat["messages"])

# ---------------- DELETE CHAT ----------------
@app.route("/delete-chat/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    collection.delete_one({"_id": ObjectId(chat_id)})
    return jsonify({"status": "deleted"})

# ---------------- HEALTH ----------------
@app.route("/")
def home():
    return {"status": "Flask API running (low memory)"}

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=False)

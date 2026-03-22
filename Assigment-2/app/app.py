from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/tododb")
client = MongoClient(MONGO_URI)
db = client.tododb
todos = db.todos


@app.route("/health")
def health():
    try:
        client.admin.command("ping")
        return jsonify({"status": "healthy", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/")
def index():
    all_todos = list(todos.find())
    return render_template("index.html", todos=all_todos)


@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task", "").strip()
    if task:
        todos.insert_one({"task": task, "done": False})
    return redirect(url_for("index"))


@app.route("/complete/<todo_id>")
def complete(todo_id):
    todos.update_one({"_id": ObjectId(todo_id)}, {"$set": {"done": True}})
    return redirect(url_for("index"))


@app.route("/delete/<todo_id>")
def delete(todo_id):
    todos.delete_one({"_id": ObjectId(todo_id)})
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

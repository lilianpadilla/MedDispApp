# app.py
from flask import Flask, jsonify, request
from sqlalchemy import text
from connection import engine  # import the shared database connection

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "hello from root /"}

@app.route("/users", methods=["GET"])
def get_users():
    """Retrieve all users from PostgreSQL"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users"))
        rows = [dict(r) for r in result.mappings()]
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True)

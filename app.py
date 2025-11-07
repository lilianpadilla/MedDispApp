# app.py
from flask import Flask, jsonify, request
from sqlalchemy import text
from connection import engine, SessionLocal, Base  # import the shared database connection
from models import User

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "hello from root /"}

@app.route("/users", methods=["GET"])
def get_users():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return jsonify([{"id": u.id, "name": u.name, "age": u.age} for u in users])

if __name__ == "__main__":
    app.run(debug=True)

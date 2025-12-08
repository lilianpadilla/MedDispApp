from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")

url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM patient;"))
        rows = result.mappings().all()
        sample = rows[0]
        for row in result:
            print(row)
    print("Connected successfully to db!")
except Exception as e:
    print("Connection failed:", e)

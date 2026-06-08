from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://agriuser:agripass@localhost:3306/agriweather_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

import os
from sqlalchemy import URL, text
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

from routes.student import student_bp
from routes.mentor import mentor_bp
from routes.college import college_bp

load_dotenv()

app = Flask(__name__)

# PostgreSQL configuration
database_url = URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# CREATE WORK LOGS TABLE
# =========================

with app.app_context():
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS work_logs (
            work_log_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            task_id INTEGER,
            work_date DATE NOT NULL,
            hours NUMERIC(5,2) NOT NULL,
            description TEXT NOT NULL,
            approval_status VARCHAR(20) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    db.session.commit()

@app.route("/test-db")
def test_db():
    try:
        with db.engine.connect() as connection:
            result = connection.execute(db.text("SELECT 1"))
            return "Database connected successfully! ✅"
    except Exception as e:
        return f"Database connection failed: {str(e)}", 500

@app.route("/")
def home():
    return "AgentX Backend is Running!"


app.register_blueprint(student_bp)
app.register_blueprint(mentor_bp)
app.register_blueprint(college_bp)


if __name__ == "__main__":
    app.run(debug=True)
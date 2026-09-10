from flask import Blueprint, jsonify

college_bp = Blueprint("college", __name__)

# college dashboard

@college_bp.route("/college/dashboard", methods=["GET"])
def college_dashboard():

    dashboard = {
        "total_students": 50,
        "active_internships": 42,
        "average_attendance": 78,
        "average_performance": 75,
        "at_risk_students": 8
    }

    return jsonify(dashboard)

# College Students

@college_bp.route("/college/students", methods=["GET"])
def college_students():

    students = [
        {
            "student_id": 1,
            "name": "Rahul",
            "department": "CSE",
            "company": "Tech Solutions",
            "attendance": 85,
            "performance": 82,
            "risk": "Low"
        },
        {
            "student_id": 2,
            "name": "Aditi",
            "department": "CSE",
            "company": "Tech Solutions",
            "attendance": 68,
            "performance": 65,
            "risk": "Medium"
        },
        {
            "student_id": 3,
            "name": "Priya",
            "department": "CSE",
            "company": "Innovate Labs",
            "attendance": 48,
            "performance": 48,
            "risk": "High"
        }
    ]

    return jsonify(students)

# College Performance API

@college_bp.route("/college/performance", methods=["GET"])
def college_performance():

    performance = {
        "average_attendance": 78,
        "average_punctuality": 81,
        "average_task_completion": 74,
        "average_mentor_rating": 80,
        "average_overall_score": 75
    }

    return jsonify(performance)

# At-Risk Students API

@college_bp.route("/college/at-risk", methods=["GET"])
def college_at_risk():

    at_risk_students = [
        {
            "student_id": 3,
            "name": "Priya",
            "attendance": 48,
            "punctuality": 55,
            "performance": 48,
            "risk": "High",
            "reason": "Low attendance and poor task completion"
        },
        {
            "student_id": 2,
            "name": "Aditi",
            "attendance": 68,
            "punctuality": 70,
            "performance": 65,
            "risk": "Medium",
            "reason": "Below average attendance and performance"
        }
    ]

    return jsonify(at_risk_students)
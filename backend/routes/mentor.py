from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text

mentor_bp = Blueprint("mentor", __name__)

# mentor intern acsses 
@mentor_bp.route("/mentor/interns", methods=["GET"])
def mentor_interns():
    interns = [
        {
            "student_id": 1,
            "name": "Rahul",
            "company": "Tech Solutions",
            "attendance": 85,
            "punctuality": 90,
            "tasks_completed": 7,
            "total_tasks": 10,
            "performance": 82,
            "risk": "Low"
        },
        {
            "student_id": 2,
            "name": "Aditi",
            "company": "Tech Solutions",
            "attendance": 68,
            "punctuality": 70,
            "tasks_completed": 5,
            "total_tasks": 10,
            "performance": 65,
            "risk": "Medium"
        },
        {
            "student_id": 3,
            "name": "Priya",
            "company": "Tech Solutions",
            "attendance": 48,
            "punctuality": 55,
            "tasks_completed": 3,
            "total_tasks": 10,
            "performance": 48,
            "risk": "High"
        }
    ]

    return jsonify(interns)


# Mentor Work-Log Review API

@mentor_bp.route("/mentor/work-log/<int:log_id>/review", methods=["POST"])
def review_work_log(log_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    status = data.get("status")
    feedback = data.get("feedback", "")

    if status not in ["Approved", "Rejected"]:
        return jsonify({
            "error": "Status must be Approved or Rejected"
        }), 400

    db = current_app.extensions["sqlalchemy"]

    query = text("""
        UPDATE work_logs
        SET
            approval_status = :status,
            feedback = :feedback
        WHERE work_log_id = :log_id
        RETURNING
            work_log_id,
            student_id,
            task_id,
            work_date,
            hours,
            description,
            approval_status,
            feedback
    """)

    result = db.session.execute(
        query,
        {
            "status": status,
            "feedback": feedback,
            "log_id": log_id
        }
    ).fetchone()

    if not result:
        return jsonify({
            "error": "Work log not found"
        }), 404

    db.session.commit()

    work_log = {
        "id": result.work_log_id,
        "student_id": result.student_id,
        "task_id": result.task_id,
        "date": str(result.work_date),
        "hours": float(result.hours),
        "description": result.description,
        "approval_status": result.approval_status,
        "feedback": result.feedback
    }

    return jsonify({
        "message": f"Work log {status.lower()} successfully",
        "work_log": work_log
    }), 200
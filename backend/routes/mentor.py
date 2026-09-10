from flask import Blueprint, jsonify, request

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


#Mentor Work-Log Review API

mentor_work_logs = [
    {
        "id": 1,
        "student_id": 1,
        "student_name": "Rahul",
        "task": "Create Student Dashboard",
        "hours": 6,
        "description": "Developed the student dashboard API",
        "approval_status": "Pending"
    }
]


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

    for log in mentor_work_logs:
        if log["id"] == log_id:
            log["approval_status"] = status
            log["feedback"] = feedback

            return jsonify({
                "message": f"Work log {status.lower()} successfully",
                "work_log": log
            }), 200

    return jsonify({
        "error": "Work log not found"
    }), 404
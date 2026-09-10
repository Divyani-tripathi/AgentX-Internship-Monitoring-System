from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text

mentor_bp = Blueprint("mentor", __name__)

# Mentor Intern Access API

@mentor_bp.route("/mentor/interns", methods=["GET"])
def mentor_interns():

    db = current_app.extensions["sqlalchemy"]

    query = text("""
    SELECT
        s.student_id,
        s.student_name,
        i.company_name,
        ip.tasks_completed,
        ip.total_tasks,
        ip.progress_percentage,

        COUNT(a.attendance_id) AS total_days,

        COUNT(
            CASE
                WHEN LOWER(a.status) = 'present'
                THEN 1
            END
        ) AS present_days

    FROM students s

    LEFT JOIN internships i
        ON s.student_id = i.student_id

    LEFT JOIN internship_progress ip
        ON s.student_id = ip.student_id

    LEFT JOIN attendance a
        ON s.student_id = a.student_id

    GROUP BY
        s.student_id,
        s.student_name,
        i.company_name,
        ip.tasks_completed,
        ip.total_tasks,
        ip.progress_percentage

    ORDER BY s.student_id
""")

    result = db.session.execute(query).fetchall()

    interns = []

    for row in result:

        tasks_completed = row.tasks_completed or 0
        total_tasks = row.total_tasks or 0

        task_completion = (
            round((tasks_completed / total_tasks) * 100)
            if total_tasks > 0 else 0
        )
        total_days = row.total_days or 0
        present_days = row.present_days or 0

        attendance = (
            round((present_days / total_days) * 100)
            if total_days > 0 else 0
        )
        performance = float(row.progress_percentage or 0)

        if performance >= 75:
            risk = "Low"
        elif performance >= 50:
            risk = "Medium"
        else:
            risk = "High"

        interns.append({
            "student_id": row.student_id,
            "name": row.student_name,
            "company": row.company_name,
            "attendance": attendance,
            "tasks_completed": tasks_completed,
            "total_tasks": total_tasks,
            "task_completion": task_completion,
            "performance": performance,
            "risk": risk
        })

    return jsonify(interns)

# Mentor At-Risk Students API

@mentor_bp.route("/mentor/at-risk", methods=["GET"])
def mentor_at_risk():

    db = current_app.extensions["sqlalchemy"]

    query = text("""
        SELECT
            s.student_id,
            s.student_name,
            i.company_name,
            ip.tasks_completed,
            ip.total_tasks,
            ip.progress_percentage,

            COUNT(a.attendance_id) AS total_days,

            COUNT(
                CASE
                    WHEN LOWER(a.status) = 'present'
                    THEN 1
                END
            ) AS present_days

        FROM students s

        LEFT JOIN internships i
            ON s.student_id = i.student_id

        LEFT JOIN internship_progress ip
            ON s.student_id = ip.student_id

        LEFT JOIN attendance a
            ON s.student_id = a.student_id

        GROUP BY
            s.student_id,
            s.student_name,
            i.company_name,
            ip.tasks_completed,
            ip.total_tasks,
            ip.progress_percentage

        ORDER BY ip.progress_percentage ASC
    """)

    result = db.session.execute(query).fetchall()

    at_risk_students = []

    for row in result:

        tasks_completed = row.tasks_completed or 0
        total_tasks = row.total_tasks or 0

        task_completion = (
            round((tasks_completed / total_tasks) * 100)
            if total_tasks > 0 else 0
        )

        total_days = row.total_days or 0
        present_days = row.present_days or 0

        attendance = (
            round((present_days / total_days) * 100)
            if total_days > 0 else 0
        )

        performance = float(row.progress_percentage or 0)

        if performance < 50:
            risk = "High"
        elif performance < 75:
            risk = "Medium"
        else:
            risk = "Low"

        # Only return students who need attention
        if risk in ["High", "Medium"]:

            at_risk_students.append({
                "student_id": row.student_id,
                "name": row.student_name,
                "company": row.company_name,
                "attendance": attendance,
                "task_completion": task_completion,
                "performance": performance,
                "risk": risk
            })

    return jsonify({
        "total_at_risk": len(at_risk_students),
        "students": at_risk_students
    })

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
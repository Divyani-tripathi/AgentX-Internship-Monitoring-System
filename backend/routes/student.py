from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text

student_bp = Blueprint("student", __name__)


# =========================
# STUDENT DASHBOARD
# =========================

@student_bp.route("/student/dashboard", methods=["GET"])
def student_dashboard():

    student_id = request.args.get("student_id", 1, type=int)

    db = current_app.extensions["sqlalchemy"]

    query = text("""
        SELECT
            s.student_id,
            s.student_name,
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

        LEFT JOIN internship_progress ip
            ON s.student_id = ip.student_id

        LEFT JOIN attendance a
            ON s.student_id = a.student_id

        WHERE s.student_id = :student_id

        GROUP BY
            s.student_id,
            s.student_name,
            ip.tasks_completed,
            ip.total_tasks,
            ip.progress_percentage
    """)

    result = db.session.execute(
        query,
        {"student_id": student_id}
    ).fetchone()

    if not result:
        return jsonify({
            "error": "Student not found"
        }), 404

    # Task completion
    tasks_completed = result.tasks_completed or 0
    total_tasks = result.total_tasks or 0

    if total_tasks > 0:
        task_completion = round(
            (tasks_completed / total_tasks) * 100
        )
    else:
        task_completion = 0

    # Attendance percentage
    total_days = result.total_days or 0
    present_days = result.present_days or 0

    if total_days > 0:
        attendance_percentage = round(
            (present_days / total_days) * 100
        )
    else:
        attendance_percentage = 0

    data = {
        "student_id": result.student_id,
        "name": result.student_name,

        "attendance": attendance_percentage,

        "tasks_completed": tasks_completed,
        "total_tasks": total_tasks,
        "task_completion": task_completion,

        "performance": float(
            result.progress_percentage or 0
        )
    }

    return jsonify(data)

# =========================
# STUDENT ATTENDANCE
# =========================

@student_bp.route("/student/attendance", methods=["GET"])
def student_attendance():

    student_id = request.args.get("student_id", 1, type=int)

    db = current_app.extensions["sqlalchemy"]

    query = text("""
        SELECT
            attendance_id,
            attendance_date,
            status
        FROM attendance
        WHERE student_id = :student_id
        ORDER BY attendance_date DESC
    """)

    result = db.session.execute(
        query,
        {"student_id": student_id}
    ).fetchall()

    attendance = []

    for row in result:
        attendance.append({
            "attendance_id": row.attendance_id,
            "date": str(row.attendance_date),
            "status": row.status
        })

    return jsonify({
        "student_id": student_id,
        "attendance": attendance
    })


# =========================
# STUDENT TASKS
# =========================

@student_bp.route("/student/tasks", methods=["GET"])
def student_tasks():

    student_id = request.args.get("student_id", 1, type=int)

    db = current_app.extensions["sqlalchemy"]

    query = text("""
        SELECT
            submission_id,
            task_name,
            submission_type,
            submission_link,
            screenshot_path,
            submitted_at,
            submission_status
        FROM task_submissions
        WHERE student_id = :student_id
        ORDER BY submitted_at DESC
    """)

    result = db.session.execute(
        query,
        {"student_id": student_id}
    ).fetchall()

    tasks = []

    for row in result:
        tasks.append({
            "submission_id": row.submission_id,
            "task_name": row.task_name,
            "submission_type": row.submission_type,
            "submission_link": row.submission_link,
            "screenshot_path": row.screenshot_path,
            "submitted_at": (
                str(row.submitted_at)
                if row.submitted_at
                else None
            ),
            "status": row.submission_status
        })

    return jsonify({
        "student_id": student_id,
        "tasks": tasks
    })

# =========================
# STUDENT WORK LOG
# =========================

# Temporary storage
work_logs = []


@student_bp.route("/student/work-log", methods=["POST"])
def create_work_log():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    required_fields = [
        "student_id",
        "task_id",
        "date",
        "hours",
        "description"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    work_log = {
        "id": len(work_logs) + 1,
        "student_id": data["student_id"],
        "task_id": data["task_id"],
        "date": data["date"],
        "hours": data["hours"],
        "description": data["description"],
        "approval_status": "Pending"
    }

    work_logs.append(work_log)

    return jsonify({
        "message": "Work log submitted successfully",
        "work_log": work_log
    }), 201


@student_bp.route("/student/work-logs", methods=["GET"])
def get_work_logs():

    return jsonify({
        "work_logs": work_logs
    })


# =========================
# STUDENT PERFORMANCE
# =========================

@student_bp.route("/student/performance", methods=["GET"])
def student_performance():

    student_id = request.args.get("student_id", 1, type=int)

    db = current_app.extensions["sqlalchemy"]

    query = text("""
        SELECT
            tasks_completed,
            total_tasks,
            progress_percentage
        FROM internship_progress
        WHERE student_id = :student_id
        ORDER BY last_updated DESC
        LIMIT 1
    """)

    result = db.session.execute(
        query,
        {"student_id": student_id}
    ).fetchone()

    if not result:
        return jsonify({
            "error": "Performance data not found"
        }), 404

    tasks_completed = result.tasks_completed or 0
    total_tasks = result.total_tasks or 0

    if total_tasks > 0:
        task_completion_score = round(
            (tasks_completed / total_tasks) * 100
        )
    else:
        task_completion_score = 0

    performance = {
        "task_completion_score": task_completion_score,
        "overall_score": float(
            result.progress_percentage or 0
        )
    }

    return jsonify(performance)
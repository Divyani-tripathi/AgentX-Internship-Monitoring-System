from flask import Blueprint, jsonify, current_app
from sqlalchemy import text

college_bp = Blueprint("college", __name__)


# College Performance API
@college_bp.route("/college/performance", methods=["GET"])
def college_performance():

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

    students = []

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

        students.append({
            "student_id": row.student_id,
            "name": row.student_name,
            "company": row.company_name,
            "attendance": attendance,
            "task_completion": task_completion,
            "performance": performance
        })

    return jsonify({
        "total_students": len(students),
        "students": students
    })


# College At-Risk Students API

@college_bp.route("/college/at-risk", methods=["GET"])
def college_at_risk():

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
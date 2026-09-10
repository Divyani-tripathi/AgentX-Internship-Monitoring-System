import requests


FRIEND_BACKEND_URL = "http://10.133.52.161:5000"


def fetch_student_data(student_id):
    """
    Fetch real student data from friend's backend.
    """

    url = f"{FRIEND_BACKEND_URL}/student/dashboard"

    response = requests.get(
        url,
        params={"student_id": student_id},
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def prepare_features(student_data):
    """
    Prepare dashboard data for the AI performance system.
    """

    attendance = float(student_data.get("attendance", 0))
    task_completion = float(student_data.get("task_completion", 0))

    tasks_completed = int(student_data.get("tasks_completed", 0))
    total_tasks = int(student_data.get("total_tasks", 0))

    return {
        "attendance": attendance,
        "task_completion": task_completion,
        "tasks_completed": tasks_completed,
        "total_tasks": total_tasks
    }
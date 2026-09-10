def calculate_performance_score(features):
    """
    Calculate performance score from 0 to 100.

    Attendance      = 50%
    Task Completion = 40%
    Task Submission = 10%
    """

    attendance = features.get("attendance", 0)
    task_completion = features.get("task_completion", 0)

    tasks_completed = features.get("tasks_completed", 0)
    total_tasks = features.get("total_tasks", 0)

    # Task submission percentage
    if total_tasks > 0:
        submission_percentage = (
            tasks_completed / total_tasks
        ) * 100
    else:
        submission_percentage = 0

    # Weighted score
    score = (
        attendance * 0.50
        + task_completion * 0.40
        + submission_percentage * 0.10
    )

    return round(score, 2)


def get_risk_level(score):

    if score < 40:
        return "High"
    elif score < 70:
        return "Medium"
    else:
        return "Low"
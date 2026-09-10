from preprocessing import fetch_student_data, prepare_features
from performance import calculate_performance_score, get_risk_level


def predict_student_performance(student_id):

    # Fetch real student data from friend's backend
    student_data = fetch_student_data(student_id)

    # Prepare features
    features = prepare_features(student_data)

    # Calculate performance score
    score = calculate_performance_score(features)

    # Calculate risk level
    risk_level = get_risk_level(score)

    return {
        "student_id": student_id,
        "name": student_data.get("name"),
        "performance_score": score,
        "risk_level": risk_level,
        "features": features
    }


if __name__ == "__main__":

    result = predict_student_performance(1)

    print("\n===== AI RESULT =====")
    print("Student ID:", result["student_id"])
    print("Name:", result["name"])
    print("Features:", result["features"])
    print("Performance Score:", result["performance_score"])
    print("Risk Level:", result["risk_level"])
    print("=====================\n")
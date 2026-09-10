from flask import Flask, request, jsonify
from predict import predict_student_performance

app = Flask(__name__)


@app.route("/ai/predict", methods=["GET"])
def ai_predict():

    # Get student ID from URL
    student_id = request.args.get("student_id", type=int)

    if student_id is None:
        return jsonify({
            "error": "student_id is required"
        }), 400

    try:
        # Run AI prediction
        result = predict_student_performance(student_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/")
def home():
    return "AgentX AI Service is Running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
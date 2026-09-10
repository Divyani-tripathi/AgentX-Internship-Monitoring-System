from flask import Blueprint, request, jsonify, render_template_string
from sqlalchemy import text
from flask import current_app
from datetime import datetime
import math
import uuid
import io
import qrcode


attendance_bp = Blueprint("attendance", __name__)

ALLOWED_RADIUS_METERS = 100


def get_db():
    return current_app.extensions["sqlalchemy"].db


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS coordinates using Haversine formula.
    Returns distance in meters.
    """

    R = 6371000  # Earth radius in meters

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ---------------------------------------------------------
# MENTOR PAGE
# ---------------------------------------------------------

@attendance_bp.route("/attendance/mentor", methods=["GET"])
def mentor_attendance_page():

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>AgentX - Mentor Attendance</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            text-align: center;
        }

        input, button {
            padding: 12px;
            margin: 8px;
            font-size: 16px;
        }

        button {
            cursor: pointer;
        }

        #qr {
            margin-top: 25px;
        }

        img {
            max-width: 300px;
        }

        table {
            width: 100%;
            margin-top: 25px;
            border-collapse: collapse;
        }

        th, td {
            border: 1px solid #ccc;
            padding: 10px;
        }

        th {
            background: #eee;
        }

        .success {
            color: green;
            font-weight: bold;
        }

        .error {
            color: red;
            font-weight: bold;
        }
    </style>
</head>

<body>

<h1>📱 AgentX QR Attendance</h1>

<p>Enter the subject and allow your browser to access your GPS location.</p>

<input
    id="subject"
    type="text"
    placeholder="Subject / Session"
>

<br>

<button onclick="createSession()">
    📍 Get GPS & Generate QR
</button>

<div id="message"></div>

<div id="qr"></div>

<h2>Live Attendance</h2>

<table>
    <thead>
        <tr>
            <th>Student ID</th>
            <th>Name</th>
            <th>Distance</th>
            <th>Time</th>
            <th>Status</th>
        </tr>
    </thead>

    <tbody id="attendanceBody">
        <tr>
            <td colspan="5">No active session</td>
        </tr>
    </tbody>
</table>


<script>

let currentSession = null;
let polling = null;


function createSession() {

    const subject = document.getElementById("subject").value.trim();

    if (!subject) {
        showMessage("Please enter subject.", true);
        return;
    }

    if (!navigator.geolocation) {
        showMessage("GPS is not supported by this browser.", true);
        return;
    }

    showMessage("Getting mentor GPS location...");

    navigator.geolocation.getCurrentPosition(

        async function(position) {

            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            try {

                const response = await fetch("/attendance/create-session", {

                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        subject: subject,
                        latitude: lat,
                        longitude: lon
                    })

                });

                const data = await response.json();

                if (!response.ok) {
                    showMessage(data.message || "Failed to create session.", true);
                    return;
                }

                currentSession = data.session_id;

                document.getElementById("qr").innerHTML = `
                    <h2>Scan this QR Code</h2>
                    <img src="${data.qr_url}">
                    <p>Students should scan this QR using their phone.</p>
                    <p><b>Session:</b> ${data.session_id}</p>
                `;

                showMessage(
                    "Attendance session created successfully."
                );

                startPolling();

            } catch (error) {

                showMessage(
                    "Server error: " + error,
                    true
                );

            }

        },

        function(error) {

            showMessage(
                "GPS permission is required. Please allow location access.",
                true
            );

        },

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }

    );
}


function startPolling() {

    if (polling) {
        clearInterval(polling);
    }

    loadAttendance();

    polling = setInterval(loadAttendance, 3000);
}


async function loadAttendance() {

    if (!currentSession) {
        return;
    }

    try {

        const response = await fetch(
            "/attendance/session/" + currentSession
        );

        const data = await response.json();

        const tbody = document.getElementById(
            "attendanceBody"
        );

        if (!data.students || data.students.length === 0) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="5">
                        Waiting for students...
                    </td>
                </tr>
            `;

            return;
        }

        tbody.innerHTML = "";

        data.students.forEach(student => {

            tbody.innerHTML += `
                <tr>
                    <td>${student.student_id}</td>
                    <td>${student.student_name}</td>
                    <td>${student.distance_m} m</td>
                    <td>${student.marked_at}</td>
                    <td class="success">
                        ${student.status}
                    </td>
                </tr>
            `;

        });

    } catch (error) {

        console.log(error);

    }
}


function showMessage(message, error=false) {

    const element = document.getElementById("message");

    element.innerHTML = message;

    element.className = error ? "error" : "success";

}

</script>

</body>
</html>
""")


# ---------------------------------------------------------
# CREATE ATTENDANCE SESSION
# ---------------------------------------------------------

@attendance_bp.route("/attendance/create-session", methods=["POST"])
def create_session():

    data = request.get_json() or {}

    subject = data.get("subject")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not subject:
        return jsonify({
            "message": "Subject is required."
        }), 400

    if latitude is None or longitude is None:
        return jsonify({
            "message": "Mentor GPS location is required."
        }), 400

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except ValueError:

        return jsonify({
            "message": "Invalid GPS coordinates."
        }), 400

    session_id = str(uuid.uuid4())

    db = get_db()

    try:

        # Close previous active sessions
        db.session.execute(
            text("""
                UPDATE attendance_sessions
                SET active = FALSE
                WHERE active = TRUE
            """)
        )

        # Create new session
        db.session.execute(
            text("""
                INSERT INTO attendance_sessions
                (
                    session_id,
                    subject,
                    mentor_lat,
                    mentor_lon,
                    created_at,
                    active
                )
                VALUES
                (
                    :session_id,
                    :subject,
                    :lat,
                    :lon,
                    CURRENT_TIMESTAMP,
                    TRUE
                )
            """),
            {
                "session_id": session_id,
                "subject": subject,
                "lat": latitude,
                "lon": longitude
            }
        )

        db.session.commit()

        # Get correct HTTPS/HTTP URL from current request
        scan_url = (
            request.host_url.rstrip("/")
            + "/attendance/scan?session="
            + session_id
        )

        # Generate QR
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4
        )

        qr.add_data(scan_url)
        qr.make(fit=True)

        image = qr.make_image()

        # Store QR temporarily as data URL
        import base64

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        qr_base64 = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        qr_url = (
            "data:image/png;base64,"
            + qr_base64
        )

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "scan_url": scan_url,
            "qr_url": qr_url
        })

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "message": str(e)
        }), 500


# ---------------------------------------------------------
# QR SCAN PAGE
# ---------------------------------------------------------

@attendance_bp.route("/attendance/scan", methods=["GET"])
def scan_page():

    session_id = request.args.get("session")

    if not session_id:
        return "Invalid attendance session.", 400

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<title>AgentX Student Attendance</title>

<style>

body {
    font-family: Arial;
    max-width: 500px;
    margin: 40px auto;
    padding: 20px;
    text-align: center;
}

input, button {
    width: 90%;
    padding: 14px;
    margin: 10px;
    font-size: 18px;
}

button {
    cursor: pointer;
}

.success {
    color: green;
    font-weight: bold;
}

.error {
    color: red;
    font-weight: bold;
}

</style>

</head>

<body>

<h1>🎓 Student Attendance</h1>

<p>Enter your Student ID.</p>

<input
    id="studentId"
    type="number"
    placeholder="Student ID"
>

<button onclick="markAttendance()">
    📍 Allow GPS & Mark Attendance
</button>

<div id="message"></div>

<script>

async function markAttendance() {

    const studentId =
        document.getElementById("studentId").value;

    if (!studentId) {

        showMessage(
            "Please enter your Student ID.",
            true
        );

        return;
    }

    if (!navigator.geolocation) {

        showMessage(
            "GPS is not supported.",
            true
        );

        return;
    }

    showMessage(
        "Getting your GPS location..."
    );

    navigator.geolocation.getCurrentPosition(

        async function(position) {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;

            try {

                const response = await fetch(
                    "/attendance/mark",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            session_id:
                                SESSION_ID,

                            student_id:
                                parseInt(studentId),

                            latitude:
                                latitude,

                            longitude:
                                longitude

                        })
                    }
                );

                const data =
                    await response.json();

                if (!response.ok) {

                    showMessage(
                        data.message ||
                        "Attendance failed.",
                        true
                    );

                    return;
                }

                showMessage(
                    "✅ " + data.message
                );

            } catch (error) {

                showMessage(
                    "Server error: " + error,
                    true
                );

            }

        },

        function(error) {

            showMessage(
                "Please allow GPS/location permission.",
                true
            );

        },

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }

    );
}


function showMessage(message, error=false) {

    const element =
        document.getElementById("message");

    element.innerHTML = message;

    element.className =
        error ? "error" : "success";

}


const SESSION_ID = {{ session_id|tojson }};

</script>

</body>

</html>
""", session_id=session_id)


# ---------------------------------------------------------
# MARK ATTENDANCE
# ---------------------------------------------------------

@attendance_bp.route("/attendance/mark", methods=["POST"])
def mark_attendance():

    data = request.get_json() or {}

    session_id = data.get("session_id")
    student_id = data.get("student_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not all([
        session_id,
        student_id,
        latitude is not None,
        longitude is not None
    ]):

        return jsonify({
            "message": "All attendance details are required."
        }), 400

    try:

        student_id = int(student_id)
        latitude = float(latitude)
        longitude = float(longitude)

    except ValueError:

        return jsonify({
            "message": "Invalid student ID or GPS coordinates."
        }), 400

    db = get_db()

    try:

        # -------------------------------------------------
        # Check session
        # -------------------------------------------------

        session = db.session.execute(
            text("""
                SELECT
                    session_id,
                    mentor_lat,
                    mentor_lon,
                    active
                FROM attendance_sessions
                WHERE session_id = :session_id
            """),
            {
                "session_id": session_id
            }
        ).mappings().first()

        if not session:

            return jsonify({
                "message": "Attendance session not found."
            }), 404

        if not session["active"]:

            return jsonify({
                "message": "This attendance session is closed."
            }), 400

        # -------------------------------------------------
        # Check student
        # -------------------------------------------------

        student = db.session.execute(
            text("""
                SELECT
                    student_id,
                    student_name
                FROM students
                WHERE student_id = :student_id
            """),
            {
                "student_id": student_id
            }
        ).mappings().first()

        if not student:

            return jsonify({
                "message": "Student ID not found."
            }), 404

        # -------------------------------------------------
        # Calculate GPS distance
        # -------------------------------------------------

        distance = calculate_distance(
            session["mentor_lat"],
            session["mentor_lon"],
            latitude,
            longitude
        )

        distance = round(distance, 2)

        # -------------------------------------------------
        # GPS validation
        # -------------------------------------------------

        if distance > ALLOWED_RADIUS_METERS:

            return jsonify({
                "message": (
                    "Attendance rejected. "
                    "You are "
                    + str(distance)
                    + " meters away. "
                    "You must be within "
                    + str(ALLOWED_RADIUS_METERS)
                    + " meters."
                ),
                "distance_m": distance
            }), 403

        # -------------------------------------------------
        # Duplicate check for today's attendance
        # -------------------------------------------------

        existing = db.session.execute(
            text("""
                SELECT attendance_id
                FROM attendance
                WHERE student_id = :student_id
                AND attendance_date = CURRENT_DATE
                LIMIT 1
            """),
            {
                "student_id": student_id
            }
        ).first()

        if existing:

            return jsonify({
                "message": "Attendance already marked today.",
                "distance_m": distance
            }), 409

        # -------------------------------------------------
        # Insert into existing attendance table
        # -------------------------------------------------

        db.session.execute(
            text("""
                INSERT INTO attendance
                (
                    student_id,
                    attendance_date,
                    status
                )
                VALUES
                (
                    :student_id,
                    CURRENT_DATE,
                    'Present'
                )
            """),
            {
                "student_id": student_id
            }
        )

        # -------------------------------------------------
        # Insert GPS/session record
        # -------------------------------------------------

        db.session.execute(
            text("""
                INSERT INTO attendance_session_records
                (
                    session_id,
                    student_id,
                    student_lat,
                    student_lon,
                    distance_m,
                    marked_at
                )
                VALUES
                (
                    :session_id,
                    :student_id,
                    :lat,
                    :lon,
                    :distance,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (session_id, student_id)
                DO NOTHING
            """),
            {
                "session_id": session_id,
                "student_id": student_id,
                "lat": latitude,
                "lon": longitude,
                "distance": distance
            }
        )

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": (
                "Attendance marked successfully "
                "for " + student["student_name"]
            ),
            "student_id": student_id,
            "distance_m": distance
        })

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "message": str(e)
        }), 500


# ---------------------------------------------------------
# LIVE SESSION ATTENDANCE
# ---------------------------------------------------------

@attendance_bp.route(
    "/attendance/session/<session_id>",
    methods=["GET"]
)
def session_attendance(session_id):

    db = get_db()

    try:

        rows = db.session.execute(
            text("""
                SELECT
                    r.student_id,
                    s.student_name,
                    r.distance_m,
                    r.marked_at,
                    'Present' AS status
                FROM attendance_session_records r
                JOIN students s
                    ON s.student_id = r.student_id
                WHERE r.session_id = :session_id
                ORDER BY r.marked_at ASC
            """),
            {
                "session_id": session_id
            }
        ).mappings().all()

        students = []

        for row in rows:

            marked_at = row["marked_at"]

            if isinstance(marked_at, datetime):

                marked_at = marked_at.strftime(
                    "%H:%M:%S"
                )

            students.append({

                "student_id":
                    row["student_id"],

                "student_name":
                    row["student_name"],

                "distance_m":
                    round(float(row["distance_m"]), 2),

                "marked_at":
                    marked_at,

                "status":
                    row["status"]

            })

        return jsonify({
            "session_id": session_id,
            "students": students
        })

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

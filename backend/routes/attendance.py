from flask import Blueprint, jsonify, request, Response
from datetime import datetime, timedelta, timezone
import io
import math
import secrets
import qrcode


# ============================================================
# ATTENDANCE BLUEPRINT
# ============================================================

attendance_bp = Blueprint("attendance", __name__)


# ============================================================
# CONFIGURATION
# ============================================================

SESSION_DURATION_MINUTES = 30

# Temporary company location
# Change these later to the actual company location.
COMPANY_LATITUDE = 21.1458
COMPANY_LONGITUDE = 79.0882

# For testing/demo.
# After testing, change this to 150.
ALLOWED_RADIUS_METERS = 500000


# ============================================================
# TEMPORARY MEMORY STORAGE
# ============================================================

active_session = None
attendance_records = []


# ============================================================
# GPS DISTANCE CALCULATION
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371000

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ============================================================
# CHECK ACTIVE SESSION
# ============================================================

def session_is_valid(session_id):

    global active_session

    if active_session is None:
        return False

    if session_id != active_session["id"]:
        return False

    now = datetime.now(timezone.utc)

    if now >= active_session["expires_at"]:
        return False

    return True


# ============================================================
# MENTOR ATTENDANCE PAGE
# ============================================================

@attendance_bp.route("/attendance/mentor")
def mentor_attendance():

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <meta name="viewport"
              content="width=device-width, initial-scale=1">

        <title>Mentor Attendance</title>

    </head>

    <body style="
        font-family:Arial;
        text-align:center;
        padding:30px;
        background:#f5f5f5;
    ">

        <div style="
            background:white;
            max-width:600px;
            margin:auto;
            padding:30px;
            border-radius:15px;
        ">

            <h1>🏢 AgentX</h1>

            <h2>Internship Attendance</h2>

            <p>
                Start a new attendance session.
            </p>

            <p>
                QR will remain valid for
                <b>30 minutes</b>.
            </p>

            <br>

            <a href="/attendance/start">

                <button style="
                    padding:15px 30px;
                    font-size:18px;
                    border-radius:10px;
                    cursor:pointer;
                ">

                    START ATTENDANCE

                </button>

            </a>

            <br><br>

            <a href="/attendance/records">
                View Attendance Records
            </a>

        </div>

    </body>

    </html>
    """


# ============================================================
# START NEW ATTENDANCE SESSION
# ============================================================

@attendance_bp.route("/attendance/start")
def start_attendance():

    global active_session

    session_id = secrets.token_urlsafe(20)

    started_at = datetime.now(timezone.utc)

    expires_at = (
        started_at
        + timedelta(minutes=SESSION_DURATION_MINUTES)
    )

    active_session = {

        "id": session_id,

        "started_at": started_at,

        "expires_at": expires_at

    }

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <meta name="viewport"
              content="width=device-width, initial-scale=1">

        <title>Attendance QR</title>

    </head>

    <body style="
        font-family:Arial;
        text-align:center;
        padding:20px;
        background:#f5f5f5;
    ">

        <div style="
            background:white;
            max-width:600px;
            margin:auto;
            padding:25px;
            border-radius:15px;
        ">

            <h1>✅ Attendance Started</h1>

            <h2>Scan this QR</h2>

            <img
                src="/attendance/qr"
                width="320"
                alt="Attendance QR"
            >

            <h3>⏱️ Valid for 30 minutes</h3>

            <p>
                Students should scan this QR using their phone.
            </p>

            <br>

            <a href="/attendance/records">
                View Attendance Records
            </a>

        </div>

    </body>

    </html>
    """


# ============================================================
# GENERATE QR CODE
# ============================================================

@attendance_bp.route("/attendance/qr")
def generate_qr():

    if active_session is None:

        return Response(
            "No active attendance session.",
            status=404
        )

    if not session_is_valid(active_session["id"]):

        return Response(
            "QR EXPIRED. Please start a new attendance session.",
            status=410
        )

    # The QR uses the current HTTPS website address.
    # This works when the backend is deployed on an HTTPS server.

    base_url = request.url_root.rstrip("/")

    scan_url = (
        base_url
        + "/attendance/scan/"
        + active_session["id"]
    )

    qr = qrcode.QRCode(

        version=1,

        error_correction=qrcode.constants.ERROR_CORRECT_M,

        box_size=10,

        border=4

    )

    qr.add_data(scan_url)

    qr.make(fit=True)

    image = qr.make_image()

    image_bytes = io.BytesIO()

    image.save(
        image_bytes,
        format="PNG"
    )

    image_bytes.seek(0)

    return Response(
        image_bytes.getvalue(),
        mimetype="image/png"
    )


# ============================================================
# STUDENT SCAN PAGE
# ============================================================

@attendance_bp.route("/attendance/scan/<session_id>")
def scan_attendance(session_id):

    if not session_is_valid(session_id):

        return """
        <!DOCTYPE html>

        <html>

        <body style="
            font-family:Arial;
            text-align:center;
            padding:40px;
        ">

            <h1>❌ QR EXPIRED</h1>

            <p>
                This attendance QR is no longer valid.
            </p>

            <p>
                Please scan the new QR displayed by the mentor.
            </p>

        </body>

        </html>
        """, 410


    return """
    <!DOCTYPE html>

    <html>

    <head>

        <meta name="viewport"
              content="width=device-width, initial-scale=1">

        <title>Student Attendance</title>

        <style>

            body {
                font-family: Arial;
                background: #f5f5f5;
                text-align: center;
                padding: 20px;
            }

            .box {
                background: white;
                max-width: 500px;
                margin: auto;
                padding: 25px;
                border-radius: 15px;
            }

            input {
                width: 90%;
                max-width: 350px;
                padding: 14px;
                font-size: 18px;
                border: 1px solid #aaa;
                border-radius: 8px;
            }

            button {
                padding: 15px 25px;
                font-size: 18px;
                border-radius: 10px;
                cursor: pointer;
            }

            #result {
                margin-top: 20px;
                font-size: 17px;
            }

        </style>

    </head>


    <body>

        <div class="box">

            <h1>🎓 Student Attendance</h1>

            <h2>QR Verified ✅</h2>

            <p>
                Enter your Student ID
            </p>

            <input
                id="student_id"
                type="text"
                placeholder="Enter Student ID"
            >

            <br><br>

            <button onclick="markAttendance()">

                📍 MARK ATTENDANCE

            </button>

            <div id="result"></div>

        </div>


        <script>

        function markAttendance() {

            var studentId =
                document.getElementById("student_id")
                .value
                .trim();


            if (!studentId) {

                document.getElementById("result")
                    .innerHTML =
                    "❌ Please enter Student ID.";

                return;

            }


            document.getElementById("result")
                .innerHTML =
                "📍 Requesting GPS location...";


            if (!navigator.geolocation) {

                document.getElementById("result")
                    .innerHTML =
                    "❌ GPS is not supported by this browser.";

                return;

            }


            navigator.geolocation.getCurrentPosition(

                function(position) {

                    var latitude =
                        position.coords.latitude;

                    var longitude =
                        position.coords.longitude;


                    document.getElementById("result")
                        .innerHTML =
                        "📍 GPS received. Marking attendance...";


                    fetch(
                        "/attendance/mark",
                        {

                            method: "POST",

                            headers: {
                                "Content-Type":
                                "application/json"
                            },

                            body: JSON.stringify({

                                student_id:
                                studentId,

                                session_id:
                                "__SESSION_ID__",

                                latitude:
                                latitude,

                                longitude:
                                longitude

                            })

                        }
                    )

                    .then(function(response) {

                        return response.json();

                    })

                    .then(function(data) {

                        document.getElementById("result")
                            .innerHTML =
                            data.message;

                    })

                    .catch(function(error) {

                        document.getElementById("result")
                            .innerHTML =
                            "❌ Server connection failed. Please try again.";

                    });

                },


                function(error) {

                    document.getElementById("result")
                        .innerHTML =
                        "❌ Please allow Location/GPS permission and try again.";

                },


                {

                    enableHighAccuracy: true,

                    timeout: 15000,

                    maximumAge: 0

                }

            );

        }

        </script>

    </body>

    </html>
    """.replace(
        "__SESSION_ID__",
        session_id
    )


# ============================================================
# MARK ATTENDANCE
# ============================================================

@attendance_bp.route(
    "/attendance/mark",
    methods=["POST"]
)
def mark_attendance():

    if active_session is None:

        return jsonify({

            "success": False,

            "message":
            "❌ No active attendance session."

        }), 400


    now = datetime.now(timezone.utc)


    if now >= active_session["expires_at"]:

        return jsonify({

            "success": False,

            "message":
            "❌ QR expired. Please scan the new QR."

        }), 410


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success": False,

            "message":
            "❌ Invalid request."

        }), 400


    student_id = data.get(
        "student_id"
    )

    session_id = data.get(
        "session_id"
    )

    latitude = data.get(
        "latitude"
    )

    longitude = data.get(
        "longitude"
    )


    # --------------------------------------------------------
    # STUDENT ID
    # --------------------------------------------------------

    if not student_id:

        return jsonify({

            "success": False,

            "message":
            "❌ Student ID is required."

        }), 400


    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    if session_id != active_session["id"]:

        return jsonify({

            "success": False,

            "message":
            "❌ Invalid or expired QR."

        }), 400


    # --------------------------------------------------------
    # GPS
    # --------------------------------------------------------

    if latitude is None or longitude is None:

        return jsonify({

            "success": False,

            "message":
            "❌ GPS location is required."

        }), 400


    try:

        latitude = float(latitude)

        longitude = float(longitude)

    except ValueError:

        return jsonify({

            "success": False,

            "message":
            "❌ Invalid GPS coordinates."

        }), 400


    # --------------------------------------------------------
    # DISTANCE
    # --------------------------------------------------------

    distance = calculate_distance(

        latitude,

        longitude,

        COMPANY_LATITUDE,

        COMPANY_LONGITUDE

    )


    if distance > ALLOWED_RADIUS_METERS:

        return jsonify({

            "success": False,

            "message":
            "❌ You are outside the allowed company location."

        }), 403


    # --------------------------------------------------------
    # DUPLICATE CHECK
    # --------------------------------------------------------

    for record in attendance_records:

        if (

            record["student_id"]
            == student_id

            and

            record["session_id"]
            == session_id

        ):

            return jsonify({

                "success": False,

                "message":
                "⚠️ Attendance already marked for this session."

            }), 409


    # --------------------------------------------------------
    # SERVER TIMESTAMP
    # --------------------------------------------------------

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


    # --------------------------------------------------------
    # SAVE RECORD
    # --------------------------------------------------------

    record = {

        "student_id":
        student_id,

        "session_id":
        session_id,

        "latitude":
        latitude,

        "longitude":
        longitude,

        "distance_meters":
        round(distance, 2),

        "timestamp":
        timestamp,

        "status":
        "PRESENT"

    }


    attendance_records.append(
        record
    )


    return jsonify({

        "success": True,

        "message":
        "✅ ATTENDANCE MARKED SUCCESSFULLY"
        "<br><br>"
        "Student ID: "
        + str(student_id)
        + "<br>"
        "Status: PRESENT"
        + "<br>"
        "Server Time: "
        + timestamp
        + "<br>"
        "GPS Location: "
        + str(latitude)
        + ", "
        + str(longitude)

    })


# ============================================================
# ATTENDANCE RECORDS
# ============================================================

@attendance_bp.route(
    "/attendance/records"
)
def attendance_records_page():

    rows = ""

    for record in attendance_records:

        rows += """

        <tr>

            <td>{}</td>

            <td>{}</td>

            <td>{}</td>

            <td>{}</td>

            <td>{}</td>

            <td>{} m</td>

        </tr>

        """.format(

            record["student_id"],

            record["status"],

            record["timestamp"],

            record["latitude"],

            record["longitude"],

            record["distance_meters"]

        )


    return """

    <!DOCTYPE html>

    <html>

    <head>

        <meta name="viewport"
              content="width=device-width, initial-scale=1">

        <title>Attendance Records</title>

    </head>

    <body style="
        font-family:Arial;
        padding:20px;
    ">

        <h1>📋 Attendance Records</h1>

        <table
            border="1"
            cellpadding="10"
            cellspacing="0"
        >

            <tr>

                <th>Student ID</th>

                <th>Status</th>

                <th>Timestamp</th>

                <th>Latitude</th>

                <th>Longitude</th>

                <th>Distance</th>

            </tr>

            {}

        </table>

        <br>

        <a href="/attendance/mentor">
            Back to Mentor Page
        </a>

    </body>

    </html>

    """.format(rows)

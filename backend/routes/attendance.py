from flask import Blueprint, jsonify, request, Response
from datetime import datetime, timedelta, timezone
import io
import math
import secrets
import qrcode

attendance_bp = Blueprint("attendance", __name__)

# =========================================================
# CONFIGURATION
# =========================================================

# Each attendance QR session is valid for 30 minutes
SESSION_DURATION_MINUTES = 30

# TEMPORARY COMPANY LOCATION
# Change these later to the actual internship/company location
COMPANY_LATITUDE = 21.1458
COMPANY_LONGITUDE = 79.0882

# Student must be within 150 meters of company location
ALLOWED_RADIUS_METERS = 150

# For local testing this is None.
# After deployment, put your public HTTPS backend URL here.
# Example:
# PUBLIC_BASE_URL = "https://your-app.onrender.com"
PUBLIC_BASE_URL = None


# =========================================================
# TEMPORARY STORAGE
# =========================================================

active_session = None
attendance_records = []


# =========================================================
# TIME
# =========================================================

def utc_now():
    return datetime.now(timezone.utc)


# =========================================================
# GPS DISTANCE
# =========================================================

def haversine_meters(lat1, lon1, lat2, lon2):

    earth_radius = 6371000

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


# =========================================================
# CHECK ACTIVE SESSION
# =========================================================

def session_is_active():

    global active_session

    if active_session is None:
        return False

    if utc_now() >= active_session["expires_at"]:

        active_session = None

        return False

    return True


# =========================================================
# MENTOR ATTENDANCE PAGE
# =========================================================

@attendance_bp.route("/attendance/mentor", methods=["GET"])
def mentor_page():

    return """
<!DOCTYPE html>

<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Mentor Attendance</title>

<style>

body {
    font-family: Arial;
    text-align: center;
    padding: 30px;
}

button {
    padding: 12px 25px;
    font-size: 18px;
    cursor: pointer;
}

img {
    width: 280px;
    margin-top: 20px;
}

#status {
    margin: 20px;
    font-weight: bold;
}

</style>

</head>

<body>

<h1>Mentor Attendance</h1>

<p>QR attendance session is valid for 30 minutes.</p>

<button onclick="startAttendance()">
Start Attendance
</button>

<div id="status">
No active attendance session
</div>

<img id="qr" style="display:none;">

<script>

async function startAttendance() {

    const response = await fetch(
        "/attendance/start",
        {
            method: "POST"
        }
    );

    const data = await response.json();

    if (!response.ok) {

        document.getElementById("status").innerText =
            data.error || "Unable to start attendance";

        return;
    }

    document.getElementById("status").innerText =
        "Attendance started. QR is valid for 30 minutes.";

    const qr = document.getElementById("qr");

    qr.src = "/attendance/qr?t=" + Date.now();

    qr.style.display = "inline-block";
}

</script>

</body>

</html>
"""


# =========================================================
# START ATTENDANCE SESSION
# =========================================================

@attendance_bp.route("/attendance/start", methods=["GET", "POST"])
def start_attendance():

    global active_session
    global attendance_records

    now = utc_now()

    session_id = secrets.token_urlsafe(24)

    expires_at = now + timedelta(
        minutes=SESSION_DURATION_MINUTES
    )

    active_session = {

        "session_id": session_id,

        "started_at": now,

        "expires_at": expires_at

    }

    # New session gets a new attendance list
    attendance_records = []

    return jsonify({

        "success": True,

        "message": "Attendance session started",

        "session_id": session_id,

        "duration_minutes": SESSION_DURATION_MINUTES,

        "started_at": now.isoformat(),

        "expires_at": expires_at.isoformat()

    })


# =========================================================
# GENERATE QR CODE
# =========================================================

@attendance_bp.route("/attendance/qr", methods=["GET"])
def attendance_qr():

    if not session_is_active():

        return jsonify({

            "success": False,

            "error":
            "No active attendance session. Open /attendance/mentor first."

        }), 400

    session_id = active_session["session_id"]

    if PUBLIC_BASE_URL:

        base_url = PUBLIC_BASE_URL.rstrip("/")

    else:

        base_url = request.host_url.rstrip("/")

    scan_url = (
        f"{base_url}/attendance/scan/{session_id}"
    )

    qr = qrcode.QRCode(

        version=1,

        box_size=10,

        border=4

    )

    qr.add_data(scan_url)

    qr.make(fit=True)

    image = qr.make_image(

        fill_color="black",

        back_color="white"

    )

    output = io.BytesIO()

    image.save(

        output,

        format="PNG"

    )

    output.seek(0)

    return Response(

        output.getvalue(),

        mimetype="image/png"

    )


# =========================================================
# ATTENDANCE STATUS
# =========================================================

@attendance_bp.route("/attendance/status", methods=["GET"])
def attendance_status():

    if not session_is_active():

        return jsonify({

            "active": False,

            "message":
            "No active attendance session"

        })

    remaining_seconds = int(

        (
            active_session["expires_at"]
            - utc_now()
        ).total_seconds()

    )

    return jsonify({

        "active": True,

        "session_id":
        active_session["session_id"],

        "remaining_seconds":
        max(0, remaining_seconds),

        "expires_at":
        active_session["expires_at"].isoformat()

    })


# =========================================================
# STUDENT QR SCAN PAGE
# =========================================================

@attendance_bp.route(
    "/attendance/scan/<session_id>",
    methods=["GET"]
)
def scan_page(session_id):

    if not session_is_active():

        return """

        <h2>QR Expired</h2>

        <p>
        This attendance session has expired.
        Please ask the mentor for a new QR.
        </p>

        """, 410

    if session_id != active_session["session_id"]:

        return """

        <h2>Invalid QR</h2>

        <p>
        This QR does not belong to the current
        attendance session.
        </p>

        """, 400

    return f"""

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Mark Attendance</title>

<style>

body {{

    font-family: Arial;

    text-align: center;

    padding: 25px;

}}

input {{

    padding: 12px;

    font-size: 17px;

    width: 90%;

    max-width: 320px;

}}

button {{

    padding: 12px 22px;

    font-size: 17px;

    margin-top: 15px;

}}

#result {{

    margin-top: 20px;

    font-weight: bold;

}}

</style>

</head>

<body>

<h2>Internship Attendance</h2>

<p>
Enter your Student ID and allow location access.
</p>

<input
    id="student_id"
    placeholder="Enter Student ID"
>

<br>

<button onclick="markAttendance()">

Mark Attendance

</button>

<div id="result"></div>

<script>

async function markAttendance() {{

    const studentId =
        document
        .getElementById("student_id")
        .value
        .trim();

    const result =
        document
        .getElementById("result");

    if (!studentId) {{

        result.innerText =
            "Please enter Student ID.";

        return;

    }}

    if (!navigator.geolocation) {{

        result.innerText =
            "GPS is not supported on this device.";

        return;

    }}

    result.innerText =
        "Getting your location...";

    navigator.geolocation.getCurrentPosition(

        async (position) => {{

            const response =
                await fetch(

                    "/attendance/mark",

                    {{

                        method: "POST",

                        headers: {{

                            "Content-Type":
                            "application/json"

                        }},

                        body: JSON.stringify({{

                            session_id:
                            "{session_id}",

                            student_id:
                            studentId,

                            latitude:
                            position.coords.latitude,

                            longitude:
                            position.coords.longitude

                        }})

                    }}

                );

            const data =
                await response.json();

            result.innerText =
                data.message ||
                data.error ||
                "Attendance response received.";

        }},

        () => {{

            result.innerText =
                "Location permission is required.";

        }},

        {{

            enableHighAccuracy: true,

            timeout: 10000

        }}

    );

}}

</script>

</body>

</html>

"""


# =========================================================
# MARK ATTENDANCE
# =========================================================

@attendance_bp.route(
    "/attendance/mark",
    methods=["POST"]
)
def mark_attendance():

    if not session_is_active():

        return jsonify({

            "success": False,

            "error":
            "Attendance session has expired."

        }), 410

    data = request.get_json(
        silent=True
    ) or {}

    student_id = str(
        data.get("student_id", "")
    ).strip()

    session_id = data.get(
        "session_id"
    )

    latitude = data.get(
        "latitude"
    )

    longitude = data.get(
        "longitude"
    )

    if not student_id:

        return jsonify({

            "success": False,

            "error":
            "Student ID is required."

        }), 400

    if session_id != active_session["session_id"]:

        return jsonify({

            "success": False,

            "error":
            "Invalid attendance session."

        }), 400

    try:

        latitude = float(latitude)

        longitude = float(longitude)

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "success": False,

            "error":
            "Valid GPS coordinates are required."

        }), 400

    # Prevent duplicate attendance
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

                "error":
                "Attendance already marked for this session."

            }), 409

    # Calculate distance from company
    distance = haversine_meters(

        latitude,

        longitude,

        COMPANY_LATITUDE,

        COMPANY_LONGITUDE

    )

    # GPS validation
    if distance > ALLOWED_RADIUS_METERS:

        return jsonify({

            "success": False,

            "error":
            "You are outside the allowed attendance location.",

            "distance_meters":
            round(distance, 2)

        }), 403

    # SERVER-GENERATED TIMESTAMP
    record = {

        "student_id":
        student_id,

        "session_id":
        session_id,

        "status":
        "PRESENT",

        "timestamp":
        utc_now().isoformat(),

        "latitude":
        latitude,

        "longitude":
        longitude,

        "distance_meters":
        round(distance, 2)

    }

    attendance_records.append(
        record
    )

    return jsonify({

        "success": True,

        "message":
        "Attendance marked successfully.",

        "attendance":
        record

    })


# =========================================================
# VIEW ATTENDANCE RECORDS
# =========================================================

@attendance_bp.route(
    "/attendance/records",
    methods=["GET"]
)
def attendance_records_view():

    return jsonify({

        "count":
        len(attendance_records),

        "records":
        attendance_records

    })

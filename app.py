from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.exceptions import BadRequest

from config import Config
from models import db, Track


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

USERNAME = "admin"
PASSWORD = "admin123"


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def clean_boolean(value):
    if value in [True, "true", "True", "1", 1, "yes", "Yes"]:
        return True
    return False


def validate_track_data(data, partial=False):
    allowed_fields = {"title", "artist", "album", "genre", "year", "is_hit"}
    required_fields = {"title", "artist", "album", "genre", "year"}

    if not isinstance(data, dict):
        return None, "JSON body is required."

    unknown_fields = set(data.keys()) - allowed_fields
    if unknown_fields:
        return None, f"Unknown field(s): {', '.join(unknown_fields)}"

    cleaned_data = {}

    for field in ["title", "artist", "album", "genre"]:
        if field in data:
            cleaned_data[field] = clean_text(data.get(field))

    if "year" in data:
        try:
            year = int(data.get("year"))
            if year < 1900 or year > 2100:
                return None, "Year must be between 1900 and 2100."
            cleaned_data["year"] = year
        except ValueError:
            return None, "Year must be a valid number."

    if "is_hit" in data:
        cleaned_data["is_hit"] = clean_boolean(data.get("is_hit"))

    if not partial:
        missing_fields = []
        for field in required_fields:
            if field not in cleaned_data or cleaned_data.get(field) == "":
                missing_fields.append(field)

        if missing_fields:
            return None, f"Missing required field(s): {', '.join(missing_fields)}"

    if partial and not cleaned_data:
        return None, "At least one field is required for update."

    for field in ["title", "artist", "album", "genre"]:
        if field in cleaned_data:
            if not cleaned_data[field]:
                return None, f"{field.title()} cannot be empty."

            if len(cleaned_data[field]) > 120:
                return None, f"{field.title()} must be less than 120 characters."

    return cleaned_data, None


with app.app_context():
    db.create_all()


@app.route("/")
def login_page():
    return render_template("login.html")


@app.route("/home")
def home_page():
    return render_template("home.html")


@app.route("/app")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
    except BadRequest:
        return jsonify({"error": "Invalid JSON body."}), 400

    if not data:
        return jsonify({"error": "Username and password are required."}), 400

    username = clean_text(data.get("username"))
    password = clean_text(data.get("password"))

    if username == USERNAME and password == PASSWORD:
        access_token = create_access_token(identity=username)
        return jsonify({
            "message": "Login successful.",
            "access_token": access_token,
            "username": username
        }), 200

    return jsonify({"error": "Invalid username or password."}), 401


@app.route("/tracks", methods=["POST"])
@jwt_required()
def create_track():
    try:
        data = request.get_json()
    except BadRequest:
        return jsonify({"error": "Invalid JSON body."}), 400

    cleaned_data, error = validate_track_data(data, partial=False)

    if error:
        return jsonify({"error": error}), 400

    track = Track(
        title=cleaned_data["title"],
        artist=cleaned_data["artist"],
        album=cleaned_data["album"],
        genre=cleaned_data["genre"],
        year=cleaned_data["year"],
        is_hit=cleaned_data.get("is_hit", False),
    )

    db.session.add(track)
    db.session.commit()

    return jsonify({
        "message": "Track created successfully.",
        "track": track.to_dict()
    }), 201


@app.route("/tracks", methods=["GET"])
@jwt_required()
def get_tracks():
    search = clean_text(request.args.get("search", "")).lower()

    tracks = Track.query.order_by(Track.id.desc()).all()
    track_list = [track.to_dict() for track in tracks]

    if search:
        track_list = [
            track for track in track_list
            if search in track["title"].lower()
            or search in track["artist"].lower()
            or search in track["album"].lower()
            or search in track["genre"].lower()
            or search in str(track["year"])
        ]

    return jsonify(track_list), 200


@app.route("/tracks/summary", methods=["GET"])
@jwt_required()
def get_tracks_summary():
    tracks = Track.query.all()

    total_tracks = len(tracks)
    hit_tracks = len([track for track in tracks if track.is_hit])
    total_genres = len(set(track.genre for track in tracks))
    latest_year = max([track.year for track in tracks], default="N/A")

    genre_summary = {}
    year_summary = {}

    for track in tracks:
        genre_summary[track.genre] = genre_summary.get(track.genre, 0) + 1
        year_summary[track.year] = year_summary.get(track.year, 0) + 1

    recent_tracks = sorted(
        [track.to_dict() for track in tracks],
        key=lambda x: x["id"],
        reverse=True
    )[:5]

    top_hit_tracks = [
        track.to_dict() for track in tracks if track.is_hit
    ][:5]

    return jsonify({
        "total_tracks": total_tracks,
        "hit_tracks": hit_tracks,
        "total_genres": total_genres,
        "latest_year": latest_year,
        "genre_summary": genre_summary,
        "year_summary": year_summary,
        "recent_tracks": recent_tracks,
        "top_hit_tracks": top_hit_tracks,
    }), 200


@app.route("/tracks/<int:track_id>", methods=["PUT"])
@jwt_required()
def update_track(track_id):
    track = db.session.get(Track, track_id)

    if track is None:
        return jsonify({"error": "Track not found."}), 404

    try:
        data = request.get_json()
    except BadRequest:
        return jsonify({"error": "Invalid JSON body."}), 400

    cleaned_data, error = validate_track_data(data, partial=True)

    if error:
        return jsonify({"error": error}), 400

    if "title" in cleaned_data:
        track.title = cleaned_data["title"]
    if "artist" in cleaned_data:
        track.artist = cleaned_data["artist"]
    if "album" in cleaned_data:
        track.album = cleaned_data["album"]
    if "genre" in cleaned_data:
        track.genre = cleaned_data["genre"]
    if "year" in cleaned_data:
        track.year = cleaned_data["year"]
    if "is_hit" in cleaned_data:
        track.is_hit = cleaned_data["is_hit"]

    db.session.commit()

    return jsonify({
        "message": "Track updated successfully.",
        "track": track.to_dict()
    }), 200


@app.route("/tracks/<int:track_id>", methods=["DELETE"])
@jwt_required()
def delete_track(track_id):
    track = db.session.get(Track, track_id)

    if track is None:
        return jsonify({"error": "Track not found."}), 404

    db.session.delete(track)
    db.session.commit()

    return jsonify({"message": "Track deleted successfully."}), 200


if __name__ == "__main__":
    app.run(debug=True)
import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from api.lyrics import lyrics_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Server Error: {str(e)}")
    return jsonify({"code": 500, "message": "Internal Server Error"}), 500


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/lyrics", methods=["GET"])
def get_lyrics_route():
    title = request.args.get("title", "").strip()
    artist = request.args.get("artist", "").strip()
    try:
        duration = int(request.args.get("duration", -1))
    except (ValueError, TypeError):
        duration = -1
    if not title:
        return jsonify({"code": 400, "message": "Missing title"}), 400
    try:
        result = lyrics_engine.get_lyrics_by_query(title, artist, duration)
        if result:
            return jsonify({"code": 200, "lyrics": result})
        return jsonify({"code": 404, "message": "Lyrics not found"}), 404
    except Exception as e:
        logger.error(f"API Error: {e}")
        return jsonify({"code": 500, "message": "Processing error"}), 500


app = app

import os
import uuid
import logging
import threading
import tempfile
from flask import Blueprint, render_template, request, jsonify
from utils import sanitize_singer_name, is_valid_email, check_ffmpeg
from services.youtube_service import download_audio_files
from services.audio_service import process_and_merge_clips, create_zip_archive
from services.email_service import send_mashup_email

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)

# Thread-safe job tracker
# job_id -> {"status": "queued|processing|completed|failed", "message": "status text", "progress": 0-100}
jobs = {}
jobs_lock = threading.Lock()

def update_job(job_id: str, status: str, message: str, progress: int):
    with jobs_lock:
        jobs[job_id] = {
            "status": status,
            "message": message,
            "progress": progress
        }
    logger.info(f"Job {job_id} updated: {status} - {message} ({progress}%)")

def run_mashup_background_job(job_id: str, singer: str, num_videos: int, duration: int, email: str):
    """
    Executes the mashup pipeline in a background thread using a secure,
    request-scoped temp directory that cleans up automatically when finished.
    """
    try:
        # Check for FFmpeg availability
        ffmpeg_check = check_ffmpeg()
        if not ffmpeg_check["status"]:
            raise Exception("FFmpeg/FFprobe is not installed or configured on the server environment.")

        # Create a unique temporary directory for this specific request
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Starting background job {job_id} in {temp_dir}")
            
            # Step 1: Download Audio files
            update_job(job_id, "processing", "Downloading audio tracks from YouTube...", 10)
            downloads_dir = os.path.join(temp_dir, "downloads")
            
            def yt_dlp_progress(msg):
                # Interpolate downlods progress between 10% and 60%
                update_job(job_id, "processing", msg, 20)
                
            audio_files = download_audio_files(
                singer, num_videos, downloads_dir, 
                progress_callback=yt_dlp_progress
            )
            
            # Step 2: Trim and Merge Audio Clips
            update_job(job_id, "processing", "Slicing and merging audio clips...", 60)
            merged_mp3 = os.path.join(temp_dir, "mashup.mp3")
            
            def audio_progress(msg):
                update_job(job_id, "processing", msg, 75)
                
            process_and_merge_clips(
                audio_files, duration, merged_mp3,
                progress_callback=audio_progress
            )
            
            # Step 3: Archive into ZIP
            update_job(job_id, "processing", "Creating ZIP archive...", 85)
            zip_path = os.path.join(temp_dir, "mashup.zip")
            create_zip_archive(merged_mp3, zip_path)
            
            # Step 4: Email package
            update_job(job_id, "processing", "Mailing zip archive...", 90)
            send_mashup_email(
                recipient_email=email,
                artist_name=singer,
                num_songs=num_videos,
                duration=duration,
                attachment_path=zip_path,
                progress_callback=lambda msg: update_job(job_id, "processing", msg, 95)
            )
            
            update_job(job_id, "completed", f"Success! Mashup emailed to {email}.", 100)
            
    except Exception as e:
        logger.exception(f"Background job {job_id} failed")
        update_job(job_id, "failed", f"Failed: {str(e)}", 100)

@main_bp.route("/", methods=["GET"])
def index():
    """
    Renders the main page.
    """
    return render_template("index.html")

@main_bp.route("/submit", methods=["POST"])
def submit_mashup():
    """
    Accepts form submissions, runs validations, registers job ID,
    and starts a daemon background thread to process the request.
    """
    singer_raw = request.form.get("singer_name", "").strip()
    num_videos_raw = request.form.get("num_videos", "").strip()
    duration_raw = request.form.get("duration", "").strip()
    email = request.form.get("email", "").strip()

    # Validations
    errors = []
    
    # 1. Sanitize singer name
    singer = sanitize_singer_name(singer_raw)
    if not singer:
        errors.append("Invalid singer name. Please use only alphanumeric characters and spaces.")

    # 2. Validate number of videos (> 10)
    try:
        num_videos = int(num_videos_raw)
        if num_videos <= 10:
            errors.append("Number of videos must be greater than 10.")
    except ValueError:
        errors.append("Number of videos must be a valid integer.")

    # 3. Validate clip duration (> 20)
    try:
        duration = int(duration_raw)
        if duration <= 20:
            errors.append("Duration must be greater than 20 seconds.")
    except ValueError:
        errors.append("Duration must be a valid integer.")

    # 4. Validate email
    if not is_valid_email(email):
        errors.append("Please enter a valid email address.")

    if errors:
        return jsonify({"status": "error", "errors": errors}), 400

    # Start background execution
    job_id = str(uuid.uuid4())
    update_job(job_id, "queued", "Queueing request...", 0)
    
    # Spawn background daemon thread
    thread = threading.Thread(
        target=run_mashup_background_job,
        args=(job_id, singer, num_videos, duration, email),
        daemon=True
    )
    thread.start()

    return jsonify({
        "status": "success",
        "job_id": job_id,
        "message": "Job initiated successfully."
    })

@main_bp.route("/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """
    Returns the current status of a job.
    """
    with jobs_lock:
        job = jobs.get(job_id)
        
    if not job:
        return jsonify({"status": "error", "message": "Job ID not found."}), 404
        
    return jsonify(job)

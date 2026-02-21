import re
import subprocess
import shutil
import logging

logger = logging.getLogger(__name__)

def sanitize_singer_name(name: str) -> str:
    """
    Sanitizes the singer name to be safe for file paths and search queries.
    Allows only alphanumeric characters, spaces, hyphens, and underscores.
    """
    if not name:
        return ""
    # Strip any directory traversal sequences
    cleaned = re.sub(r'[\.\/\\\?%\*:\n\r\|"<>_]', '', name)
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def is_valid_email(email: str) -> bool:
    """
    Validates email format using regex.
    """
    if not email:
        return False
    # Standard email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def check_ffmpeg() -> dict:
    """
    Checks if FFmpeg and FFprobe are installed and available in the system PATH.
    Returns a dict with 'status' (bool) and 'message' (str).
    """
    ffmpeg_found = shutil.which("ffmpeg") is not None
    ffprobe_found = shutil.which("ffprobe") is not None
    
    if ffmpeg_found and ffprobe_found:
        return {
            "status": True,
            "message": "FFmpeg and FFprobe are properly installed and available in PATH."
        }
    
    missing = []
    if not ffmpeg_found:
        missing.append("FFmpeg")
    if not ffprobe_found:
        missing.append("FFprobe")
        
    msg = (
        f"Missing components: {', '.join(missing)}. "
        "Please ensure FFmpeg is installed and added to your system environment variables (PATH).\n"
        "Installation guides:\n"
        "- Windows: Download from gyan.dev or use 'winget install Gyan.FFmpeg'.\n"
        "- macOS: Install via Homebrew: 'brew install ffmpeg'.\n"
        "- Linux: Install via package manager: 'sudo apt install ffmpeg' or 'sudo yum install ffmpeg'."
    )
    logger.error(msg)
    return {
        "status": False,
        "message": msg
    }

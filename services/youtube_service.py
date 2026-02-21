import os
import logging
import yt_dlp

logger = logging.getLogger(__name__)

def download_audio_files(singer_name: str, num_videos: int, download_dir: str, progress_callback=None) -> list:
    """
    Searches YouTube for the singer name, downloads the audio-only streams for N videos,
    and extracts them as MP3s directly to the download_dir.
    
    :param singer_name: Name of the artist/singer.
    :param num_videos: Number of videos to search and download.
    :param download_dir: Directory where the output MP3 files will be stored.
    :param progress_callback: Optional callable for reporting download status/stage updates.
    :return: List of absolute file paths to the downloaded MP3 files.
    """
    if progress_callback:
        progress_callback("Searching YouTube and preparing downloads...")
        
    os.makedirs(download_dir, exist_ok=True)
    
    # Check for cookies (from env secure variable or local cookies.txt file)
    env_cookies = os.environ.get("YOUTUBE_COOKIES")
    cookie_path = None

    if env_cookies:
        logger.info("Using cookies from YOUTUBE_COOKIES environment variable.")
        cookie_path = os.path.join(download_dir, "temp_cookies.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(env_cookies)
    elif os.path.exists("cookies.txt"):
        logger.info("Using local cookies.txt file.")
        cookie_path = "cookies.txt"
    else:
        logger.info("No cookies provided. Proceeding anonymously.")

    # Custom progress hook for yt-dlp to trace downloads
    downloaded_count = 0
    def ydl_hook(d):
        nonlocal downloaded_count
        if d.get('status') == 'finished':
            downloaded_count += 1
            msg = f"Downloaded and converted {downloaded_count}/{num_videos} videos..."
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

    # Filter out videos longer than 10 minutes (600 seconds) to avoid massive mix files
    def filter_duration(info_dict, *, incomplete):
        duration = info_dict.get('duration')
        if duration and duration > 600:
            return 'Video is too long (likely a compilation mix)'
        return None

    ydl_opts = {
        # Audio-only extraction settings
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "outtmpl": os.path.join(download_dir, "%(autonumber)s_%(title)s.%(ext)s"),
        "ignoreerrors": True,  # Skip errors so we can continue with the rest of the playlist/results
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 15,
        "progress_hooks": [ydl_hook],
        "restrictfilenames": True,  # Restrict to ASCII characters only
        "match_filter": filter_duration,  # Skip mix videos
        "extractor_args": {
            "youtube": {
                "client": ["ios", "android", "web_music", "web"]
            }
        }
    }

    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    # Construct the search query
    search_query = f"ytsearch{num_videos}:{singer_name} song"
    logger.info(f"Searching and downloading: {search_query}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
    except Exception as e:
        logger.error(f"yt-dlp download failed: {str(e)}")
        if progress_callback:
            progress_callback(f"Download error: {str(e)}")
            
    # Find all downloaded MP3s in the download directory
    downloaded_files = [
        os.path.join(download_dir, f)
        for f in sorted(os.listdir(download_dir))
        if f.lower().endswith(".mp3")
    ]

    logger.info(f"Successfully downloaded and extracted {len(downloaded_files)} MP3 file(s).")
    
    if not downloaded_files:
        raise Exception(
            "No audio tracks were successfully downloaded. "
            "This can happen due to YouTube bot protection, invalid search query, or network errors."
        )

    return downloaded_files

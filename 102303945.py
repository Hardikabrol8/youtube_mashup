import sys
import os
import logging
import tempfile
from utils import sanitize_singer_name, check_ffmpeg
from services.youtube_service import download_audio_files
from services.audio_service import process_and_merge_clips

# Set up logging for CLI execution
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cli_mashup")

def validate_cli_args(args):
    if len(args) != 4:
        logger.error("Incorrect number of arguments.")
        print("\nUsage : python 102303945.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        print('Example: python 102303945.py "Sharry Maan" 20 25 output.mp3\n')
        sys.exit(1)

    singer_name_raw, num_videos_str, audio_duration_str, output_file = args

    # Check FFmpeg installation
    ffmpeg_check = check_ffmpeg()
    if not ffmpeg_check["status"]:
        logger.error(ffmpeg_check["message"])
        sys.exit(1)

    # Sanitize Singer Name
    singer_name = sanitize_singer_name(singer_name_raw)
    if not singer_name:
        logger.error("Singer name must contain alphanumeric characters.")
        sys.exit(1)

    # Validate NumberOfVideos > 10
    try:
        num_videos = int(num_videos_str)
        if num_videos <= 10:
            raise ValueError
    except ValueError:
        logger.error(f"<NumberOfVideos> must be an integer greater than 10. Got: '{num_videos_str}'")
        sys.exit(1)

    # Validate AudioDuration > 20
    try:
        audio_duration = int(audio_duration_str)
        if audio_duration <= 20:
            raise ValueError
    except ValueError:
        logger.error(f"<AudioDuration> must be an integer greater than 20. Got: '{audio_duration_str}'")
        sys.exit(1)

    # Validate output filename ends with .mp3
    if not output_file.lower().endswith(".mp3"):
        logger.error(f"<OutputFileName> must end with '.mp3'. Got: '{output_file}'")
        sys.exit(1)

    return singer_name, num_videos, audio_duration, output_file

def main():
    singer, n_videos, duration, out_file = validate_cli_args(sys.argv[1:])

    logger.info("=" * 50)
    logger.info("  YouTube Mashup Creator (CLI Mode)")
    logger.info("=" * 50)
    logger.info(f"  Singer        : {singer}")
    logger.info(f"  Videos        : {n_videos}")
    logger.info(f"  Clip duration : {duration}s")
    logger.info(f"  Output file   : {out_file}")
    logger.info("=" * 50)

    try:
        # Create a temp dir for CLI execution so that it clears all intermediate downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = os.path.join(temp_dir, "downloads")
            
            logger.info("Downloading audio streams from YouTube...")
            audio_files = download_audio_files(
                singer, n_videos, downloads_dir, 
                progress_callback=lambda msg: logger.info(f"  [Downloader] {msg}")
            )
            
            logger.info("Slicing and merging audio clips...")
            process_and_merge_clips(
                audio_files, duration, out_file,
                progress_callback=lambda msg: logger.info(f"  [Processor] {msg}")
            )
            
        logger.info(f"Success! Mashup saved to {out_file}")

    except KeyboardInterrupt:
        logger.error("\nExecution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nUnexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

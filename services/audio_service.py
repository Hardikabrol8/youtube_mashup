import os
import logging
import zipfile
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def process_and_merge_clips(audio_files: list, duration_sec: int, output_file_path: str, progress_callback=None) -> str:
    """
    Trims the first Y seconds of each audio file and merges them into a single MP3 output file.
    
    :param audio_files: List of paths to individual MP3 files.
    :param duration_sec: Number of seconds to keep from the start of each file.
    :param output_file_path: Path where the merged output MP3 file will be saved.
    :param progress_callback: Optional callable for reporting execution stage updates.
    :return: Absolute path to the created output file.
    """
    if progress_callback:
        progress_callback(f"Trimming clips to {duration_sec}s and merging...")

    combined = AudioSegment.empty()
    duration_ms = duration_sec * 1000
    successful_clips = 0

    for i, apath in enumerate(audio_files, 1):
        filename = os.path.basename(apath)
        try:
            logger.info(f"Processing clip {i}/{len(audio_files)}: {filename}")
            if progress_callback:
                progress_callback(f"Processing clip {i}/{len(audio_files)}: {filename[:25]}...")
                
            seg = AudioSegment.from_mp3(apath)
            # Clip the segment to the first duration_ms milliseconds
            chunk = seg[:duration_ms] if len(seg) >= duration_ms else seg
            combined += chunk
            successful_clips += 1
        except Exception as e:
            logger.warning(f"Failed to process clip '{filename}': {str(e)}")
            continue

    if successful_clips == 0 or len(combined) == 0:
        raise Exception("Failed to process any audio clips. Resulting mashup would be empty.")

    logger.info(f"Exporting merged audio to: {output_file_path}")
    if progress_callback:
        progress_callback("Exporting merged mashup MP3...")
        
    combined.export(output_file_path, format="mp3")
    logger.info(f"Mashup exported successfully. Total duration: {len(combined)/1000:.2f}s")
    
    return output_file_path

def create_zip_archive(mp3_file_path: str, zip_file_path: str, progress_callback=None) -> str:
    """
    Zips the merged MP3 file into a zip archive.
    
    :param mp3_file_path: Path to the source MP3 file.
    :param zip_file_path: Path where the output ZIP file will be saved.
    :param progress_callback: Optional callable for reporting updates.
    :return: Absolute path to the created ZIP file.
    """
    if progress_callback:
        progress_callback("Compressing mashup into a ZIP file...")
        
    logger.info(f"Creating zip archive at: {zip_file_path}")
    
    if not os.path.exists(mp3_file_path):
        raise FileNotFoundError(f"Source MP3 file {mp3_file_path} not found.")

    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Save as "mashup.mp3" inside the zip archive
        zf.write(mp3_file_path, arcname="mashup.mp3")
        
    logger.info("ZIP archive created successfully.")
    return zip_file_path

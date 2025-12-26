'''
Perceptual Hash Calculator for Images and Videos

Uses imagehash library for perceptual hashing with parallel processing support.
'''

import os
import subprocess
import tempfile
from typing import Optional, Tuple
from PIL import Image
import imagehash
from logger import info_logger, error_logger


def calculate_image_phash(file_path: str) -> Optional[Tuple[str, int, int]]:
    '''
    @brief Calculate perceptual hash for an image file
    @param file_path Path to image file
    @return Tuple of (hash_string, width, height) or None on error
    '''
    try:
        with Image.open(file_path) as img:
            # Get dimensions
            width, height = img.size

            # Calculate perceptual hash (16x16 = 256-bit hash for better accuracy)
            phash = imagehash.phash(img, hash_size=16)

            return (str(phash), width, height)

    except Exception as e:
        error_logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return None


def extract_video_frame(video_path: str, output_path: str, timestamp: str = "00:00:01") -> bool:
    '''
    @brief Extract a single frame from video using ffmpeg
    @param video_path Path to video file
    @param output_path Path to save extracted frame
    @param timestamp Timestamp to extract frame from (default: 1 second)
    @return True if successful, False otherwise
    '''
    try:
        cmd = [
            'ffmpeg',
            '-ss', timestamp,
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30
        )

        return result.returncode == 0

    except Exception as e:
        error_logger.error(f"Failed to extract frame from {video_path}: {e}")
        return False


def get_video_info(video_path: str) -> Optional[Tuple[int, int, float]]:
    '''
    @brief Get video dimensions and duration using ffprobe
    @param video_path Path to video file
    @return Tuple of (width, height, duration) or None on error
    '''
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration',
            '-of', 'csv=p=0',
            video_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            text=True
        )

        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            if len(parts) >= 3:
                width = int(parts[0])
                height = int(parts[1])
                duration = float(parts[2])
                return (width, height, duration)

    except Exception as e:
        error_logger.error(f"Failed to get video info for {video_path}: {e}")

    return None


def calculate_video_phash(file_path: str) -> Optional[Tuple[str, int, int, float]]:
    '''
    @brief Calculate perceptual hash for a video file using keyframe
    @param file_path Path to video file
    @return Tuple of (hash_string, width, height, duration) or None on error
    '''
    temp_frame = None

    try:
        # Get video info first
        video_info = get_video_info(file_path)
        if video_info is None:
            return None

        width, height, duration = video_info

        # Create temporary file for extracted frame
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
            temp_frame = temp.name

        # Extract frame at 10% into the video (skip intros/black screens)
        timestamp_seconds = max(1, int(duration * 0.1))
        timestamp = f"00:00:{timestamp_seconds:02d}"

        if not extract_video_frame(file_path, temp_frame, timestamp):
            return None

        # Calculate hash of extracted frame
        with Image.open(temp_frame) as img:
            phash = imagehash.phash(img, hash_size=16)

        return (str(phash), width, height, duration)

    except Exception as e:
        error_logger.error(f"Failed to calculate video hash for {file_path}: {e}")
        return None

    finally:
        # Clean up temporary frame
        if temp_frame and os.path.exists(temp_frame):
            try:
                os.remove(temp_frame)
            except:
                pass


def process_media_file(args: Tuple[str, str]) -> Optional[dict]:
    '''
    @brief Process a single media file (image or video) for parallel execution
    @param args Tuple of (file_path, media_type)
    @return Dictionary with file info and hash, or None on error
    '''
    file_path, media_type = args

    try:
        # Get file stats
        stat = os.stat(file_path)
        file_size = stat.st_size
        modification_time = stat.st_mtime

        # Calculate hash based on media type
        if media_type == 'image':
            result = calculate_image_phash(file_path)
            if result is None:
                return None

            phash, width, height = result

            return {
                'file_path': file_path,
                'perceptual_hash': phash,
                'file_size': file_size,
                'modification_time': modification_time,
                'media_type': media_type,
                'width': width,
                'height': height,
                'duration': None
            }

        elif media_type == 'video':
            result = calculate_video_phash(file_path)
            if result is None:
                return None

            phash, width, height, duration = result

            return {
                'file_path': file_path,
                'perceptual_hash': phash,
                'file_size': file_size,
                'modification_time': modification_time,
                'media_type': media_type,
                'width': width,
                'height': height,
                'duration': duration
            }

    except Exception as e:
        error_logger.error(f"Failed to process {file_path}: {e}")
        return None

    return None

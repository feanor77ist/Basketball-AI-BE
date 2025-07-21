import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def extract_video_metadata(video_path):
    """Extract metadata from video file"""
    try:
        # Use OpenCV for basic properties
        cap = cv2.VideoCapture(video_path)
        metadata = {}
        
        if cap.isOpened():
            metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
            metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            metadata['duration'] = frame_count / metadata['fps'] if metadata['fps'] > 0 else 0
            cap.release()
        
        # Use MoviePy for duration verification
        try:
            clip = VideoFileClip(video_path)
            metadata['duration'] = clip.duration
            clip.close()
        except Exception:
            pass  # Use OpenCV duration if MoviePy fails
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting video metadata: {str(e)}")
        return {}


def validate_video_file(file_path):
    """Validate video file format and properties"""
    try:
        # Check file extension
        ext = os.path.splitext(file_path)[1][1:].lower()
        if ext not in getattr(settings, 'SUPPORTED_VIDEO_FORMATS', ['mp4', 'avi', 'mov']):
            return False, f"Unsupported format: {ext}"
        
        # Check if file can be opened
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return False, "Cannot open video file"
        
        # Check duration
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        
        max_duration = getattr(settings, 'MAX_VIDEO_DURATION', 3600)
        if duration > max_duration:
            return False, f"Video too long: {duration}s (max: {max_duration}s)"
        
        cap.release()
        return True, "Valid video file"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def create_video_thumbnail(video_path, output_path, timestamp=5.0):
    """Create thumbnail from video at specified timestamp"""
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if ret:
            # Resize frame for thumbnail
            height, width = frame.shape[:2]
            thumbnail_width = 320
            thumbnail_height = int(height * thumbnail_width / width)
            
            thumbnail = cv2.resize(frame, (thumbnail_width, thumbnail_height))
            cv2.imwrite(output_path, thumbnail)
            
        cap.release()
        return True
        
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        return False


def segment_video(video_path, segment_length=3):
    """Segment video into clips of specified length"""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        
        segments = []
        for start_time in range(0, int(duration), segment_length):
            end_time = min(start_time + segment_length, duration)
            segments.append((start_time, end_time))
        
        clip.close()
        return segments
        
    except Exception as e:
        logger.error(f"Error segmenting video: {str(e)}")
        return []


def calculate_video_quality_score(video_path):
    """Calculate quality score for video based on resolution, fps, etc."""
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return 0
        
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate quality score (0-100)
        resolution_score = min(100, (width * height) / (1920 * 1080) * 50)
        fps_score = min(50, fps / 30 * 50)
        
        quality_score = resolution_score + fps_score
        
        cap.release()
        return min(100, quality_score)
        
    except Exception as e:
        logger.error(f"Error calculating quality score: {str(e)}")
        return 0


def detect_scene_changes(video_path, threshold=0.3):
    """Detect scene changes in video for better action segmentation"""
    try:
        cap = cv2.VideoCapture(video_path)
        scene_changes = []
        
        ret, prev_frame = cap.read()
        if not ret:
            return scene_changes
        
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate histogram difference
            hist_prev = cv2.calcHist([prev_gray], [0], None, [256], [0, 256])
            hist_curr = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # Normalize histograms
            cv2.normalize(hist_prev, hist_prev)
            cv2.normalize(hist_curr, hist_curr)
            
            # Calculate correlation
            correlation = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CORREL)
            
            if correlation < threshold:
                fps = cap.get(cv2.CAP_PROP_FPS)
                timestamp = frame_count / fps
                scene_changes.append(timestamp)
            
            prev_gray = gray.copy()
            frame_count += 1
        
        cap.release()
        return scene_changes
        
    except Exception as e:
        logger.error(f"Error detecting scene changes: {str(e)}")
        return []


def optimize_video_for_processing(input_path, output_path, target_fps=15, max_width=1280):
    """Optimize video for faster processing"""
    try:
        clip = VideoFileClip(input_path)
        
        # Resize if necessary
        if clip.w > max_width:
            clip = clip.resize(width=max_width)
        
        # Reduce FPS for processing
        if clip.fps > target_fps:
            clip = clip.set_fps(target_fps)
        
        # Write optimized video
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        clip.close()
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing video: {str(e)}")
        return False


class VideoProcessor:
    """Class for advanced video processing operations"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.metadata = extract_video_metadata(video_path)
    
    def extract_frames(self, interval=1.0):
        """Extract frames at specified intervals"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            interval_frames = int(fps * interval)
            
            frames = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % interval_frames == 0:
                    frames.append(frame)
                
                frame_count += 1
            
            cap.release()
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            return []
    
    def detect_motion_areas(self, threshold=25):
        """Detect areas with significant motion"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            
            ret, prev_frame = cap.read()
            if not ret:
                return []
            
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            motion_areas = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calculate frame difference
                diff = cv2.absdiff(prev_gray, gray)
                _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Filter significant motion areas
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 1000:  # Minimum area threshold
                        x, y, w, h = cv2.boundingRect(contour)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        timestamp = frame_count / fps
                        
                        motion_areas.append({
                            'timestamp': timestamp,
                            'bbox': (x, y, w, h),
                            'area': area
                        })
                
                prev_gray = gray.copy()
                frame_count += 1
            
            cap.release()
            return motion_areas
            
        except Exception as e:
            logger.error(f"Error detecting motion areas: {str(e)}")
            return [] 
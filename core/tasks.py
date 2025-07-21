import os
import cv2
import numpy as np
import pandas as pd
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from moviepy.editor import VideoFileClip, concatenate_videoclips
import logging

# ML imports
try:
    from mmaction.apis import init_recognizer, inference_recognizer
    from ultralytics import YOLO
    import torch
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")

from videos.models import Video
from players.models import Player
from actions.models import Action
from highlights.models import Highlight
from stats.models import Stats

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_video_task(self, video_id):
    """
    Main video processing pipeline task
    Orchestrates the complete video analysis workflow
    """
    try:
        video = Video.objects.get(id=video_id)
        video.status = 'processing'
        video.processing_started_at = timezone.now()
        video.save()
        
        logger.info(f"Starting video processing for video {video_id}")
        
        # Step 1: Player detection
        detect_players_task.delay(str(video.id))
        
        # Subsequent steps will be triggered by each task completion
        return {"status": "started", "video_id": str(video.id)}
        
    except Video.DoesNotExist:
        logger.error(f"Video {video_id} not found")
        return {"status": "error", "message": "Video not found"}
    
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        video = Video.objects.get(id=video_id)
        video.status = 'error'
        video.error_message = str(e)
        video.save()
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def detect_players_task(self, video_id):
    """
    Detect players in video using YOLOv8 + DeepSORT
    """
    try:
        video = Video.objects.get(id=video_id)
        video_path = video.file.path
        
        logger.info(f"Starting player detection for video {video_id}")
        
        # Initialize YOLO model
        model_path = getattr(settings, 'YOLO_MODEL_PATH', 'yolov8n.pt')
        model = YOLO(model_path)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Player tracking data
        player_tracks = {}
        frame_idx = 0
        
        # Process video frames
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run YOLO detection every 30 frames (roughly 1 second)
            if frame_idx % 30 == 0:
                results = model(frame)
                
                # Process detections
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            # Filter for person class (class 0 in COCO)
                            if int(box.cls) == 0 and float(box.conf) > 0.5:
                                # Extract bounding box
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                conf = float(box.conf)
                                
                                # Simple tracking by area overlap
                                track_id = len(player_tracks)
                                player_tracks[track_id] = {
                                    'bbox_history': [(x1, y1, x2, y2)],
                                    'confidence_history': [conf],
                                    'frame_indices': [frame_idx]
                                }
            
            frame_idx += 1
        
        cap.release()
        
        # Create Player objects from tracks
        for track_id, track_data in player_tracks.items():
            if len(track_data['frame_indices']) > 10:  # Minimum appearances
                avg_confidence = np.mean(track_data['confidence_history'])
                avg_bbox_area = np.mean([
                    (x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in track_data['bbox_history']
                ])
                
                # Determine team color (simplified - could be enhanced)
                team_color = 'red' if track_id % 2 == 0 else 'blue'
                
                Player.objects.create(
                    video=video,
                    jersey_number=str(track_id + 1),  # Simple numbering
                    team_color=team_color,
                    player_id_model=f"track_{track_id}",
                    detection_confidence=avg_confidence,
                    avg_bbox_area=avg_bbox_area
                )
        
        # Update video status
        video.status = 'players_detected'
        video.save()
        
        logger.info(f"Player detection completed for video {video_id}. Found {len(player_tracks)} players")
        
        # Trigger next step: ball localization and score analysis
        analyze_ball_and_score_task.delay(str(video.id))
        
        return {"status": "completed", "players_detected": len(player_tracks)}
        
    except Exception as e:
        logger.error(f"Error in player detection for video {video_id}: {str(e)}")
        video = Video.objects.get(id=video_id)
        video.status = 'error'
        video.error_message = f"Player detection failed: {str(e)}"
        video.save()
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def analyze_ball_and_score_task(self, video_id):
    """
    Analyze ball localization and score tracking
    """
    try:
        video = Video.objects.get(id=video_id)
        logger.info(f"Starting ball and score analysis for video {video_id}")
        
        # This is a placeholder for ball tracking implementation
        # In a real implementation, you would:
        # 1. Use specialized ball detection models
        # 2. Track ball movement patterns
        # 3. Detect scoring events
        # 4. Associate scores with players
        
        # For now, we'll simulate the process
        video.status = 'ball_analyzed'
        video.save()
        
        # Trigger action detection
        detect_actions_with_mmaction.delay(str(video.id), 'mmaction2_tsn', 0.5)
        
        return {"status": "completed"}
        
    except Exception as e:
        logger.error(f"Error in ball analysis for video {video_id}: {str(e)}")
        video = Video.objects.get(id=video_id)
        video.status = 'error'
        video.error_message = f"Ball analysis failed: {str(e)}"
        video.save()
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def detect_actions_with_mmaction(self, video_id, model_type='mmaction2_tsn', confidence_threshold=0.5):
    """
    Detect actions using mmaction2 models
    """
    try:
        video = Video.objects.get(id=video_id)
        video_path = video.file.path
        
        logger.info(f"Starting action detection for video {video_id} with {model_type}")
        
        # Initialize mmaction2 model
        config_path = getattr(settings, 'MMACTION2_CONFIG_PATH', None)
        checkpoint_path = getattr(settings, 'MMACTION2_CHECKPOINT_PATH', None)
        
        if not config_path or not checkpoint_path:
            raise Exception("MMAction2 model paths not configured")
        
        # Initialize recognizer
        model = init_recognizer(config_path, checkpoint_path, device='cpu')
        
        # Segment video into clips
        segment_length = getattr(settings, 'VIDEO_SEGMENT_LENGTH', 3)  # 3 seconds
        clip = VideoFileClip(video_path)
        duration = clip.duration
        
        actions_created = 0
        
        # Process video in segments
        for start_time in range(0, int(duration), segment_length):
            end_time = min(start_time + segment_length, duration)
            
            # Extract segment
            segment = clip.subclip(start_time, end_time)
            segment_path = f'/tmp/segment_{video_id}_{start_time}.mp4'
            segment.write_videofile(segment_path, verbose=False, logger=None)
            
            try:
                # Run inference
                results = inference_recognizer(model, segment_path)
                
                # Process results
                for result in results:
                    # Extract top prediction
                    if hasattr(result, 'pred_scores'):
                        scores = result.pred_scores.cpu().numpy()
                        labels = result.pred_labels.cpu().numpy()
                        
                        top_idx = np.argmax(scores)
                        confidence = scores[top_idx]
                        label_idx = labels[top_idx]
                        
                        if confidence > confidence_threshold:
                            # Map label to action type (simplified mapping)
                            action_type = _map_mmaction_label_to_action_type(label_idx)
                            
                            if action_type:
                                # Try to associate with a player (simplified)
                                players = Player.objects.filter(video=video)
                                player = players.first() if players.exists() else None
                                
                                Action.objects.create(
                                    video=video,
                                    player=player,
                                    type=action_type,
                                    start_time=start_time,
                                    end_time=end_time,
                                    model_type=model_type,
                                    confidence=confidence,
                                    metadata={'mmaction_label': int(label_idx)}
                                )
                                actions_created += 1
                
                # Clean up segment file
                os.remove(segment_path)
                
            except Exception as e:
                logger.warning(f"Error processing segment {start_time}-{end_time}: {str(e)}")
                continue
        
        clip.close()
        
        # Update video status
        video.status = 'actions_done'
        video.save()
        
        logger.info(f"Action detection completed for video {video_id}. Created {actions_created} actions")
        
        # Trigger stats calculation
        calculate_stats_task.delay(str(video.id))
        
        return {"status": "completed", "actions_created": actions_created}
        
    except Exception as e:
        logger.error(f"Error in action detection for video {video_id}: {str(e)}")
        video = Video.objects.get(id=video_id)
        video.status = 'error'
        video.error_message = f"Action detection failed: {str(e)}"
        video.save()
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def calculate_stats_task(self, video_id):
    """
    Calculate player statistics from detected actions
    """
    try:
        video = Video.objects.get(id=video_id)
        players = Player.objects.filter(video=video)
        
        logger.info(f"Calculating stats for video {video_id}")
        
        # Calculate stats for each player
        for player in players:
            actions = Action.objects.filter(video=video, player=player)
            
            # Initialize stats
            stats = Stats.objects.create(
                video=video,
                player=player
            )
            
            # Count different action types
            for action in actions:
                if action.type == 'shot_2pt':
                    stats.fga_2pt += 1
                    if action.is_successful:
                        stats.fgm_2pt += 1
                elif action.type == 'shot_3pt':
                    stats.fga_3pt += 1
                    if action.is_successful:
                        stats.fgm_3pt += 1
                elif action.type == 'free_throw':
                    stats.fta += 1
                    if action.is_successful:
                        stats.ftm += 1
                elif action.type == 'assist':
                    stats.assists += 1
                elif action.type in ['rebound_offensive', 'rebound_defensive']:
                    if action.type == 'rebound_offensive':
                        stats.offensive_rebounds += 1
                    else:
                        stats.defensive_rebounds += 1
                elif action.type == 'steal':
                    stats.steals += 1
                elif action.type == 'block':
                    stats.blocks += 1
                elif action.type == 'turnover':
                    stats.turnovers += 1
                elif action.type == 'foul':
                    stats.fouls += 1
            
            # Calculate minutes played (simplified)
            stats.minutes_played = video.duration / 60 if video.duration else 0
            
            stats.save()  # This will auto-calculate points and rebounds
        
        # Update video status
        video.status = 'highlights_created'  # Ready for highlight generation
        video.save()
        
        logger.info(f"Stats calculation completed for video {video_id}")
        
        # Trigger highlight generation
        auto_generate_highlights_task.delay(str(video.id))
        
        return {"status": "completed", "stats_created": players.count()}
        
    except Exception as e:
        logger.error(f"Error calculating stats for video {video_id}: {str(e)}")
        video = Video.objects.get(id=video_id)
        video.status = 'error'
        video.error_message = f"Stats calculation failed: {str(e)}"
        video.save()
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def auto_generate_highlights_task(self, video_id):
    """
    Auto-generate highlights for a video
    """
    try:
        video = Video.objects.get(id=video_id)
        
        logger.info(f"Generating highlights for video {video_id}")
        
        # Create different types of highlights
        highlight_types = [
            ('best_plays', 0.8, 60),
            ('shooting_highlights', 0.7, 45),
            ('defensive_highlights', 0.7, 30)
        ]
        
        for highlight_type, min_confidence, max_duration in highlight_types:
            highlight = Highlight.objects.create(
                video=video,
                title=f"Auto-generated {highlight_type.replace('_', ' ').title()}",
                highlight_type=highlight_type,
                min_confidence=min_confidence,
                max_duration=max_duration,
                is_processing=True
            )
            
            # Generate highlight video
            create_highlight_video.delay(str(highlight.id))
        
        # Mark video as complete
        video.status = 'done'
        video.processing_completed_at = timezone.now()
        video.save()
        
        return {"status": "completed", "highlights_created": len(highlight_types)}
        
    except Exception as e:
        logger.error(f"Error generating highlights for video {video_id}: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def create_highlight_video(self, highlight_id):
    """
    Create highlight video from selected actions
    """
    try:
        highlight = Highlight.objects.get(id=highlight_id)
        video = highlight.video
        
        logger.info(f"Creating highlight video for highlight {highlight_id}")
        
        # Get relevant actions based on highlight type and confidence
        actions = Action.objects.filter(
            video=video,
            confidence__gte=highlight.min_confidence
        )
        
        # Filter actions based on highlight type
        if highlight.highlight_type == 'shooting_highlights':
            actions = actions.filter(
                type__in=['shot_2pt', 'shot_3pt', 'dunk', 'layup', 'free_throw']
            )
        elif highlight.highlight_type == 'defensive_highlights':
            actions = actions.filter(
                type__in=['block', 'steal', 'rebound_defensive']
            )
        elif highlight.highlight_type == 'best_plays':
            actions = actions.filter(
                type__in=['shot_3pt', 'dunk', 'assist', 'steal', 'block']
            )
        
        # Limit by player if specified
        if highlight.player:
            actions = actions.filter(player=highlight.player)
        
        # Sort by confidence and limit duration
        actions = actions.order_by('-confidence')
        
        # Create video clips
        video_clip = VideoFileClip(video.file.path)
        clips = []
        total_duration = 0
        
        for action in actions:
            if total_duration >= highlight.max_duration:
                break
            
            # Add buffer around action
            buffer = 1.0  # 1 second buffer
            start = max(0, action.start_time - buffer)
            end = min(video_clip.duration, action.end_time + buffer)
            
            clip_duration = end - start
            if total_duration + clip_duration <= highlight.max_duration:
                clip = video_clip.subclip(start, end)
                clips.append(clip)
                total_duration += clip_duration
                
                # Add action to highlight
                highlight.actions.add(action)
        
        if clips:
            # Concatenate clips
            final_clip = concatenate_videoclips(clips)
            
            # Save highlight video
            highlight_path = f'highlights/{timezone.now().strftime("%Y/%m/%d")}/highlight_{highlight_id}.mp4'
            full_path = os.path.join(settings.MEDIA_ROOT, highlight_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            final_clip.write_videofile(full_path, verbose=False, logger=None)
            
            # Update highlight object
            highlight.file = highlight_path
            highlight.duration = total_duration
            highlight.is_processing = False
            highlight.save()
            
            # Clean up
            final_clip.close()
            for clip in clips:
                clip.close()
        
        video_clip.close()
        
        logger.info(f"Highlight video created for highlight {highlight_id}")
        
        return {"status": "completed", "duration": total_duration}
        
    except Exception as e:
        logger.error(f"Error creating highlight video for highlight {highlight_id}: {str(e)}")
        highlight = Highlight.objects.get(id=highlight_id)
        highlight.is_processing = False
        highlight.processing_error = str(e)
        highlight.save()
        return {"status": "error", "message": str(e)}


def _map_mmaction_label_to_action_type(label_idx):
    """
    Map mmaction2 label index to our action types
    This is a simplified mapping - in practice, you'd need to train
    a basketball-specific model or fine-tune existing models
    """
    # Simplified mapping based on common action recognition datasets
    mapping = {
        0: 'shot_2pt',
        1: 'pass',
        2: 'dribble',
        3: 'run',
        4: 'jump',
        5: 'shot_3pt',
        # Add more mappings based on your model's output classes
    }
    
    return mapping.get(label_idx, None) 
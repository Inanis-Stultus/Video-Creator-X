import os
import logging
import moviepy.editor as mp
from moviepy.video.fx import all as vfx
from file_manager import FileManager

logger = logging.getLogger(__name__)

def get_media_resolution(filepath):
    """Get the resolution of a media file."""
    try:
        if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
            clip = mp.ImageClip(filepath)
        else:
            clip = mp.VideoFileClip(filepath)
        width, height = clip.size
        clip.close()
        return width, height
    except Exception as e:
        logger.error(f"Failed to get resolution for {filepath}: {str(e)}")
        return None

def get_max_resolution(timeline):
    """Get the maximum resolution from all media in timeline."""
    max_width = 0
    max_height = 0

    for item in timeline:
        resolution = get_media_resolution(item['filepath'])
        if resolution:
            width, height = resolution
            max_width = max(max_width, width)
            max_height = max(max_height, height)

    return max_width or 1920, max_height or 1080

def resize_clip_maintain_aspect(clip, target_width, target_height):
    """Resize clip maintaining aspect ratio with padding if needed."""
    try:
        orig_width, orig_height = clip.size
        orig_aspect = orig_width / orig_height
        target_aspect = target_width / target_height

        # Create a black background clip
        bg_clip = mp.ColorClip(size=(target_width, target_height), color=(0, 0, 0))
        bg_clip = bg_clip.set_duration(clip.duration)

        # Calculate new dimensions maintaining aspect ratio
        if orig_aspect > target_aspect:
            new_width = target_width
            new_height = int(target_width / orig_aspect)
        else:
            new_height = target_height
            new_width = int(target_height * orig_aspect)

        # Resize with updated PIL parameters
        resized_clip = clip.resize(width=new_width, height=new_height)

        # Center the clip
        x_pos = (target_width - new_width) // 2
        y_pos = (target_height - new_height) // 2

        positioned_clip = resized_clip.set_position((x_pos, y_pos))
        return mp.CompositeVideoClip([bg_clip, positioned_clip])
    except Exception as e:
        logger.error(f"Failed to resize clip: {str(e)}")
        return clip

def apply_transition(clip, transition_type='fade', duration=1.0, position='start'):
    """Apply transition effect to a clip at the start or end."""
    try:
        if transition_type == 'none':
            return clip

        clip_width, clip_height = clip.size

        if transition_type == 'fade':
            if position == 'start':
                return clip.fadein(duration)
            else:
                return clip.fadeout(duration)
        elif transition_type == 'slide':
            if position == 'start':
                def slide_pos(t):
                    if t < duration:
                        progress = t / duration
                        return (-clip_width + (clip_width * progress), 'center')
                    return ('center', 'center')
                return clip.set_position(slide_pos)
            else:
                def slide_pos(t):
                    if t > clip.duration - duration:
                        progress = (t - (clip.duration - duration)) / duration
                        return (clip_width * progress, 'center')
                    return ('center', 'center')
                return clip.set_position(slide_pos)
        elif transition_type == 'zoom':
            if position == 'start':
                def zoom_scale(t):
                    if t < duration:
                        # Start from scale 0.2 and zoom in to 1.0
                        progress = t / duration
                        return 0.2 + (0.8 * progress)
                    return 1.0

                # Apply zoom effect
                zoomed = clip.resize(lambda t: zoom_scale(t))
                return zoomed.set_position('center')
            else:
                def zoom_scale(t):
                    if t > clip.duration - duration:
                        # Start from scale 1.0 and zoom out to 0.2
                        progress = (t - (clip.duration - duration)) / duration
                        return 1.0 - (0.8 * progress)
                    return 1.0

                # Apply zoom effect
                zoomed = clip.resize(lambda t: zoom_scale(t))
                return zoomed.set_position('center')

        return clip
    except Exception as e:
        logger.error(f"Failed to apply transition: {str(e)}")
        return clip

def process_video(timeline, output_path, target_resolution=None):
    """Process video clips according to timeline with progress tracking."""
    clips = []
    transition_duration = 1.0
    file_manager = FileManager.get_instance()

    try:
        total_steps = len(timeline) * 2 + 1  # Loading + processing for each clip + final export
        current_step = 0

        # Determine target resolution
        if target_resolution:
            target_width, target_height = target_resolution
        else:
            target_width, target_height = get_max_resolution(timeline)
            logger.info(f"Using max resolution from media: {target_width}x{target_height}")

        # Process each item in timeline
        for item in timeline:
            filepath = item['filepath']
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            duration = float(item.get('duration', 5))
            keep_audio = item.get('keepAudio', True)

            # Update progress for loading
            current_step += 1
            file_manager.update_progress((current_step / total_steps) * 100)

            if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                clip = mp.ImageClip(filepath, duration=duration)
            elif filepath.lower().endswith('.gif'):
                clip = mp.VideoFileClip(filepath).loop(duration=duration)
            else:
                clip = mp.VideoFileClip(filepath)
                if not keep_audio:
                    clip = clip.without_audio()

            # Resize clip to target resolution with proper centering
            clip = resize_clip_maintain_aspect(clip, target_width, target_height)

            # Apply effects before transitions
            if item.get('effects'):
                for effect in item['effects']:
                    try:
                        if effect == 'grayscale':
                            clip = clip.fx(vfx.blackwhite)
                        elif effect == 'mirror':
                            clip = clip.fx(vfx.mirror_x)
                    except Exception as e:
                        logger.error(f"Failed to apply effect {effect}: {str(e)}")

            # Apply transitions
            start_transition = item.get('startTransition', 'fade')
            end_transition = item.get('endTransition', 'fade')

            if start_transition != 'none':
                clip = apply_transition(clip, start_transition, transition_duration, 'start')
            if end_transition != 'none':
                clip = apply_transition(clip, end_transition, transition_duration, 'end')

            clips.append(clip)

            # Update progress for processing
            current_step += 1
            file_manager.update_progress((current_step / total_steps) * 100)

        # Ensure clips don't overlap during transitions
        final_clips = []
        current_start = 0
        for clip in clips:
            clip = clip.set_start(current_start)
            final_clips.append(clip)
            current_start += clip.duration - (transition_duration / 2)

        # Create final composition
        final_clip = mp.CompositeVideoClip(final_clips, size=(target_width, target_height))
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)

        # Cleanup clips
        for clip in clips:
            clip.close()
        final_clip.close()

        # Set progress to 100% when complete
        file_manager.update_progress(100)

        return True
    except Exception as e:
        logger.error(f"Video processing failed: {str(e)}")
        raise
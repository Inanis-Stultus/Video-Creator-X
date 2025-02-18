import os
import io
import logging
import base64
import moviepy.editor as mp
from moviepy.video.fx import all as vfx

logger = logging.getLogger(__name__)

def get_media_resolution(clip):
    """Get the resolution of a media clip."""
    try:
        width, height = clip.size
        return width, height
    except Exception as e:
        logger.error(f"Failed to get resolution: {str(e)}")
        return None

def get_max_resolution(clips):
    """Get the maximum resolution from all media clips."""
    max_width = 0
    max_height = 0

    for clip in clips:
        if clip:
            width, height = clip.size
            max_width = max(max_width, width)
            max_height = max(max_height, height)

    return max_width or 1920, max_height or 1080  # Default to 1080p if no valid media

def resize_clip_maintain_aspect(clip, target_width, target_height):
    """Resize clip maintaining aspect ratio with padding if needed."""
    try:
        orig_width, orig_height = clip.size
        orig_aspect = orig_width / orig_height
        target_aspect = target_width / target_height

        # Create a black background clip for the entire duration
        bg_clip = mp.ColorClip(size=(target_width, target_height), color=(0, 0, 0))
        bg_clip = bg_clip.set_duration(clip.duration)

        if orig_aspect > target_aspect:  # Width is the limiting factor
            new_width = target_width
            new_height = int(target_width / orig_aspect)
            scaled_clip = clip.resize(width=new_width, height=new_height)
            y_position = (target_height - new_height) // 2
            positioned_clip = scaled_clip.set_position(("center", y_position))
        else:  # Height is the limiting factor
            new_height = target_height
            new_width = int(target_height * orig_aspect)
            scaled_clip = clip.resize(width=new_width, height=new_height)
            x_position = (target_width - new_width) // 2
            positioned_clip = scaled_clip.set_position((x_position, "center"))

        return mp.CompositeVideoClip([bg_clip, positioned_clip], size=(target_width, target_height))
    except Exception as e:
        logger.error(f"Failed to resize clip: {str(e)}")
        return clip

def apply_filter(clip, filter_type):
    """Apply video filter to clip."""
    try:
        if filter_type == 'grayscale':
            return clip.fx(vfx.blackwhite)
        elif filter_type == 'blur':
            return clip.fx(vfx.blur, sigma=2)
        elif filter_type == 'mirror':
            return clip.fx(vfx.mirror_x)
        elif filter_type == 'bright':
            return clip.fx(vfx.colorx, factor=1.5)
        elif filter_type == 'dark':
            return clip.fx(vfx.colorx, factor=0.5)
        elif filter_type == 'contrast':
            return clip.fx(vfx.lum_contrast, contrast=50)
        return clip
    except Exception as e:
        logger.error(f"Failed to apply filter {filter_type}: {str(e)}")
        return clip

def apply_transition(clip, transition_type='fade', duration=1.0, position='start'):
    """Apply transition effect to a clip at the start or end."""
    try:
        if transition_type == 'none':
            return clip

        # Store original position and size
        original_pos = clip.pos if hasattr(clip, 'pos') else lambda t: ('center', 'center')
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
                        return (-clip_width + (clip_width * progress), original_pos(t)[1])
                    return original_pos(t)
                return clip.set_position(slide_pos)
            else:
                def slide_pos(t):
                    if t > clip.duration - duration:
                        progress = (t - (clip.duration - duration)) / duration
                        return (clip_width * progress, original_pos(t)[1])
                    return original_pos(t)
                return clip.set_position(slide_pos)
        elif transition_type == 'zoom':
            if position == 'start':
                def zoom_scale(t):
                    if t < duration:
                        return 1.5 + 4 * (1 - t / duration)
                    return 1
                zoomed_clip = clip.resize(zoom_scale)
                return zoomed_clip.set_position(original_pos)
            else:
                def zoom_scale(t):
                    if t > clip.duration - duration:
                        return 1 + 0.9 * ((t - (clip.duration - duration)) / duration)
                    return 1
                zoomed_clip = clip.resize(zoom_scale)
                return zoomed_clip.set_position(original_pos)
        return clip
    except Exception as e:
        logger.error(f"Failed to apply transition: {str(e)}")
        return clip

def process_video(timeline, output_stream, target_resolution=None):
    """Process video clips according to timeline."""
    input_clips = []
    clips = []
    transition_duration = 1.0  # Default transition duration

    try:
        # Load all clips first
        for item in timeline:
            file_data = item.get('file_data')
            if not file_data:
                raise ValueError("No file data provided")

            # Decode base64 data
            binary_data = base64.b64decode(file_data)
            file_buffer = io.BytesIO(binary_data)

            duration = float(item.get('duration', 5))
            keep_audio = item.get('keepAudio', True)

            if item['filename'].lower().endswith(('.png', '.jpg', '.jpeg')):
                clip = mp.ImageClip(file_buffer, duration=duration)
            elif item['filename'].lower().endswith('.gif'):
                clip = mp.VideoFileClip(file_buffer).loop(duration=duration)
            else:
                clip = mp.VideoFileClip(file_buffer)
                if not keep_audio:
                    clip = clip.without_audio()

            input_clips.append(clip)

        # Determine target resolution from loaded clips
        if target_resolution:
            target_width, target_height = target_resolution
        else:
            target_width, target_height = get_max_resolution(input_clips)
            logger.info(f"Using max resolution from media: {target_width}x{target_height}")

        # Process each clip
        for idx, (item, clip) in enumerate(zip(timeline, input_clips)):
            # Resize clip to target resolution with proper centering
            clip = resize_clip_maintain_aspect(clip, target_width, target_height)

            # Apply filters
            if item.get('filter'):
                clip = apply_filter(clip, item['filter'])

            # Apply transitions
            start_transition = item.get('startTransition', 'fade')
            end_transition = item.get('endTransition', 'fade')

            if start_transition != 'none':
                clip = apply_transition(clip, start_transition, transition_duration, 'start')
            if end_transition != 'none':
                clip = apply_transition(clip, end_transition, transition_duration, 'end')

            clips.append(clip)

        # Ensure clips don't overlap during transitions
        final_clips = []
        current_start = 0
        for clip in clips:
            clip = clip.set_start(current_start)
            final_clips.append(clip)
            current_start += clip.duration

        final_clip = mp.CompositeVideoClip(final_clips, size=(target_width, target_height))
        final_clip.write_videofile(output_stream, codec='libx264', audio_codec='aac', fps=24)

        # Cleanup clips to free memory
        for clip in input_clips + clips:
            try:
                clip.close()
            except:
                pass
        final_clip.close()

        return True
    except Exception as e:
        logger.error(f"Video processing failed: {str(e)}")
        # Cleanup on error
        for clip in input_clips + clips:
            try:
                clip.close()
            except:
                pass
        raise

from file_manager import FileManager
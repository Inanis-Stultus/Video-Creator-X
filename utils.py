import os
import io
import logging
import base64
import tempfile
import numpy as np
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
        elif filter_type == 'sepia':
            def make_sepia(image):
                sepia_matrix = np.array([
                    [0.393, 0.769, 0.189],
                    [0.349, 0.686, 0.168],
                    [0.272, 0.534, 0.131]
                ])
                sepia_img = image.dot(sepia_matrix.T)
                np.clip(sepia_img, 0, 255, out=sepia_img)
                return sepia_img
            return clip.image_transform(make_sepia)
        elif filter_type == 'blur':
            return clip.fx(vfx.blur, sigma=2)
        elif filter_type == 'sharpen':
            return clip.fx(vfx.lum_contrast, contrast=50, brightness=0)
        elif filter_type == 'invert':
            return clip.image_transform(lambda frame: 255 - frame)
        elif filter_type == 'bright':
            return clip.fx(vfx.colorx, factor=1.5)
        elif filter_type == 'dark':
            return clip.fx(vfx.colorx, factor=0.5)
        elif filter_type == 'contrast':
            return clip.fx(vfx.lum_contrast, contrast=50)
        elif filter_type == 'vignette':
            def add_vignette(get_frame, t):
                frame = get_frame(t)
                height, width = frame.shape[:2]
                x = np.linspace(-1, 1, width)
                y = np.linspace(-1, 1, height)
                X, Y = np.meshgrid(x, y)
                mask = np.sqrt(X**2 + Y**2)
                mask = np.clip(1 - mask, 0, 1)
                mask = np.dstack((mask, mask, mask))
                return frame * mask
            return clip.transform(add_vignette)
        return clip
    except Exception as e:
        logger.error(f"Failed to apply filter {filter_type}: {str(e)}")
        return clip

def apply_transition(clip, transition_type='fade-in', duration=1.0, position='start'):
    """Apply transition effect to a clip at the start or end."""
    try:
        if transition_type == 'none':
            return clip

        # Store original position and size
        original_pos = clip.pos if hasattr(clip, 'pos') else lambda t: ('center', 'center')
        clip_width, clip_height = clip.size

        # Map UI transition names to internal names
        transition_map = {
            'fade-in': ('fade', 'start'),
            'fade-out': ('fade', 'end'),
            'dissolve-in': ('dissolve', 'start'),
            'dissolve-out': ('dissolve', 'end'),
            'wipe-right': ('wipe', 'start'),
            'wipe-left': ('wipe', 'end'),
            'slide-right': ('slide', 'start'),
            'slide-left': ('slide', 'end'),
            'rotate-in': ('rotate', 'start'),
            'rotate-out': ('rotate', 'end'),
            'zoom-in': ('zoom', 'start'),
            'zoom-out': ('zoom', 'end'),
            'blur-in': ('blur', 'start'),
            'blur-out': ('blur', 'end')
        }

        # Get internal transition type and position
        internal_type, internal_position = transition_map.get(transition_type, (transition_type, position))

        if internal_type == 'fade':
            if internal_position == 'start':
                return clip.fadein(duration)
            else:
                return clip.fadeout(duration)
        elif internal_type == 'dissolve':
            if internal_position == 'start':
                mask = mp.VideoClip(lambda t: 1 - (t/duration if t < duration else 1), duration=clip.duration)
                return clip.set_mask(mask)
            else:
                mask = mp.VideoClip(lambda t: (t-clip.duration+duration)/duration if t > clip.duration-duration else 1, duration=clip.duration)
                return clip.set_mask(mask)
        elif internal_type == 'wipe':
            if internal_position == 'start':
                def wipe_mask(t):
                    if t < duration:
                        return np.tile(np.linspace(0, 1, clip_width) > (1 - t/duration), (clip_height, 1))
                    return 1
                mask = mp.VideoClip(lambda t: wipe_mask(t), duration=clip.duration)
                return clip.set_mask(mask)
            else:
                def wipe_mask(t):
                    if t > clip.duration - duration:
                        progress = (t - (clip.duration - duration))/duration
                        return np.tile(np.linspace(0, 1, clip_width) > progress, (clip_height, 1))
                    return 1
                mask = mp.VideoClip(lambda t: wipe_mask(t), duration=clip.duration)
                return clip.set_mask(mask)
        elif internal_type == 'slide':
            if internal_position == 'start':
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
        elif internal_type == 'rotate':
            if internal_position == 'start':
                def rotate_scale(t):
                    if t < duration:
                        angle = 360 * (1 - t/duration)
                        scale = t/duration
                        return lambda pic: mp.vfx.rotate(pic, angle).resize(scale)
                    return lambda pic: pic
                return clip.transform(rotate_scale)
            else:
                def rotate_scale(t):
                    if t > clip.duration - duration:
                        progress = (t - (clip.duration - duration))/duration
                        angle = 360 * progress
                        scale = 1 - progress
                        return lambda pic: mp.vfx.rotate(pic, angle).resize(scale)
                    return lambda pic: pic
                return clip.transform(rotate_scale)
        elif internal_type == 'zoom':
            if internal_position == 'start':
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
        elif internal_type == 'blur':
            if internal_position == 'start':
                def blur_transform(get_frame, t):
                    frame = get_frame(t)
                    if t < duration:
                        sigma = 20 * (1 - t/duration)
                        return vfx.blur(frame, sigma)
                    return frame
                return clip.transform(blur_transform)
            else:
                def blur_transform(get_frame, t):
                    frame = get_frame(t)
                    if t > clip.duration - duration:
                        sigma = 20 * ((t - (clip.duration - duration))/duration)
                        return vfx.blur(frame, sigma)
                    return frame
                return clip.transform(blur_transform)
        return clip
    except Exception as e:
        logger.error(f"Failed to apply transition: {str(e)}")
        return clip

def process_video(timeline, output_path, target_resolution=None):
    """Process video clips according to timeline."""
    input_clips = []
    clips = []
    temp_files = []  # Track temporary files for cleanup
    transition_duration = 1.0  # Default transition duration

    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Load all clips first
            for item in timeline:
                file_data = item.get('file_data')
                if not file_data:
                    raise ValueError("No file data provided")

                # Decode base64 data and save to temporary file
                binary_data = base64.b64decode(file_data)
                temp_path = os.path.join(temp_dir, item['filename'])
                with open(temp_path, 'wb') as f:
                    f.write(binary_data)
                temp_files.append(temp_path)

                duration = float(item.get('duration', 5))
                keep_audio = item.get('keepAudio', True)

                if item['filename'].lower().endswith(('.png', '.jpg', '.jpeg')):
                    clip = mp.ImageClip(temp_path, duration=duration)
                elif item['filename'].lower().endswith('.gif'):
                    clip = mp.VideoFileClip(temp_path).loop(duration=duration)
                else:
                    clip = mp.VideoFileClip(temp_path)
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
                start_transition = item.get('startTransition', 'fade-in')
                end_transition = item.get('endTransition', 'fade-out')

                if start_transition != 'none':
                    clip = apply_transition(clip, start_transition, transition_duration, 'start')
                if end_transition != 'none':
                    clip = apply_transition(clip, end_transition, transition_duration, 'end')

                clips.append(clip)

            # Ensure clips don't overlap during transitions by calculating proper start times
            final_clips = []
            current_start = 0
            for idx, clip in enumerate(clips):
                # Set the start time for the current clip
                clip = clip.set_start(current_start)
                final_clips.append(clip)

                # Calculate the next start time:
                # - For transitions, we need to ensure the current clip's fade out completes
                #   before the next clip's fade in begins
                # Move the start time by the full duration of the current clip
                current_start += clip.duration

            final_clip = mp.CompositeVideoClip(final_clips, size=(target_width, target_height))
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)

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
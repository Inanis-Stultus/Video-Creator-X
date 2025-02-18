import os
import io
import logging
import base64
import tempfile
import numpy as np
import moviepy.editor as mp
from moviepy.video.fx import all as vfx
from PIL import Image
import cv2

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

        # Create a black background clip
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

        return mp.CompositeVideoClip([bg_clip, positioned_clip])
    except Exception as e:
        logger.error(f"Failed to resize clip: {str(e)}")
        return clip

def apply_filter(clip, filter_type):
    """Apply video filter to clip."""
    try:
        if filter_type == 'grayscale':
            return clip.fx(vfx.blackwhite)
        elif filter_type == 'sepia':
            def make_sepia(frame):
                frame_array = np.array(frame)
                sepia_matrix = np.array([
                    [0.393, 0.769, 0.189],
                    [0.349, 0.686, 0.168],
                    [0.272, 0.534, 0.131]
                ])
                sepia_image = np.dot(frame_array[...,:3], sepia_matrix.T)
                sepia_image = np.clip(sepia_image, 0, 255).astype(np.uint8)
                return sepia_image
            return clip.fl_image(make_sepia)
        elif filter_type == 'blur':
            return clip.fx(vfx.blur, radius=3.0)
        elif filter_type == 'sharpen':
            def sharpen(frame):
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                return cv2.filter2D(frame, -1, kernel)
            return clip.fl_image(sharpen)
        elif filter_type == 'invert':
            def invert(frame):
                return 255 - frame
            return clip.fl_image(invert)
        elif filter_type == 'bright':
            return clip.fx(vfx.colorx, factor=1.5)
        elif filter_type == 'dark':
            return clip.fx(vfx.colorx, factor=0.5)
        elif filter_type == 'contrast':
            return clip.fx(vfx.lum_contrast, contrast=50)
        elif filter_type == 'vignette':
            def add_vignette(frame):
                rows, cols = frame.shape[:2]
                # Generate vignette mask
                kernel_x = cv2.getGaussianKernel(cols, cols/2)
                kernel_y = cv2.getGaussianKernel(rows, rows/2)
                kernel = kernel_y * kernel_x.T
                mask = 255 * kernel / np.linalg.norm(kernel)
                mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
                vignetted = frame * (mask/255)
                return vignetted.astype(np.uint8)
            return clip.fl_image(add_vignette)
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

        internal_type, internal_position = transition_map.get(transition_type, (transition_type, position))

        # Create a copy of the clip to preserve audio
        clip_with_transition = clip.copy()

        if internal_type == 'fade':
            if internal_position == 'start':
                return clip.fx(vfx.fadein, duration)
            else:
                return clip.fx(vfx.fadeout, duration)

        elif internal_type == 'dissolve':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]

                if internal_position == 'start':
                    if t < duration:
                        # Create a checkerboard pattern for dissolve
                        pattern_size = 20
                        x = np.arange(w).reshape(1, w)
                        y = np.arange(h).reshape(h, 1)
                        pattern = ((x + y) // pattern_size) % 2

                        progress = t / duration
                        threshold = np.random.random(pattern.shape) * (1 - progress)
                        mask = pattern > threshold
                        mask = np.dstack([mask] * 3)
                        return frame * mask
                    return frame
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        pattern_size = 20
                        x = np.arange(w).reshape(1, w)
                        y = np.arange(h).reshape(h, 1)
                        pattern = ((x + y) // pattern_size) % 2

                        progress = remaining / duration
                        threshold = np.random.random(pattern.shape) * progress
                        mask = pattern > threshold
                        mask = np.dstack([mask] * 3)
                        return frame * mask
                    return frame

            new_clip = mp.VideoClip(make_frame, duration=clip.duration)
            new_clip.fps = clip.fps
            if clip.audio is not None:
                new_clip = new_clip.set_audio(clip.audio)
            return new_clip

        elif internal_type == 'slide':
            def get_slide_position(t):
                if internal_position == 'start':
                    if t < duration:
                        progress = t / duration
                        return (clip_width * (progress - 1), 'center')
                    return ('center', 'center')
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        progress = 1 - (remaining / duration)
                        return (clip_width * progress, 'center')
                    return ('center', 'center')

            sliding_clip = clip.set_position(get_slide_position)
            if clip.audio is not None:
                sliding_clip = sliding_clip.set_audio(clip.audio)
            return sliding_clip

        elif internal_type == 'zoom':
            def get_zoom_scale(t):
                if internal_position == 'start':
                    if t < duration:
                        # Start from 0.5 and zoom to 1.0
                        progress = t / duration
                        return 0.5 + 0.5 * progress
                    return 1.0
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        # Start from 1.0 and zoom to 0.5
                        progress = remaining / duration
                        return 0.5 + 0.5 * progress
                    return 1.0

            zoomed_clip = clip.fx(vfx.resize, lambda t: get_zoom_scale(t))
            if clip.audio is not None:
                zoomed_clip = zoomed_clip.set_audio(clip.audio)
            return zoomed_clip

        elif internal_type == 'rotate':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                center = (w//2, h//2)

                if internal_position == 'start':
                    if t < duration:
                        angle = 360 * (1 - t/duration)
                        scale = t/duration
                    else:
                        angle = 0
                        scale = 1
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        angle = 360 * (1 - remaining/duration)
                        scale = remaining/duration
                    else:
                        angle = 0
                        scale = 1

                if scale > 0:
                    matrix = cv2.getRotationMatrix2D(center, angle, scale)
                    rotated = cv2.warpAffine(frame, matrix, (w, h))
                    return rotated
                return np.zeros_like(frame)

            new_clip = mp.VideoClip(make_frame, duration=clip.duration)
            new_clip.fps = clip.fps
            if clip.audio is not None:
                new_clip = new_clip.set_audio(clip.audio)
            return new_clip

        elif internal_type == 'wipe':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                mask = np.zeros((h, w))

                if internal_position == 'start':
                    if t < duration:
                        edge = int(w * (t/duration))
                        mask[:, :edge] = 1
                    else:
                        mask[:, :] = 1
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        edge = int(w * (remaining/duration))
                        mask[:, :edge] = 1
                    else:
                        mask[:, :] = 1

                mask = np.dstack([mask] * 3)
                return frame * mask

            new_clip = mp.VideoClip(make_frame, duration=clip.duration)
            new_clip.fps = clip.fps
            if clip.audio is not None:
                new_clip = new_clip.set_audio(clip.audio)
            return new_clip

        elif internal_type == 'blur':
            def make_frame(t):
                frame = clip.get_frame(t)
                if internal_position == 'start':
                    if t < duration:
                        sigma = 20 * (1 - t/duration)
                        return cv2.GaussianBlur(frame, (0,0), sigma)
                    return frame
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        sigma = 20 * (1 - remaining/duration)
                        return cv2.GaussianBlur(frame, (0,0), sigma)
                    return frame

            new_clip = mp.VideoClip(make_frame, duration=clip.duration)
            new_clip.fps = clip.fps
            if clip.audio is not None:
                new_clip = new_clip.set_audio(clip.audio)
            return new_clip

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
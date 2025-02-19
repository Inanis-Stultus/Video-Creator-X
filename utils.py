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
        # Keep all existing filter cases unchanged
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
            def blur_frame(frame):
                return cv2.GaussianBlur(frame, (15, 15), 0)
            return clip.fl_image(blur_frame)
        elif filter_type == 'sharpen':
            def sharpen(frame):
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                return cv2.filter2D(frame, -1, kernel)
            return clip.fl_image(sharpen)
        elif filter_type == 'bright':
            return clip.fx(vfx.colorx, factor=1.5)
        elif filter_type == 'dark':
            return clip.fx(vfx.colorx, factor=0.5)
        elif filter_type == 'contrast':
            return clip.fx(vfx.lum_contrast, contrast=50)
        elif filter_type == 'mirror':
            return clip.fx(vfx.mirror_x)

        # New filters start here
        elif filter_type == 'cartoon':
            def cartoonize(frame):
                # Convert to float and normalize
                frame = frame.astype(np.float32) / 255.0
                # Edge detection
                edges = cv2.Canny(cv2.convertScaleAbs(frame), 100, 200)
                edges = cv2.dilate(edges, None)
                edges = edges.astype(np.float32) / 255.0
                # Color quantization
                frame = frame * 4
                frame = frame.astype(np.uint8)
                frame = frame * 64
                # Combine edges with color quantization
                frame = frame.astype(np.float32) / 255.0
                cartoon = frame * (1 - edges[:,:,np.newaxis])
                return (cartoon * 255).astype(np.uint8)
            return clip.fl_image(cartoonize)

        elif filter_type == 'oil_painting':
            def oil_paint(frame):
                # Oil painting effect parameters
                radius = 4
                intensity_levels = 12
                # Convert to float32
                frame_f = frame.astype(np.float32)
                # Calculate intensity
                intensity = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                # Create output image
                output = np.zeros_like(frame_f)
                # Apply oil painting effect
                for i in range(-radius, radius + 1):
                    for j in range(-radius, radius + 1):
                        if i*i + j*j <= radius*radius:
                            shifted = np.roll(np.roll(frame_f, i, axis=0), j, axis=1)
                            shifted_intensity = np.roll(np.roll(intensity, i, axis=0), j, axis=1)
                            output += shifted * (shifted_intensity[:,:,np.newaxis] / 255.0)
                output = output / ((2*radius+1)**2)
                return output.astype(np.uint8)
            return clip.fl_image(oil_paint)

        elif filter_type == 'rainbow':
            def add_rainbow(frame):
                height, width = frame.shape[:2]
                # Create rainbow gradient
                rainbow = np.zeros((height, width, 3), dtype=np.uint8)
                for i in range(width):
                    hue = (i / width * 180).astype(np.uint8)
                    rainbow[:,i] = [hue, 255, 255]
                rainbow = cv2.cvtColor(rainbow, cv2.COLOR_HSV2RGB)
                # Blend with original frame
                return cv2.addWeighted(frame, 0.7, rainbow, 0.3, 0)
            return clip.fl_image(add_rainbow)

        elif filter_type == 'neon':
            def neon_effect(frame):
                # Edge detection
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                edges = cv2.dilate(edges, None)
                # Create neon effect
                edges = cv2.GaussianBlur(edges, (9, 9), 0)
                # Colorize edges
                edges_color = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
                edges_color[:,:,0] = edges  # Blue channel
                edges_color[:,:,1] = 0      # Green channel
                edges_color[:,:,2] = edges  # Red channel
                # Blend with original
                return cv2.addWeighted(frame, 0.7, edges_color, 0.3, 0)
            return clip.fl_image(neon_effect)

        elif filter_type == 'thermal':
            def thermal_effect(frame):
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                # Apply color map
                thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
                # Convert back to RGB
                return cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB)
            return clip.fl_image(thermal_effect)

        elif filter_type == 'pencil_sketch':
            def sketch_effect(frame):
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                # Invert
                inv = 255 - gray
                # Apply Gaussian blur
                blur = cv2.GaussianBlur(inv, (21, 21), 0)
                # Blend
                sketch = cv2.divide(gray, 255-blur, scale=256.0)
                # Convert back to RGB
                return cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)
            return clip.fl_image(sketch_effect)

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
            # Keep all existing transitions
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
            'blur-out': ('blur', 'end'),
            # New transitions
            'ripple-in': ('ripple', 'start'),
            'ripple-out': ('ripple', 'end'),
            'spiral-in': ('spiral', 'start'),
            'spiral-out': ('spiral', 'end'),
            'matrix-in': ('matrix', 'start'),
            'matrix-out': ('matrix', 'end'),
            'heart-in': ('heart', 'start'),
            'heart-out': ('heart', 'end'),
            'shatter-in': ('shatter', 'start'),
            'shatter-out': ('shatter', 'end')
        }

        internal_type, internal_position = transition_map.get(transition_type, (transition_type, position))

        # Keep all existing transition effects unchanged
        if internal_type == 'fade':
            if internal_position == 'start':
                return clip.fx(vfx.fadein, duration)
            else:
                return clip.fx(vfx.fadeout, duration)
        elif internal_type == 'dissolve':
            # Fixed dissolve effect with proper audio handling
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]

                if internal_position == 'start':
                    if t < duration:
                        # Use fixed random seed for consistent pattern
                        np.random.seed(42)
                        mask = np.random.random((h, w))
                        threshold = t / duration
                        mask = mask < threshold
                        mask = np.dstack([mask] * 3)
                        return frame * mask
                    return frame
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        np.random.seed(42)
                        mask = np.random.random((h, w))
                        threshold = remaining / duration
                        mask = mask < threshold
                        mask = np.dstack([mask] * 3)
                        return frame * mask
                    return frame

            new_clip = mp.VideoClip(make_frame, duration=clip.duration)
            new_clip.fps = clip.fps
            # Preserve audio from original clip
            if clip.audio is not None:
                new_clip = new_clip.set_audio(clip.audio)
            return new_clip
        elif internal_type == 'slide':
            # Fixed slide transition with independent start/end positions
            def get_slide_position(t):
                original_x, original_y = original_pos(t) if callable(original_pos) else original_pos
                original_x = 0 if original_x == 'center' else original_x

                if internal_position == 'start':
                    if t < duration:
                        progress = t / duration
                        # Start from right (screen width) and slide to center
                        x_offset = clip_width * (1 - progress)
                        return (x_offset, 'center')
                    return ('center', 'center')
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        progress = remaining / duration
                        # Start at center and slide to left (-screen width)
                        x_offset = -clip_width * (1 - progress)
                        return (x_offset, 'center')
                    return ('center', 'center')

            return clip.set_position(get_slide_position)
        elif internal_type == 'zoom':
            # Fixed zoom transition with correct scaling
            def get_zoom_scale(t):
                if internal_position == 'start':
                    if t < duration:
                        # Start from 0.2 (small) and zoom to 1.0 (normal)
                        progress = t / duration
                        return 0.2 + (0.8 * progress)
                    return 1.0
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        # Start from 1.0 (normal) and zoom to 0.2 (small)
                        progress = remaining / duration
                        return 1.0 - (0.8 * (1 - progress))
                    return 1.0

            return clip.fx(vfx.resize, lambda t: get_zoom_scale(t))
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
            return new_clip
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
            return new_clip

        # New transition effects start here
        elif internal_type == 'ripple':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]

                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1

                center = (w//2, h//2)
                max_radius = np.sqrt(w**2 + h**2)
                radius = int(max_radius * progress)

                # Create ripple effect
                y, x = np.ogrid[:h, :w]
                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
                ripple = np.sin(dist/10 - radius/10) * progress
                ripple = np.dstack([ripple, ripple, ripple])

                return cv2.addWeighted(frame, 1-progress, (frame * (1 + ripple)).clip(0, 255).astype(np.uint8), progress, 0)

            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'spiral':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]

                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1

                center = (w//2, h//2)
                y, x = np.ogrid[:h, :w]
                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
                angle = np.arctan2(y - center[1], x - center[0])
                mask = (angle + dist/10) < (progress * 20)
                mask = mask.astype(np.float32)
                mask = np.dstack([mask, mask, mask])

                return (frame * mask).astype(np.uint8)

            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'matrix':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]

                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1

                # Create digital rain effect
                matrix = np.random.rand(h, w) < (progress * 0.3)
                rain = np.roll(matrix, int(progress * h//2), axis=0)
                rain = np.dstack([rain * 0.1, rain * 0.8, rain * 0.3])  # Green tint

                return cv2.addWeighted(frame, progress, (rain * 255).astype(np.uint8), 1-progress, 0)

            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'heart':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]

                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1

                # Create heart shape mask
                center = (w//2, h//2)
                size = int(min(w, h) * progress)
                mask = np.zeros((h, w))
                y, x = np.ogrid[:h, :w]
                # Heart shape equation
                inside_heart = ((x - center[0])**2 + (y - center[1])**2 - size**2)**3 - (x - center[0])**2 * (y - center[1])**3 < 0
                mask[inside_heart] = 1
                mask = np.dstack([mask, mask, mask])

                return (frame * mask).astype(np.uint8)

            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'shatter':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]

                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1

                # Create shatter effect
                pieces = 20
                piece_h = h // pieces
                piece_w = w // pieces
                shattered = np.zeros_like(frame)

                for i in range(pieces):
                    for j in range(pieces):
                        y1 = i * piece_h
                        y2 = (i + 1) * piece_h
                        x1 = j * piece_w
                        x2 = (j + 1) * piece_w

                        # Random displacement based on progress
                        if progress < 1:
                            dx = int(np.random.normal(0, 50 * (1-progress)))
                            dy = int(np.random.normal(0, 50 * (1-progress)))

                            # Ensure we stay within bounds
                            y1_new = max(0, min(h-piece_h, y1 + dy))
                            x1_new = max(0, min(w-piece_w, x1 + dx))
                            y2_new = y1_new + piece_h
                            x2_new = x1_new + piece_w

                            shattered[y1_new:y2_new, x1_new:x2_new] = frame[y1:y2, x1:x2]
                        else:
                            shattered[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

                return shattered.astype(np.uint8)

            return create_clip_with_audio(clip, make_frame)

        # Keep all other existing transition effects unchanged
        return clip
    except Exception as e:
        logger.error(f"Failed to apply transition: {str(e)}")
        return clip

def create_clip_with_audio(original_clip, make_frame_func):
    """Helper function to create a new clip while preserving audio"""
    new_clip = mp.VideoClip(make_frame_func, duration=original_clip.duration)
    new_clip.fps = original_clip.fps
    if original_clip.audio is not None:
        new_clip = new_clip.set_audio(original_clip.audio)
    return new_clip

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
import os
import logging
import base64
import tempfile
import moviepy.editor as mp
from moviepy.video.fx import all as vfx
import cv2
import numpy as np


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

def calculate_progress(t, clip_duration, duration, position):
    if position == 'start':
        return min(1, t / duration)
    else:
        return max(0, (clip_duration - t) / duration)

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
                # Converte o frame para um array numpy
                img = np.array(frame)

                # Importa cv2 dentro da função
                import cv2

                # Converte para escala de cinza
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

                # Reduz o blur para manter mais detalhes (de 7 para 3)
                blurred = cv2.medianBlur(gray, 1)

                # Ajusta o threshold para bordas mais nítidas
                edges = cv2.adaptiveThreshold(blurred, 255,
                                              cv2.ADAPTIVE_THRESH_MEAN_C,
                                              cv2.THRESH_BINARY, 9, 9)

                # Reduz menos as cores para manter detalhes (ajuste nos parâmetros do bilateral)
                color = cv2.bilateralFilter(img, 7, 150, 150)

                # Combina as bordas com as cores
                cartoon = cv2.bitwise_and(color, color, mask=edges)

                return cartoon

            return clip.fl_image(cartoonize)


        elif filter_type == 'oil_painting':

            def oil_paint(frame):
                # Convert from RGB (MoviePy) to BGR (OpenCV)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Apply smoothing to simulate brush strokes
                smoothed = cv2.medianBlur(frame_bgr, 7)

                # Enhance contrast and brightness
                enhanced = cv2.convertScaleAbs(smoothed, alpha=1.1, beta=10)  # Menos contraste para evitar exagero

                # Convert to HSV to adjust saturation
                hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
                hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.40)  # Aumenta saturação em 50%

                # Convert back to RGB
                frame_rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

                return frame_rgb

            return clip.fl_image(oil_paint)


        # Rainbow Filter

        elif filter_type == 'rainbow':

            def add_rainbow(frame):

                height, width = frame.shape[:2]

                rainbow = np.zeros((height, width, 3), dtype=np.uint8)

                for i in range(width):
                    hue = int((i / width) * 180)

                    rainbow[:, i] = [hue, 255, 255]

                rainbow = cv2.cvtColor(rainbow, cv2.COLOR_HSV2RGB)

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

        # New filters
        elif filter_type == 'invert':
            def invert(frame):
                return cv2.bitwise_not(frame)

            return clip.fl_image(invert)

        elif filter_type == 'emboss':
            def emboss(frame):
                kernel = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]])
                embossed = cv2.filter2D(frame, -1, kernel)
                return cv2.cvtColor(embossed, cv2.COLOR_BGR2RGB)

            return clip.fl_image(emboss)


        # Glitch Effect Filter

        elif filter_type == 'glitch':

            def glitch_effect(frame):

                height, width, _ = frame.shape

                shift = width // 10

                frame[:, :shift] = np.flip(frame[:, :shift], axis=1)

                frame[:, width - shift:] = np.flip(frame[:, width - shift:], axis=1)

                return frame

            return clip.fl_image(glitch_effect)


        # Pixelate Filter

        elif filter_type == 'pixelate':

            def pixelate(frame):

                height, width = frame.shape[:2]

                small = cv2.resize(frame, (width // 10, height // 10), interpolation=cv2.INTER_LINEAR)

                return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)

            return clip.fl_image(pixelate)

        elif filter_type == 'edge_detect':
            def edge_detect(frame):
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            return clip.fl_image(edge_detect)

        elif filter_type == 'posterize':
            def posterize(frame):
                return cv2.convertScaleAbs(frame // 64 * 64)

            return clip.fl_image(posterize)


        # Solarize Filter

        elif filter_type == 'solarize':

            def solarize(frame):

                # Converte para escala de cinza para análise de brilho

                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

                _, mask = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

                # Inverte apenas as áreas brilhantes

                inverted = cv2.bitwise_not(frame)

                result = np.where(mask[..., None] == 255, inverted, frame)

                return result

            return clip.fl_image(solarize)

        elif filter_type == 'vignette':
            def vignette(frame):
                rows, cols = frame.shape[:2]
                kernel_x = cv2.getGaussianKernel(cols, 200)
                kernel_y = cv2.getGaussianKernel(rows, 200)
                kernel = kernel_y * kernel_x.T
                mask = 255 * kernel / np.linalg.norm(kernel)
                vignette = np.copy(frame)
                for i in range(3):
                    vignette[:, :, i] = vignette[:, :, i] * mask
                return vignette.astype(np.uint8)

            return clip.fl_image(vignette)

        elif filter_type == 'halftone':
            def halftone(frame):
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
                return cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)

            return clip.fl_image(halftone)

        elif filter_type == 'noise':
            def add_noise(frame):
                noise = np.random.normal(0, 25, frame.shape).astype(np.uint8)
                noisy_frame = cv2.add(frame, noise)
                return np.clip(noisy_frame, 0, 255)

            return clip.fl_image(add_noise)

        elif filter_type == 'color_shift':
            def color_shift(frame):
                b, g, r = cv2.split(frame)
                shifted = cv2.merge((g, r, b))
                return shifted

            return clip.fl_image(color_shift)

        return clip
    except Exception as e:
        logger.error(f"Failed to apply filter {filter_type}: {str(e)}")
        return clip
def apply_transition(clip, transition_type='fade-in', duration=1.0, position='start'):
    """Apply transition effect to a clip at the start or end."""
    try:
        if transition_type == 'none':
            return clip

        # Armazena posição e tamanho original
        original_pos = clip.pos if hasattr(clip, 'pos') else lambda t: ('center', 'center')
        clip_width, clip_height = clip.size

        # Mapeamento dos nomes de transição (UI) para os nomes internos e posição
        transition_map = {
            # Transições existentes
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
            'ripple-in': ('ripple', 'start'),
            'ripple-out': ('ripple', 'end'),
            'spiral-in': ('spiral', 'start'),
            'spiral-out': ('spiral', 'end'),
            'matrix-in': ('matrix', 'start'),
            'matrix-out': ('matrix', 'end'),
            'heart-in': ('heart', 'start'),
            'heart-out': ('heart', 'end'),
            'shatter-in': ('shatter', 'start'),
            'shatter-out': ('shatter', 'end'),
            # Novas transições
            'glitch-in': ('glitch', 'start'),
            'glitch-out': ('glitch', 'end'),
            'pixelate-in': ('pixelate', 'start'),
            'pixelate-out': ('pixelate', 'end'),
            'circle-wipe-in': ('circle-wipe', 'start'),
            'circle-wipe-out': ('circle-wipe', 'end'),
            'swirl-in': ('swirl', 'start'),
            'swirl-out': ('swirl', 'end'),
            'wave-in': ('wave', 'start'),
            'wave-out': ('wave', 'end'),
            'tile-in': ('tile', 'start'),
            'tile-out': ('tile', 'end'),
            'color-shift-in': ('color-shift', 'start'),
            'color-shift-out': ('color-shift', 'end')
        }

        internal_type, internal_position = transition_map.get(transition_type, (transition_type, position))

        # ---------------------------------------------------
        # Transições já implementadas (fade, dissolve, wipe, slide, rotate, zoom, blur, matrix, heart, shatter)
        # ---------------------------------------------------
        if internal_type == 'matrix':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                # Efeito digital "Matrix"
                matrix = np.random.rand(h, w) < (progress * 0.3)
                rain = np.roll(matrix, int(progress * h // 2), axis=0)
                rain = np.dstack([rain * 0.1, rain * 0.8, rain * 0.3])  # tonalidade verde
                return cv2.addWeighted(frame, progress, (rain * 255).astype(np.uint8), 1 - progress, 0)
            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'heart':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                center = (w // 2, h // 2)
                size = int(min(w, h) * progress)
                mask = np.zeros((h, w))
                y, x = np.ogrid[:h, :w]
                # Equação para forma de coração
                inside_heart = ((x - center[0]) ** 2 + (y - center[1]) ** 2 - size ** 2) ** 3 - (x - center[0]) ** 2 * (y - center[1]) ** 3 < 0
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
                        if progress < 1:
                            dx = int(np.random.normal(0, 50 * (1 - progress)))
                            dy = int(np.random.normal(0, 50 * (1 - progress)))
                            y1_new = max(0, min(h - piece_h, y1 + dy))
                            x1_new = max(0, min(w - piece_w, x1 + dx))
                            y2_new = y1_new + piece_h
                            x2_new = x1_new + piece_w
                            shattered[y1_new:y2_new, x1_new:x2_new] = frame[y1:y2, x1:x2]
                        else:
                            shattered[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
                return shattered.astype(np.uint8)
            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'fade':
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
            if clip.audio is not None:
                new_clip = new_clip.set_audio(clip.audio)
            return new_clip

        elif internal_type == 'slide':
            def get_combined_slide_position(t):
                if callable(original_pos):
                    original_x, original_y = original_pos(t)
                else:
                    original_x, original_y = original_pos
                if original_x == 'center':
                    original_x = 0
                if original_y == 'center':
                    original_y = 0
                x_offset = original_x
                if internal_position == 'start' and 0 <= t < duration:
                    progress = t / duration
                    x_offset = -clip_width * (1 - progress)
                elif internal_position == 'end':
                    remaining = max(0, clip.duration - t)
                    if remaining < duration:
                        progress = remaining / duration
                        x_offset = -clip_width * (1 - progress)
                return (x_offset, original_y)
            return clip.set_position(get_combined_slide_position)

        elif internal_type == 'zoom':
            def get_zoom_scale(t):
                if position == 'start':
                    if t < duration:
                        progress = t / duration
                        scale = 0.1 + (0.9 * progress)
                        return scale
                    return 1.0
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        progress = remaining / duration
                        scale = 1.0 - (0.9 * (1 - progress))
                        return scale
                    return 1.0
            centered_clip = clip.set_position(('center', 'center'))
            def make_zoomed_frame(t):
                scale = get_zoom_scale(t)
                new_width = int(clip_width * scale)
                new_height = int(clip_height * scale)
                frame = clip.get_frame(t)
                resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
                output_frame = np.zeros((clip_height, clip_width, 3), dtype=np.uint8)
                y_offset = (clip_height - new_height) // 2
                x_offset = (clip_width - new_width) // 2
                output_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame
                return output_frame
            zoomed_clip = mp.VideoClip(make_zoomed_frame, duration=clip.duration)
            zoomed_clip.fps = clip.fps
            if clip.audio is not None:
                zoomed_clip = zoomed_clip.set_audio(clip.audio)
            final_clip = zoomed_clip.set_position(('center', 'center'))
            return final_clip

        elif internal_type == 'wipe':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                mask = np.zeros((h, w))
                if internal_position == 'start':
                    if t < duration:
                        edge = int(w * (t / duration))
                        mask[:, :edge] = 1
                    else:
                        mask[:, :] = 1
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        edge = int(w * (remaining / duration))
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

        elif internal_type == 'rotate':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                center = (w // 2, h // 2)
                if internal_position == 'start':
                    if t < duration:
                        angle = 360 * (1 - t / duration)
                        scale = t / duration
                    else:
                        angle = 0
                        scale = 1
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        angle = 360 * (1 - remaining / duration)
                        scale = remaining / duration
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

        elif internal_type == 'blur':
            def make_frame(t):
                frame = clip.get_frame(t)
                if internal_position == 'start':
                    if t < duration:
                        sigma = 20 * (1 - t / duration)
                        return cv2.GaussianBlur(frame, (0, 0), sigma)
                    return frame
                else:
                    remaining = clip.duration - t
                    if remaining < duration:
                        sigma = 20 * (1 - remaining / duration)
                        return cv2.GaussianBlur(frame, (0, 0), sigma)
                    return frame
            new_clip = mp.VideoClip(make_frame, duration=clip.duration)
            new_clip.fps = clip.fps
            if clip.audio is not None:
                new_clip = new_clip.set_audio(clip.audio)
            return new_clip

        # ---------------------------------------------------
        # Novas transições
        # ---------------------------------------------------

        elif internal_type == 'glitch':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                output = frame.copy()
                stripe_height = 5  # altura da faixa em pixels
                for y in range(0, h, stripe_height):
                    offset = int(np.random.normal(0, 30 * (1 - progress)))
                    y_end = min(y + stripe_height, h)
                    output[y:y_end, :] = np.roll(frame[y:y_end, :], shift=offset, axis=1)
                return output
            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'pixelate':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                # De 10% (muito pixelado) a 100% (normal)
                scale = 0.1 + 0.9 * progress
                new_w = max(1, int(w * scale))
                new_h = max(1, int(h * scale))
                small = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
                pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
                return pixelated
            return create_clip_with_audio(clip, make_frame)


        elif internal_type == 'circle-wipe':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                center = (w // 2, h // 2)
                max_radius = np.sqrt(center[0] ** 2 + center[1] ** 2)

                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1

                radius = progress * max_radius
                Y, X = np.ogrid[:h, :w]
                dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
                mask = (dist_from_center <= radius).astype(np.float32)
                mask = np.dstack([mask, mask, mask])
                return (frame * mask).astype(np.uint8)
            return create_clip_with_audio(clip, make_frame)


        elif internal_type == 'swirl':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                center = (w / 2, h / 2)
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                max_angle = 2 * np.pi
                angle_offset = max_angle * (1 - progress)
                X, Y = np.meshgrid(np.arange(w), np.arange(h))
                Xc = X - center[0]
                Yc = Y - center[1]
                theta = np.arctan2(Yc, Xc) + angle_offset * np.exp(-((Xc**2 + Yc**2) / (2*(max(w, h)/2)**2)))
                radius = np.sqrt(Xc**2 + Yc**2)
                map_x = (radius * np.cos(theta) + center[0]).astype(np.float32)
                map_y = (radius * np.sin(theta) + center[1]).astype(np.float32)
                swirled = cv2.remap(frame, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                return swirled
            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'wave':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                amplitude = 10 * (1 - progress)
                frequency = 2
                X, Y = np.meshgrid(np.arange(w), np.arange(h))
                shift = amplitude * np.sin(2 * np.pi * Y / 30 * frequency)
                map_x = (X + shift).astype(np.float32)
                map_y = Y.astype(np.float32)
                waved = cv2.remap(frame, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                return waved
            return create_clip_with_audio(clip, make_frame)


        elif internal_type == 'tile':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                tiles_x, tiles_y = 10, 10
                tile_w = w // tiles_x
                tile_h = h // tiles_y
                np.random.seed(42)

                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                    output = np.zeros_like(frame)

                    for i in range(tiles_y):
                        for j in range(tiles_x):
                            threshold = np.random.rand()

                            if progress > threshold:
                                x1 = j * tile_w
                                y1 = i * tile_h
                                x2 = x1 + tile_w if j < tiles_x - 1 else w
                                y2 = y1 + tile_h if i < tiles_y - 1 else h
                                output[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

                else:  # 'end'
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                    output = frame.copy()

                    for i in range(tiles_y):
                        for j in range(tiles_x):
                            threshold = np.random.rand()

                            # Aqui, quanto maior (1 - progress), mais blocos serão removidos
                            if (1 - progress) > threshold:
                                x1 = j * tile_w
                                y1 = i * tile_h
                                x2 = x1 + tile_w if j < tiles_x - 1 else w
                                y2 = y1 + tile_h if i < tiles_y - 1 else h
                                output[y1:y2, x1:x2] = 0

                return output
            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'color-shift':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                max_offset = 20
                offset = int(max_offset * (1 - progress))
                b, g, r = cv2.split(frame)
                M_right = np.float32([[1, 0, offset], [0, 1, 0]])
                M_left = np.float32([[1, 0, -offset], [0, 1, 0]])
                shifted_r = cv2.warpAffine(r, M_right, (w, h))
                shifted_b = cv2.warpAffine(b, M_left, (w, h))
                merged = cv2.merge([shifted_b, g, shifted_r])
                return merged
            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'ripple':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                center = (w / 2, h / 2)
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                amplitude = 5 * (1 - progress)
                wavelength = 20
                X, Y = np.meshgrid(np.arange(w), np.arange(h))
                distance = np.sqrt((X - center[0])**2 + (Y - center[1])**2)
                displacement = amplitude * np.sin(2 * np.pi * distance / wavelength)
                eps = 1e-5
                dx = displacement * (X - center[0]) / (distance + eps)
                dy = displacement * (Y - center[1]) / (distance + eps)
                map_x = (X + dx).astype(np.float32)
                map_y = (Y + dy).astype(np.float32)
                rippled = cv2.remap(frame, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                return rippled
            return create_clip_with_audio(clip, make_frame)

        elif internal_type == 'spiral':
            def make_frame(t):
                frame = clip.get_frame(t)
                h, w = frame.shape[:2]
                center = (w / 2, h / 2)
                if internal_position == 'start':
                    progress = min(1, t / duration) if t < duration else 1
                else:
                    progress = max(0, (clip.duration - t) / duration) if t > clip.duration - duration else 1
                max_angle = 2 * np.pi
                angle_offset = max_angle * (1 - progress)
                X, Y = np.meshgrid(np.arange(w), np.arange(h))
                Xc = X - center[0]
                Yc = Y - center[1]
                radius = np.sqrt(Xc**2 + Yc**2)
                theta = np.arctan2(Yc, Xc) + angle_offset
                map_x = (radius * np.cos(theta) + center[0]).astype(np.float32)
                map_y = (radius * np.sin(theta) + center[1]).astype(np.float32)
                spiraled = cv2.remap(frame, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                return spiraled
            return create_clip_with_audio(clip, make_frame)

        # Caso nenhuma transição seja aplicada, retorna o clipe original
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

def process_video(timeline, output_path, target_resolution=None, background_audio=None):
    """Process video clips according to timeline."""
    input_clips = []
    clips = []
    temp_files = []  # Track temporary files for cleanup
    transition_duration = 1.0  # Default transition duration

    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Load background audio if provided
            background_audio_clip = None
            if background_audio:
                try:
                    # Decode base64 data and save to temporary file
                    binary_data = base64.b64decode(background_audio)
                    temp_audio_path = os.path.join(temp_dir, 'background_audio.mp3')
                    with open(temp_audio_path, 'wb') as f:
                        f.write(binary_data)
                    background_audio_clip = mp.AudioFileClip(temp_audio_path)
                    temp_files.append(temp_audio_path)
                except Exception as e:
                    logger.error(f"Failed to load background audio: {str(e)}")

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
                keep_audio = item.get('keepAudio', False)

                try:
                    if item['filename'].lower().endswith(('.png', '.jpg', '.jpeg')):
                        clip = mp.ImageClip(temp_path, duration=duration)
                    elif item['filename'].lower().endswith('.gif'):
                        clip = mp.VideoFileClip(temp_path).loop(duration=duration)
                    else:
                        # Add error handling for video frame reading
                        clip = mp.VideoFileClip(temp_path)
                        # Verify clip can be read
                        test_frame = clip.get_frame(0)
                        if test_frame is None or len(test_frame.shape) != 3:
                            raise ValueError(f"Invalid video frame in {item['filename']}")
                        if not keep_audio:
                            clip = clip.without_audio()

                    input_clips.append(clip)
                    logger.info(f"Successfully loaded clip: {item['filename']}")
                except Exception as e:
                    logger.error(f"Failed to load clip {item['filename']}: {str(e)}")
                    raise

            # Determine target resolution from loaded clips
            if target_resolution:
                target_width, target_height = target_resolution
            else:
                target_width, target_height = get_max_resolution(input_clips)
                logger.info(f"Using max resolution from media: {target_width}x{target_height}")

            # Process each clip
            for idx, (item, clip) in enumerate(zip(timeline, input_clips)):
                try:
                    # Resize clip to target resolution with proper centering
                    clip = resize_clip_maintain_aspect(clip, target_width, target_height)
                    clip.set_position(('center', 'center'))

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
                    logger.info(f"Successfully processed clip {idx + 1}/{len(timeline)}")
                except Exception as e:
                    logger.error(f"Failed to process clip {idx + 1}: {str(e)}")
                    raise

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

            # Add background audio if provided
            if background_audio_clip:
                # Loop the background audio if it's shorter than the video
                if background_audio_clip.duration < final_clip.duration:
                    num_loops = int(np.ceil(final_clip.duration / background_audio_clip.duration))
                    background_audio_clip = mp.concatenate_audioclips([background_audio_clip] * num_loops)
                # Trim the audio if it's longer than the video
                background_audio_clip = background_audio_clip.subclip(0, final_clip.duration)

                # Combine video's original audio (if any) with background audio
                if final_clip.audio is not None:
                    final_audio = mp.CompositeAudioClip([
                        background_audio_clip.volumex(0.5),  # Background audio at 50% volume
                        final_clip.audio.volumex(1.0)  # Original audio at 100% volume
                    ])
                else:
                    final_audio = background_audio_clip

                final_clip = final_clip.set_audio(final_audio)

            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)

            # Cleanup clips to free memory
            for clip in input_clips + clips:
                try:
                    clip.close()
                except:
                    pass
            if background_audio_clip:
                try:
                    background_audio_clip.close()
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
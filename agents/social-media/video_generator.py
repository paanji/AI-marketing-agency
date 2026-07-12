"""
Video Generator
---------------
Turns a folder of a client's own photos into a short, platform-ready video:
Ken Burns pan/zoom on each image, crossfade-free hard cuts between them (kept
simple/robust over fancy transitions), a short caption overlay, and an
optional AI voiceover (OpenAI TTS) mixed with optional background music.

PLUGGABILITY: this is one interchangeable "provider" behind a small registry
(VIDEO_PROVIDERS) at the bottom of this file. When you're ready to add a
real AI-generated-footage vendor (Runway, Pika, Kling, Sora, Veo), write a
function with the same signature as generate_slideshow() and register it
under "ai_generated". Nothing in social_media_agent.py needs to change --
it already just calls VIDEO_PROVIDERS[config["video"]["provider"]](...).

Requires ffmpeg on PATH (present by default on GitHub's ubuntu-latest
runners; the workflow installs it explicitly anyway for reliability).

Fails soft: if no media is available, or ffmpeg/TTS fails, this raises a
specific exception that social_media_agent.py catches per-item -- one
client's missing photos or one bad API call never takes down the whole run.
"""

import os
import glob
import json
import subprocess
import tempfile
import urllib.request

SUPPORTED_IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")


class VideoGenerationError(Exception):
    pass


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoGenerationError(f"ffmpeg command failed: {' '.join(cmd)}\n{result.stderr[-800:]}")
    return result


def _generate_voiceover(text, out_path, openai_cfg):
    """Calls OpenAI's TTS endpoint. Fails soft -- returns False instead of
    raising, so a missing/invalid API key never blocks video generation.
    The result is a silent (or music-only) video rather than a failed run."""
    api_key_env = openai_cfg.get("openai_api_key_env", "OPENAI_API_KEY")
    api_key = os.environ.get(api_key_env)
    if not api_key or not text:
        return False
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/speech",
            data=json.dumps({
                "model": "gpt-4o-mini-tts",
                "voice": "alloy",
                "input": text[:2000],
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            audio_bytes = resp.read()
        with open(out_path, "wb") as f:
            f.write(audio_bytes)
        return True
    except Exception:
        return False


def generate_slideshow(media_folder, output_path, caption_text, voiceover_text, video_cfg, openai_cfg):
    """
    media_folder: directory containing images (jpg/png/webp). Video clips
        in this folder aren't handled by this provider yet -- images only
        for now. Supporting a mix of photos and short clips is a natural
        next step if a client wants it.
    output_path: where to write the final .mp4
    caption_text: short text baked into the video as an overlay (a
        headline, not a script -- kept under ~90 characters)
    voiceover_text: text to speak if TTS is enabled and available. Falls
        back to silent (or music-only) video if unavailable.
    video_cfg: config.json's `video` block
    openai_cfg: config.json's top-level dict (for openai_api_key_env)
    """
    images = sorted(
        f for f in glob.glob(os.path.join(media_folder, "*"))
        if f.lower().endswith(SUPPORTED_IMAGE_EXT)
    )
    if not images:
        raise VideoGenerationError(f"No supported images found in {media_folder}")

    width, height = video_cfg.get("resolution", [1080, 1920])  # vertical default
    seconds_per_image = video_cfg.get("seconds_per_image", 3)
    fps = video_cfg.get("fps", 30)
    frames = seconds_per_image * fps

    with tempfile.TemporaryDirectory() as tmp:
        # 1. One Ken-Burns clip per image
        clip_paths = []
        for i, img in enumerate(images):
            clip_path = os.path.join(tmp, f"clip_{i}.mp4")
            zoompan = (
                f"scale=8000:-1,zoompan=z='min(zoom+0.0008,1.15)':"
                f"d={frames}:s={width}x{height}:fps={fps}"
            )
            _run([
                "ffmpeg", "-y", "-loop", "1", "-i", img,
                "-vf", zoompan, "-t", str(seconds_per_image),
                "-pix_fmt", "yuv420p", clip_path,
            ])
            clip_paths.append(clip_path)

        # 2. Concatenate
        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w") as f:
            for c in clip_paths:
                f.write(f"file '{c}'\n")
        stitched = os.path.join(tmp, "stitched.mp4")
        _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list, "-c", "copy", stitched,
        ])

        # 3. Caption overlay
        safe_caption = caption_text.replace("'", "").replace(":", "-").replace("\n", " ")[:90]
        captioned = os.path.join(tmp, "captioned.mp4")
        drawtext = (
            f"drawtext=text='{safe_caption}':fontcolor=white:fontsize=48:"
            f"box=1:boxcolor=black@0.5:boxborderw=20:"
            f"x=(w-text_w)/2:y=h-th-120"
        )
        _run([
            "ffmpeg", "-y", "-i", stitched, "-vf", drawtext,
            "-codec:a", "copy", captioned,
        ])

        # 4. Optional voiceover + optional background music
        audio_track = None
        if video_cfg.get("use_voiceover", True):
            vo_path = os.path.join(tmp, "voiceover.mp3")
            if _generate_voiceover(voiceover_text, vo_path, openai_cfg):
                audio_track = vo_path

        music_path = video_cfg.get("background_music_path")
        has_music = bool(music_path and os.path.exists(music_path))

        if audio_track or has_music:
            inputs = ["-i", captioned]
            filter_parts = []
            idx = 1
            voice_label = music_label = None
            if audio_track:
                inputs += ["-i", audio_track]
                filter_parts.append(f"[{idx}:a]volume=1.0[voice]")
                voice_label = "[voice]"
                idx += 1
            if has_music:
                inputs += ["-i", music_path]
                filter_parts.append(f"[{idx}:a]volume=0.25[music]")
                music_label = "[music]"
                idx += 1

            if voice_label and music_label:
                filter_parts.append(f"{voice_label}{music_label}amix=inputs=2:duration=first[aout]")
                map_audio = "[aout]"
            else:
                map_audio = voice_label or music_label

            _run([
                "ffmpeg", "-y", *inputs,
                "-filter_complex", ";".join(filter_parts),
                "-map", "0:v", "-map", map_audio,
                "-shortest", "-c:v", "copy", "-c:a", "aac",
                output_path,
            ])
        else:
            _run(["ffmpeg", "-y", "-i", captioned, "-c", "copy", output_path])

    return output_path


# ---------------------------------------------------------------------------
# Provider registry -- the pluggability point for future AI-generated video
# ---------------------------------------------------------------------------

def _ai_generated_not_implemented(*args, **kwargs):
    raise NotImplementedError(
        "The 'ai_generated' video provider is not wired in yet. When ready "
        "to add Runway/Pika/Kling/Sora/Veo: pick a vendor, get an API key, "
        "add it as a GitHub Secret, and implement a function with the same "
        "signature as generate_slideshow() (media_folder/prompt, "
        "output_path, caption_text, voiceover_text, video_cfg, openai_cfg) "
        "-- then register it here as VIDEO_PROVIDERS['ai_generated']. No "
        "changes needed in social_media_agent.py; it already looks up "
        "whichever provider config.json's video.provider names."
    )


VIDEO_PROVIDERS = {
    "slideshow": generate_slideshow,
    "ai_generated": _ai_generated_not_implemented,
}

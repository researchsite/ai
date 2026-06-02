"""Generate TTS narration and combine Part 1 + Part 2 into final walkthrough.mp4."""
import asyncio, subprocess, sys
from pathlib import Path

import edge_tts
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

VID_DIR = Path("assets/video_tmp")
OUT     = Path("assets")

# ── Narration ────────────────────────────────────────────────────────────────
# Written to match the pacing of the two recorded clips.
# Kept honest, no hype — describes what the user is actually seeing.

NARRATION = (
    "ThreatScope Analytics — a browser-based security dashboard for investigating "
    "malicious IP addresses, powered by the AbuseIPDB community database. "
    "No account needed to get started. "
    "The demo tab lets you type any IP address and preview what a full threat analysis looks like. "
    "After clicking Preview, the dashboard scrolls through the full result — "
    "a confidence score gauge, country of origin, ISP, usage type, "
    "and a 90-day report activity timeline. "
    "The Sample Data tab shows a real blacklist snapshot with 20 known malicious IPs "
    "sorted by abuse confidence score. "
    "When you're ready, connect your free AbuseIPDB API key. "
    "It's stored only in your browser session and sent directly to the API. "
    "With a live connection, query any IP in real time. "
    "Here's 1.1.1.1 — Cloudflare's public DNS server. "
    "The gauge shows a low confidence score, as expected for a well-known legitimate service. "
    "Country, ISP, and usage type are pulled directly from AbuseIPDB. "
    "Every field the API returns is shown — expand Raw Intelligence for the complete response "
    "including individual reporter comments. "
    "Built for SOC teams, threat analysts, and security engineers who need answers fast. "
    "Made with Claude Code. Powered by AbuseIPDB."
)

AUDIO_PATH = VID_DIR / "narration.mp3"
VOICE = "en-US-AriaNeural"   # natural, clear Microsoft neural voice


async def generate_tts():
    print("Generating TTS narration...")
    communicate = edge_tts.Communicate(NARRATION, VOICE, rate="+5%")
    await communicate.save(str(AUDIO_PATH))
    print(f"  Audio saved: {AUDIO_PATH}")


def combine():
    p1_path = VID_DIR / "part1.webm"
    p2_path = VID_DIR / "part2.webm"

    missing = [p for p in [p1_path, p2_path] if not p.exists()]
    if missing:
        print(f"ERROR: missing clips: {missing}")
        return

    print("Loading video clips...")
    clip1 = VideoFileClip(str(p1_path))
    clip2 = VideoFileClip(str(p2_path))

    print(f"  Part 1: {clip1.duration:.1f}s  Part 2: {clip2.duration:.1f}s")
    total = clip1.duration + clip2.duration
    print(f"  Total video: {total:.1f}s")

    print("Loading narration audio...")
    narration = AudioFileClip(str(AUDIO_PATH))
    print(f"  Narration: {narration.duration:.1f}s")

    # Combine video clips
    combined = concatenate_videoclips([clip1, clip2], method="compose")

    # Fit narration to video length (trim or pad with silence)
    if narration.duration > combined.duration:
        narration = narration.subclipped(0, combined.duration)

    combined = combined.with_audio(narration)

    out_path = OUT / "walkthrough.mp4"
    print(f"Writing {out_path}...")
    combined.write_videofile(
        str(out_path),
        codec="libx264",
        audio_codec="aac",
        fps=24,
        preset="medium",
        logger=None,
    )
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"\nDone: {out_path}  ({size_mb:.1f} MB,  {combined.duration:.1f}s)")

    clip1.close()
    clip2.close()
    combined.close()
    narration.close()


if __name__ == "__main__":
    asyncio.run(generate_tts())
    combine()

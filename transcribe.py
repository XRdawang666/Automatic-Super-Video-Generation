"""Transcribe a video with Deepgram Nova-3.

Extracts mono 16kHz audio via ffmpeg, uploads to Deepgram with diarization +
word-level timestamps + filler-word preservation, transforms the response
into Scribe-compatible JSON so downstream tools (pack_transcripts, etc.) work
unchanged.

Cached: if the output file already exists, the upload is skipped.

Usage:
    python helpers/transcribe.py <video_path>
    python helpers/transcribe.py <video_path> --edit-dir /custom/edit
    python helpers/transcribe.py <video_path> --language en
    python helpers/transcribe.py <video_path> --num-speakers 2
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests


DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


def load_api_key() -> str:
    """Load API key in order: DEEPGRAM_API_KEY env/ENV, then
    ELEVENLABS_API_KEY from ENV for backward compat, then .env files."""
    # 1. Environment variable
    for env_name in ("DEEPGRAM_API_KEY", "ELEVENLABS_API_KEY"):
        v = os.environ.get(env_name, "")
        if v:
            return v

    # 2. .env files (repo root, cwd)
    for candidate in [Path(__file__).resolve().parent.parent / ".env", Path(".env")]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k == "DEEPGRAM_API_KEY":
                    return v.strip().strip('"').strip("'")
                if k == "ELEVENLABS_API_KEY":
                    return v.strip().strip('"').strip("'")

    sys.exit(
        "DEEPGRAM_API_KEY not found.\n"
        "  Get one at https://console.deepgram.com (free $200 credit for new users).\n"
        "  Then add DEEPGRAM_API_KEY=<your-key> to ~/Developer/video-use/.env\n"
        "  Or set ELEVENLABS_API_KEY for backward compatibility."
    )


def extract_audio(video_path: Path, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def call_deepgram(
    audio_path: Path,
    api_key: str,
    language: str | None = None,
    num_speakers: int | None = None,
) -> dict:
    """Send audio to Deepgram Nova-3, return raw API response."""
    params: dict[str, str] = {
        "model": "nova-3",
        "diarize": "true",
        "smart_format": "true",
        "filler_words": "true",
        "utterances": "true",
    }
    if language:
        params["language"] = language
    if num_speakers:
        # Deepgram can accept a hint for diarization
        params["diarization_version"] = "2"

    with open(audio_path, "rb") as f:
        resp = requests.post(
            DEEPGRAM_URL,
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": "audio/wav",
            },
            params=params,
            data=f.read(),
            timeout=1800,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"Deepgram returned {resp.status_code}: {resp.text[:500]}")

    return resp.json()


def _transform_deepgram_to_scribe(degram_resp: dict, num_speakers: int | None = None) -> dict:
    """Transform Deepgram Nova-3 response to Scribe-compatible JSON.

    Deepgram response shape (with diarize + utterances):
      results.channels[0].alternatives[0].words = [
        {word, start, end, speaker, confidence, punctuated_word}, ...
      ]

    Scribe expected shape:
      {
        words: [
          {type: "word", text, start, end, speaker_id: "speaker_0"},
          {type: "spacing", start, end},  // gaps between words
          {type: "audio_event", text: "(laughter)"},  // optional
        ]
      }
    """
    try:
        alt = degram_resp["results"]["channels"][0]["alternatives"][0]
        words = alt.get("words", [])
    except (KeyError, IndexError):
        return {"words": []}

    if not words:
        return {"words": []}

    output_words: list[dict] = []
    prev_end: float | None = None

    for i, w in enumerate(words):
        start = w.get("start", 0.0)
        end = w.get("end", 0.0)
        raw_text = (w.get("punctuated_word") or w.get("word") or "").strip()
        speaker = w.get("speaker", 0)

        # Insert a spacing entry for the gap since the previous word
        if prev_end is not None and start > prev_end:
            output_words.append({
                "type": "spacing",
                "start": prev_end,
                "end": start,
            })

        # Detect filler words — Deepgram returns them as words, Scribe
        # treats them as normal words too, so we just pass through.
        word_type = "word"

        output_words.append({
            "type": word_type,
            "text": raw_text,
            "start": start,
            "end": end,
            "speaker_id": f"speaker_{speaker}",
        })

        prev_end = end

    return {"words": output_words}


def transcribe_one(
    video: Path,
    edit_dir: Path,
    api_key: str,
    language: str | None = None,
    num_speakers: int | None = None,
    verbose: bool = True,
) -> Path:
    """Transcribe a single video. Returns path to transcript JSON.

    Cached: returns existing path immediately if the transcript already exists.
    Output format is Scribe-compatible so downstream helpers work unchanged.
    """
    transcripts_dir = edit_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"

    if out_path.exists():
        if verbose:
            print(f"cached: {out_path.name}")
        return out_path

    if verbose:
        print(f"  extracting audio from {video.name}", flush=True)

    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / f"{video.stem}.wav"
        extract_audio(video, audio)
        size_mb = audio.stat().st_size / (1024 * 1024)
        if verbose:
            print(f"  uploading {video.stem}.wav ({size_mb:.1f} MB) to Deepgram", flush=True)
        raw = call_deepgram(audio, api_key, language, num_speakers)

    # Transform to Scribe-compatible format
    payload = _transform_deepgram_to_scribe(raw, num_speakers)

    out_path.write_text(json.dumps(payload, indent=2))
    dt = time.time() - t0

    if verbose:
        kb = out_path.stat().st_size / 1024
        print(f"  saved: {out_path.name} ({kb:.1f} KB) in {dt:.1f}s")
        word_count = sum(1 for w in payload.get("words", []) if w.get("type") == "word")
        if word_count:
            print(f"    words: {word_count}")

    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Transcribe a video with Deepgram Nova-3")
    ap.add_argument("video", type=Path, help="Path to video file")
    ap.add_argument(
        "--edit-dir",
        type=Path,
        default=None,
        help="Edit output directory (default: <video_parent>/edit)",
    )
    ap.add_argument(
        "--language",
        type=str,
        default=None,
        help="Optional ISO language code (e.g., 'en'). Omit to auto-detect.",
    )
    ap.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Optional number of speakers when known. Improves diarization accuracy.",
    )
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")

    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    api_key = load_api_key()

    transcribe_one(
        video=video,
        edit_dir=edit_dir,
        api_key=api_key,
        language=args.language,
        num_speakers=args.num_speakers,
    )


if __name__ == "__main__":
    main()

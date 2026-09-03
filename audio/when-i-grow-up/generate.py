#!/usr/bin/env python3
"""Voice `script.md` with ElevenLabs v3 as a two-speaker conversation.

Stage directions in the script, written as *(excited)*, *(whispers)*, *(gasps)*,
become ElevenLabs v3 audio tags ([excited], [whispers], [gasps]) at the same
spot in the line, so the emotion changes exactly where the script says it does.

Two modes:

  dialogue (default)  One call to the Text-to-Dialogue endpoint (eleven_v3).
                      The model hears both sides and times the back-and-forth.

  lines               One eleven_v3 Text-to-Speech call per line, stitched into a
                      WAV (and an MP3 if `lameenc` is installed). Use this if
                      Text-to-Dialogue is not enabled on the account.

Usage:
  export ELEVENLABS_API_KEY=sk_...          # or: --env /path/to/.env
  python3 generate.py                       # -> out/when-i-grow-up.mp3
  python3 generate.py --mode lines
  python3 generate.py --kid <voice_id> --adult <voice_id>
  python3 generate.py --dry-run             # print the tagged lines and exit

Default voices (both free in the ElevenLabs voice library; add them to your
account from https://elevenlabs.io/app/voice-library before generating):
  KID    Teddy Twinkle - Cute Cartoon        XjGYkUkzth8BPs29fmcV
  ADULT  Boyd - Versatile, Fatherly, Natural gfRt6Z3Z8aTbpLfexQ7N

No third-party dependencies. `pip install lameenc` is optional (MP3 in lines mode).
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_v3"

DEFAULT_KID = "XjGYkUkzth8BPs29fmcV"     # Teddy Twinkle - Cute Cartoon
DEFAULT_ADULT = "gfRt6Z3Z8aTbpLfexQ7N"   # Boyd - Versatile, Fatherly and Natural

SAMPLE_RATE = 44100
GAP_SECONDS = 0.35   # silence between lines in `lines` mode

# Script direction -> v3 tag, where the wording differs. Anything else passes
# through as-is: *(excited)* -> [excited].
TAG_ALIASES = {
    "whispering": "whispers",
    "shouting": "shouts",
    "laughing": "laughs",
    "giggling": "giggles",
    "matter-of-fact": "deadpan",
    "hesitant": "hesitant",
}


def parse_script(path: Path):
    """Return [(speaker, text)] with *(direction)* converted to [tag] in place."""
    lines = []
    pat = re.compile(r"^\*\*(ADULT|KID):\*\*\s*(.*)$")
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = pat.match(raw.strip())
        if not m:
            continue
        speaker, text = m.group(1), m.group(2)
        text = re.sub(r"\*\((.*?)\)\*", lambda mm: "[" + TAG_ALIASES.get(mm.group(1).strip().lower(), mm.group(1).strip().lower()) + "]", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        lines.append((speaker, text))
    return lines


def load_key(env_path):
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("XI_API_KEY")
    if not key and env_path and Path(env_path).exists():
        for line in Path(env_path).read_text().splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY or pass --env (https://elevenlabs.io/app/settings/api-keys).")
    return key


def request(path, body, key, query=""):
    req = urllib.request.Request(
        f"{API}{path}{query}",
        data=json.dumps(body).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(3 * (attempt + 1))
                continue
            return e.code, detail.encode(), {}
    raise RuntimeError("unreachable")


def gen_dialogue(lines, voices, key, out_dir):
    inputs = [{"text": text, "voice_id": voices[speaker]} for speaker, text in lines]
    print(f"Text-to-Dialogue: {len(inputs)} lines, {sum(len(t) for _, t in lines)} chars, model {MODEL}")
    status, data, _ = request(
        "/text-to-dialogue",
        {"inputs": inputs, "model_id": MODEL, "settings": {"stability": 0.5, "use_speaker_boost": True}},
        key,
        query="?output_format=mp3_44100_128",
    )
    if status != 200:
        return None, data.decode(errors="replace")
    out = out_dir / "when-i-grow-up.mp3"
    out.write_bytes(data)
    return out, None


def gen_lines(lines, voices, key, out_dir):
    pcm = bytearray()
    gap = b"\x00\x00" * int(SAMPLE_RATE * GAP_SECONDS)
    seg_dir = out_dir / "segments"
    seg_dir.mkdir(exist_ok=True)
    for i, (speaker, text) in enumerate(lines, 1):
        body = {
            "text": text,
            "model_id": MODEL,
            # v3 accepts stability 0.0 (creative) / 0.5 (natural) / 1.0 (robust)
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "use_speaker_boost": True},
        }
        print(f"[{i:02d}/{len(lines)}] {speaker}: {text[:70]}")
        status, chunk, _ = request(f"/text-to-speech/{voices[speaker]}", body, key, query=f"?output_format=pcm_{SAMPLE_RATE}")
        if status != 200:
            sys.exit(f"ElevenLabs {status} on line {i}: {chunk.decode(errors='replace')}")
        (seg_dir / f"{i:02d}-{speaker.lower()}.pcm").write_bytes(chunk)
        pcm += chunk + gap

    out_wav = out_dir / "when-i-grow-up.wav"
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(pcm))
    try:
        import lameenc  # optional
    except ImportError:
        return out_wav
    enc = lameenc.Encoder()
    enc.set_bit_rate(128)
    enc.set_in_sample_rate(SAMPLE_RATE)
    enc.set_channels(1)
    enc.set_quality(2)
    out_mp3 = out_dir / "when-i-grow-up.mp3"
    out_mp3.write_bytes(enc.encode(bytes(pcm)) + enc.flush())
    return out_mp3


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["dialogue", "lines"], default="dialogue")
    ap.add_argument("--kid", default=os.environ.get("KID_VOICE_ID", DEFAULT_KID))
    ap.add_argument("--adult", default=os.environ.get("ADULT_VOICE_ID", DEFAULT_ADULT))
    ap.add_argument("--script", default=str(HERE / "script.md"))
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--env", default=None, help="path to a .env file containing ELEVENLABS_API_KEY=...")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = parse_script(Path(args.script))
    if not lines:
        sys.exit("No ADULT:/KID: lines found in script.")
    if args.dry_run:
        for s, t in lines:
            print(f"{s:5s} {t}")
        print(f"\n{len(lines)} lines, {sum(len(t) for _, t in lines)} characters")
        return

    key = load_key(args.env)
    voices = {"KID": args.kid, "ADULT": args.adult}
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "dialogue":
        out, err = gen_dialogue(lines, voices, key, out_dir)
        if err:
            print(f"Text-to-Dialogue failed: {err}\nFalling back to per-line eleven_v3 TTS.")
            out = gen_lines(lines, voices, key, out_dir)
    else:
        out = gen_lines(lines, voices, key, out_dir)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()

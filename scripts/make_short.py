import argparse
import asyncio
import glob
import math
import os
import shutil
import subprocess
import sys

import edge_tts

FPS = 25
W, H = 1080, 1920


def fmt_ts(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:01d}:{m:02d}:{s:05.2f}"


async def tts_with_words(text, voice, audio_out, rate="+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    words = []
    sentences = []
    with open(audio_out, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000
                dur = chunk["duration"] / 10_000_000
                words.append((start, start + dur, chunk["text"]))
            elif chunk["type"] == "SentenceBoundary":
                start = chunk["offset"] / 10_000_000
                dur = chunk["duration"] / 10_000_000
                sentences.append((start, start + dur, chunk["text"]))

    if words:
        return words

    # Korean voices only emit SentenceBoundary, not WordBoundary.
    # Approximate per-word timing by splitting each sentence proportionally by character count.
    pseudo = []
    for s_start, s_end, s_text in sentences:
        tokens = [t for t in s_text.split(" ") if t]
        total_chars = sum(len(t) for t in tokens) or 1
        span = s_end - s_start
        cursor = s_start
        for t in tokens:
            w_dur = span * (len(t) / total_chars)
            pseudo.append((cursor, cursor + w_dur, t))
            cursor += w_dur
    return pseudo


def group_words(words, max_chars=14, max_dur=2.2):
    """Groups raw (start, end, word) tuples into short phrase groups, keeping per-word timing."""
    groups = []
    cur = []
    cur_start = None
    cur_chars = 0
    for start, end, word in words:
        w = word.strip()
        if not w:
            continue
        if cur_start is None:
            cur_start = start
        if cur and (cur_chars + len(w) + 1 > max_chars or (end - cur_start) > max_dur):
            groups.append(cur)
            cur = []
            cur_start = start
            cur_chars = 0
        cur.append((start, end, w))
        cur_chars += len(w) + 1
    if cur:
        groups.append(cur)
    return groups


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Malgun Gothic,72,&H00FFFFFF,&H0040C7FF,&H00000000,&H60000000,-1,0,0,0,100,100,0,0,3,18,0,2,80,80,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_karaoke_text(word_group):
    """ASS karaoke: each word flips from Secondary(gold) to Primary(white) as it's spoken, and stays highlighted."""
    parts = []
    for i, (s, e, w) in enumerate(word_group):
        nxt_start = word_group[i + 1][0] if i + 1 < len(word_group) else e
        dur_cs = max(round((nxt_start - s) * 100), 1)
        parts.append(f"{{\\k{dur_cs}}}{w}")
    return " ".join(parts)


def write_ass(words, ass_path):
    groups = group_words(words)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER.format(w=W, h=H))
        for group in groups:
            if not group:
                continue
            start, end = group[0][0], group[-1][1]
            text = build_karaoke_text(group)
            f.write(f"Dialogue: 0,{fmt_ts(start)},{fmt_ts(end)},Caption,,0,0,0,,{text}\n")
    return len(groups)


def run(cmd):
    subprocess.run(cmd, check=True)


def build_image_clip(image_path, out_path, duration):
    """완만한 줌인만 사용(1.0->1.08). 컷 지점은 build_broll의 크로스페이드가 부드럽게 이어준다."""
    frames = max(int(duration * FPS), 1)
    zoom_expr = "min(zoom+0.0006,1.08)"
    vf = (
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop={W*2}:{H*2},"
        f"zoompan=z='{zoom_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}"
    )
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-vf", vf, "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        out_path,
    ]
    run(cmd)


def build_broll(images_dir, total_duration, work_dir, img_dur=4.0, xfade_dur=0.5):
    images = sorted(
        glob.glob(os.path.join(images_dir, "**", "*.png"), recursive=True)
        + glob.glob(os.path.join(images_dir, "**", "*.jpg"), recursive=True)
    )
    if not images:
        raise SystemExit(f"no images found in {images_dir}")

    n_clips = max(math.ceil(total_duration / img_dur), 1)
    clip_paths, clip_durs = [], []
    remaining = total_duration
    for i in range(n_clips):
        dur = min(img_dur, remaining)
        if dur <= 0:
            break
        is_last = (i == n_clips - 1) or (remaining - dur <= 0)
        raw_dur = dur + (0 if is_last else xfade_dur)
        img = images[i % len(images)]
        out_path = os.path.join(work_dir, f"clip_{i:03d}.mp4")
        build_image_clip(img, out_path, raw_dur)
        clip_paths.append(out_path)
        clip_durs.append(raw_dur)
        remaining -= dur

    broll_path = os.path.join(work_dir, "broll.mp4")
    if len(clip_paths) == 1:
        shutil.copy2(clip_paths[0], broll_path)
        return broll_path

    filter_parts = []
    offset = clip_durs[0] - xfade_dur
    prev_label = "0:v"
    for i in range(1, len(clip_paths)):
        out_label = f"v{i}" if i < len(clip_paths) - 1 else "vout"
        filter_parts.append(
            f"[{prev_label}][{i}:v]xfade=transition=fade:duration={xfade_dur}:offset={offset:.3f}[{out_label}]"
        )
        prev_label = out_label
        if i < len(clip_paths) - 1:
            offset += clip_durs[i] - xfade_dur

    cmd = ["ffmpeg", "-y"]
    for p in clip_paths:
        cmd += ["-i", p]
    cmd += [
        "-filter_complex", ";".join(filter_parts),
        "-map", "[vout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        broll_path,
    ]
    run(cmd)
    return broll_path


def get_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--voice", default="ko-KR-InJoonNeural")
    ap.add_argument("--rate", default="+30%")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=None)
    ap.add_argument("--bgm", default=None)
    ap.add_argument("--img-dur", type=float, default=4.0)
    args = ap.parse_args()

    with open(args.script, "r", encoding="utf-8") as f:
        text = f.read().strip()

    work_dir = args.work or os.path.join(os.path.dirname(args.out), "_work")
    os.makedirs(work_dir, exist_ok=True)

    audio_path = os.path.join(work_dir, "voice.mp3")
    print("1/4 generating voice (edge-tts)...")
    words = asyncio.run(tts_with_words(text, args.voice, audio_path, args.rate))

    ass_path = os.path.join(work_dir, "captions.ass")
    n = write_ass(words, ass_path)
    print(f"   captions: {n} lines")

    total_duration = get_duration(audio_path)
    print(f"2/4 voice duration: {total_duration:.1f}s")

    print("3/4 building broll from images...")
    broll_path = build_broll(args.images, total_duration, work_dir, args.img_dur)

    print("4/4 muxing final video...")
    ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")

    if args.bgm and os.path.exists(args.bgm):
        cmd = [
            "ffmpeg", "-y",
            "-i", broll_path, "-i", audio_path, "-i", args.bgm,
            "-filter_complex",
            f"[1:a]volume=1.0[voice];[2:a]volume=0.15[bgm];[voice][bgm]amix=inputs=2:duration=first[aout];"
            f"[0:v]ass='{ass_escaped}'[vout]",
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            args.out,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", broll_path, "-i", audio_path,
            "-vf", f"ass='{ass_escaped}'",
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            args.out,
        ]
    run(cmd)
    print(f"done: {args.out}")


if __name__ == "__main__":
    main()

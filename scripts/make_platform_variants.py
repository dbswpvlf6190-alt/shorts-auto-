import argparse
import asyncio
import os
import subprocess
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_graphic as gfx  # noqa: E402
import make_short as base  # noqa: E402  (tts/caption/get_duration 재사용)

W, H = 1080, 1920
FPS = 25


def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"failed: {' '.join(cmd)}\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}")
    return result.stdout


def get_duration(path):
    return base.get_duration(path)


# ---------- 오프닝 훅 (프리미엄 배경 + 임팩트 사운드) ----------

def make_hook_frame(text, path, kicker_text=None, danger=False):
    bg_top = (30, 10, 10) if danger else gfx.BG_TOP
    bg_bottom = (10, 3, 3) if danger else gfx.BG_BOTTOM
    accent = (255, 70, 70) if danger else gfx.ACCENT
    img = gfx.vertical_gradient(W, H, bg_top, bg_bottom)
    img = gfx.add_glow(img, (W // 2, H // 2), 520, accent, opacity=90)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, H], fill=accent)
    if kicker_text:
        gfx.kicker(d, kicker_text)
    size = 118
    f = gfx.font(size)
    while size > 50:
        if d.textlength(text, font=f) <= 920:
            break
        size -= 8
        f = gfx.font(size)
    w = d.textlength(text, font=f)
    d.text((W / 2 - w / 2, H / 2 - size / 2), text, font=f, fill=(255, 255, 255) if danger else gfx.WHITE)
    gfx.watermark(d)
    img.save(path)


def zoompunch_clip(image_path, out_path, duration, work_dir, zoom_from=1.15, zoom_to=1.0, punch_time=0.18):
    frames = max(int(duration * FPS), 1)
    punch_frames = max(int(punch_time * FPS), 1)
    zexpr = f"if(lte(on,{punch_frames}),{zoom_from}-({zoom_from}-{zoom_to})*on/{punch_frames},{zoom_to})"
    vf = (
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
        f"zoompan=z='{zexpr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", os.path.basename(image_path),
        "-vf", vf, "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        os.path.basename(out_path),
    ], cwd=work_dir)


def build_hook_audio(work_dir, total_dur, punch_time_ms, voice_audio_path):
    """무음 대신 훅 문구를 읽는 TTS 음성 + 펀치 줌 타이밍에 맞춘 임팩트 사운드(노이즈+저음 thump)를 믹스."""
    noise = os.path.join(work_dir, "impact_noise.wav")
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=color=white:duration=0.05:amplitude=1",
        "-af", "highpass=f=1500,afade=t=out:st=0:d=0.05", "-ar", "44100", "-ac", "2", noise,
    ])
    thump = os.path.join(work_dir, "impact_thump.wav")
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=85:duration=0.35",
        "-af", "afade=t=out:st=0:d=0.35,volume=6dB", "-ar", "44100", "-ac", "2", thump,
    ])
    impact_mix = os.path.join(work_dir, "impact_mix.wav")
    run([
        "ffmpeg", "-y", "-i", noise, "-i", thump,
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest:normalize=0[a]",
        "-map", "[a]", impact_mix,
    ])
    final = os.path.join(work_dir, "hook_audio_final.aac")
    run([
        "ffmpeg", "-y", "-i", voice_audio_path, "-i", impact_mix,
        "-filter_complex",
        f"[1:a]adelay={punch_time_ms}|{punch_time_ms}[imp];"
        f"[0:a]volume=1.2[voice];"
        f"[voice][imp]amix=inputs=2:duration=first:dropout_transition=0[a]",
        "-t", str(total_dur), "-map", "[a]", "-c:a", "aac", final,
    ])
    return final


def synth_voice(text, voice, rate, work_dir, audio_out):
    """voice가 'cloned'이면 복제 목소리, 아니면 기존 edge-tts."""
    if voice == "cloned":
        return base.tts_cloned_voice(text, work_dir, audio_out)
    return asyncio.run(base.tts_with_words(text, voice, audio_out, rate))


def voice_audio_name(name_stem, voice):
    return f"{name_stem}.wav" if voice == "cloned" else f"{name_stem}.mp3"


def build_yt_hook(word_lines, work_dir, out_name, voice, rate):
    """훅 문구를 TTS로 실제로 읽고, 각 구절의 팝인 타이밍을 발화 타이밍에 맞춘다."""
    full_text = " ".join(word_lines)
    voice_audio = os.path.join(work_dir, voice_audio_name("yt_hook_voice", voice))
    words = synth_voice(full_text, voice, rate, work_dir, voice_audio)
    total_duration = base.get_duration(voice_audio)

    if len(words) == len(word_lines):
        timings = [(s, e) for s, e, _ in words]
    else:
        n = len(word_lines)
        per = total_duration / n
        timings = [(i * per, (i + 1) * per) for i in range(n)]

    clip_names = []
    for i, w in enumerate(word_lines):
        img_name = f"yt_hook_{i}.png"
        make_hook_frame(w, os.path.join(work_dir, img_name), kicker_text="오늘의 정책" if i == 0 else None)
        clip_name = f"yt_hook_{i}.mp4"
        start, end = timings[i]
        dur = max(end - start, 0.3)
        zoompunch_clip(img_name, clip_name, dur, work_dir, punch_time=min(0.18, dur / 3))
        clip_names.append(clip_name)

    concat_txt = "yt_hook_concat.txt"
    with open(os.path.join(work_dir, concat_txt), "w", encoding="utf-8") as f:
        for c in clip_names:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", out_name], cwd=work_dir)
    return voice_audio, total_duration


def build_tiktok_hook(text, work_dir, out_name, voice, rate):
    img_name = "tt_hook.png"
    make_hook_frame(text, os.path.join(work_dir, img_name), kicker_text="속보", danger=True)
    voice_audio = os.path.join(work_dir, voice_audio_name("tt_hook_voice", voice))
    synth_voice(text, voice, rate, work_dir, voice_audio)
    duration = base.get_duration(voice_audio)
    zoompunch_clip(img_name, out_name, duration, work_dir, zoom_from=1.3, zoom_to=1.0, punch_time=0.22)
    return voice_audio, duration


def prepend_hook(hook_name, base_path, out_path, work_dir, voice_audio, punch_time=0.18):
    hook_path = os.path.join(work_dir, hook_name)
    hook_dur = get_duration(hook_path)

    hook_audio = build_hook_audio(work_dir, hook_dur, int(punch_time * 1000), voice_audio)

    hook_with_audio = "hook_with_audio.mp4"
    run([
        "ffmpeg", "-y", "-i", hook_name, "-i", os.path.basename(hook_audio),
        "-c:v", "copy", "-c:a", "aac", "-shortest", hook_with_audio,
    ], cwd=work_dir)

    base_name = "base_video.mp4"
    base_path_abs = os.path.abspath(base_path)
    with open(base_path_abs, "rb") as src, open(os.path.join(work_dir, base_name), "wb") as dst:
        dst.write(src.read())

    run([
        "ffmpeg", "-y", "-i", hook_with_audio, "-i", base_name,
        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "192k",
        os.path.abspath(out_path),
    ], cwd=work_dir)


# ---------- 엔딩 CTA (다음편 예고형, 2026-08-22 개편) ----------
# 신사임당(주언규) 인터뷰 근거: 구독 전환의 핵심은 "다음 회차에 대한 구체적 기대감".
# 뭉뚱그린 "팔로우하세요" 대신 다음 소재를 구체적으로 예고해서 재방문 동기를 준다.
# 동시에 문장 길이를 줄여 완료율(50%+ 필요)을 지키는 것도 목표.

DEFAULT_NEXT_TEASER = "내일도 놓치면 손해인 정책 하나 풀어드립니다"
DEFAULT_OUTRO_MAIN = "댓글로 알려주세요"


def build_outro(work_dir, out_path, voice, rate, next_teaser=DEFAULT_NEXT_TEASER,
                 main_text=DEFAULT_OUTRO_MAIN):
    os.makedirs(work_dir, exist_ok=True)
    outro_text = f"여러분은 해당되시나요? 댓글로 알려주세요. {next_teaser}"
    sub_text = next_teaser
    audio_path = os.path.join(work_dir, voice_audio_name("outro_voice", voice))
    words = synth_voice(outro_text, voice, rate, work_dir, audio_path)

    ass_path = os.path.join(work_dir, "outro_captions.ass")
    base.write_ass(words, ass_path)
    duration = base.get_duration(audio_path)

    cta_img = os.path.join(work_dir, "cta_card.png")
    gfx.cta_card(main_text, sub_text, kicker_text="구독 안내", out=cta_img)

    bg_clip = os.path.join(work_dir, "outro_bg.mp4")
    base.build_image_clip(cta_img, bg_clip, duration)

    ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
    run([
        "ffmpeg", "-y",
        "-i", bg_clip, "-i", audio_path,
        "-vf", f"ass='{ass_escaped}'",
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        out_path,
    ])
    return out_path


def append_outro(base_video, outro_video, out_path, work_dir):
    concat_txt = os.path.join(work_dir, "outro_concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write(f"file '{os.path.abspath(base_video)}'\n")
        f.write(f"file '{os.path.abspath(outro_video)}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", out_path])


# ---------- 우측 상단 고정 로고 오버레이 ----------

def apply_logo_overlay(video_path, logo_path, out_path):
    run([
        "ffmpeg", "-y", "-i", video_path, "-i", logo_path,
        "-filter_complex", "[0:v][1:v]overlay=W-w-36:52",
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "copy",
        out_path,
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-video", required=True, help="make_short.py로 만든 본편 mp4")
    ap.add_argument("--yt-hook-lines", required=True, help="세미콜론(;)으로 구분된 유튜브 훅 줄들")
    ap.add_argument("--tiktok-hook-text", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--work", default=None)
    ap.add_argument("--voice", default="cloned")
    ap.add_argument("--rate", default="+30%")
    ap.add_argument("--next-teaser", default=DEFAULT_NEXT_TEASER, help="엔딩 CTA에 넣을 다음편 예고 문구")
    args = ap.parse_args()

    work_dir = args.work or os.path.join(args.out_dir, "_hook_work")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(args.out_dir, exist_ok=True)

    print("0/3 엔딩 CTA(팔로우/댓글 유도) 생성 중...")
    outro_video = os.path.join(args.out_dir, "outro.mp4")
    build_outro(work_dir, outro_video, args.voice, args.rate, next_teaser=args.next_teaser)
    base_with_outro = os.path.join(args.out_dir, "base_with_outro.mp4")
    append_outro(args.base_video, outro_video, base_with_outro, work_dir)

    logo_path = os.path.join(work_dir, "logo.png")
    gfx.make_logo_badge(logo_path)

    yt_lines = [s.strip() for s in args.yt_hook_lines.split(";") if s.strip()]

    print("1/3 유튜브 훅(음성 내레이션 동기화) 생성 중...")
    yt_voice, _ = build_yt_hook(yt_lines, work_dir, "yt_hook.mp4", args.voice, args.rate)
    yt_raw = os.path.join(args.out_dir, "youtube_raw.mp4")
    prepend_hook("yt_hook.mp4", base_with_outro, yt_raw, work_dir, voice_audio=yt_voice, punch_time=0.18)
    yt_out = os.path.join(args.out_dir, "youtube.mp4")
    apply_logo_overlay(yt_raw, logo_path, yt_out)
    print(f"   -> {yt_out}")

    print("2/3 틱톡 훅(음성 내레이션 동기화) 생성 중...")
    tt_voice, _ = build_tiktok_hook(args.tiktok_hook_text, work_dir, "tt_hook.mp4", args.voice, args.rate)
    tt_raw = os.path.join(args.out_dir, "tiktok_raw.mp4")
    prepend_hook("tt_hook.mp4", base_with_outro, tt_raw, work_dir, voice_audio=tt_voice, punch_time=0.22)
    tt_out = os.path.join(args.out_dir, "tiktok.mp4")
    apply_logo_overlay(tt_raw, logo_path, tt_out)
    print(f"3/3 -> {tt_out}")


if __name__ == "__main__":
    main()

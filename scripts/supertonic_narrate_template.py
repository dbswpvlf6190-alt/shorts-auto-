"""daily.factlab 파이프라인용 나레이션 생성 스크립트 (2026-08-30).

make_short.py가 서브프로세스로 호출한다(이 venv에만 의존성이 있어서 메인 파이프라인 환경을 안 건드림).
edge-tts의 WordBoundary 이벤트가 없는 대신, chunk_text로 문장 단위로 나눠 각 문장을 개별 생성하고
그 문장 내에서는 글자 수 비례로 단어 타이밍을 근사한다 — make_short.py의 기존 한국어 fallback과 같은 방식.
"""
import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helper import load_text_to_speech, load_voice_style, chunk_text  # noqa: E402

GAP_SECONDS = 0.15


def synthesize(text, style_path, lang="ko", total_step=6, speed=1.05):
    tts = load_text_to_speech(os.path.join(os.path.dirname(__file__), "supertonic3", "onnx"))
    voice_style = load_voice_style([style_path])
    max_len = 120 if lang in ("ko", "ja") else 300
    chunks = chunk_text(text, max_len=max_len)

    sr = tts.sample_rate
    audio_parts = []
    words = []
    cursor = 0.0
    gap = np.zeros(int(GAP_SECONDS * sr), dtype=np.float32)

    for i, chunk in enumerate(chunks):
        wav, dur = tts(chunk, lang, voice_style, total_step, speed)
        chunk_dur = float(dur[0])
        n_samples = min(int(sr * chunk_dur), wav.shape[1])
        clip = wav[0, :n_samples]
        audio_parts.append(clip)

        tokens = [t for t in chunk.split(" ") if t.strip()]
        total_chars = sum(len(t) for t in tokens) or 1
        local_cursor = cursor
        for t in tokens:
            w_dur = chunk_dur * (len(t) / total_chars)
            words.append((local_cursor, local_cursor + w_dur, t))
            local_cursor += w_dur
        cursor += chunk_dur

        if i < len(chunks) - 1:
            audio_parts.append(gap)
            cursor += GAP_SECONDS

    final_wav = np.concatenate(audio_parts)
    return final_wav, sr, words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--style", required=True)
    ap.add_argument("--lang", default="ko")
    ap.add_argument("--total-step", type=int, default=6)
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--out-audio", required=True)
    ap.add_argument("--out-timing", required=True)
    args = ap.parse_args()

    with open(args.text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    wav, sr, words = synthesize(text, args.style, args.lang, args.total_step, args.speed)
    sf.write(args.out_audio, wav, sr)
    with open(args.out_timing, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)
    print(f"done: {args.out_audio} ({len(wav) / sr:.1f}s), {len(words)} words -> {args.out_timing}")


if __name__ == "__main__":
    main()

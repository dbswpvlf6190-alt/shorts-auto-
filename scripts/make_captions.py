import sys
from faster_whisper import WhisperModel


def fmt_ts(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:01d}:{m:02d}:{s:05.2f}"


def group_words(words, max_chars=14, max_dur=2.2):
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
        if cur and (cur_chars + len(w) > max_chars or (end - cur_start) > max_dur):
            groups.append((cur_start, cur[-1][1], "".join(c[2] for c in cur).strip()))
            cur = []
            cur_start = start
            cur_chars = 0
        cur.append((start, end, word))
        cur_chars += len(w)
    if cur:
        groups.append((cur_start, cur[-1][1], "".join(c[2] for c in cur).strip()))
    return groups


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Malgun Gothic,78,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main(audio_path, ass_path, model_size="base"):
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, language="ko", word_timestamps=True)

    words = []
    for seg in segments:
        for w in seg.words:
            words.append((w.start, w.end, w.word))

    groups = group_words(words)

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for start, end, text in groups:
            text = text.replace("\n", " ").strip()
            if not text:
                continue
            f.write(f"Dialogue: 0,{fmt_ts(start)},{fmt_ts(end)},Caption,,0,0,0,,{text}\n")

    print(f"captions written: {ass_path} ({len(groups)} lines)")


if __name__ == "__main__":
    audio_path = sys.argv[1]
    ass_path = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "base"
    main(audio_path, ass_path, model_size)

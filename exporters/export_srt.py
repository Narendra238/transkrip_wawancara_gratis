def _timestamp(seconds):
    milliseconds = int(round(max(0, seconds) * 1000))
    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    secs = milliseconds // 1000
    milliseconds %= 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def build_srt(segments):
    blocks = []
    for i, seg in enumerate(segments, start=1):
        blocks.append(
            f"{i}\n{_timestamp(seg['start'])} --> {_timestamp(seg['end'])}\n{seg['text'].strip()}\n"
        )
    return "\n".join(blocks)

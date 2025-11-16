from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class Block:
    speaker_id: str
    start_sec: float
    end_sec: float
    text: str

def _sec_to_srt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def _normalize_blocks(blocks: Iterable[Block]) -> List[Block]:
    return sorted(list(blocks), key=lambda b: (b.start_sec, b.end_sec))

def blocks_from_speakerblocks(objs: Iterable[object]) -> List[Block]:
    out: List[Block] = []
    for o in objs:
        sid = getattr(o, "speaker_id", getattr(o, "speaker", "spk_0"))
        txt = getattr(o, "text", getattr(o, "transcript", ""))
        if hasattr(o, "start") and hasattr(o, "end"):
            st = float(getattr(o, "start"))
            en = float(getattr(o, "end"))
        elif hasattr(o, "start_time") and hasattr(o, "end_time"):
            st = float(getattr(o, "start_time")) / 1000.0
            en = float(getattr(o, "end_time")) / 1000.0
        else:
            st = 0.0
            en = 0.0
        out.append(Block(speaker_id=str(sid), start_sec=st, end_sec=en, text=str(txt)))
    return _normalize_blocks(out)

def export_audacity_labels(blocks: Iterable[Block], outdir: Path, per_speaker: bool = True) -> List[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    blocks = _normalize_blocks(blocks)
    paths: List[Path] = []
    if per_speaker:
        by_spk: dict[str, List[Block]] = {}
        for b in blocks:
            by_spk.setdefault(b.speaker_id, []).append(b)
        for spk, arr in by_spk.items():
            p = outdir / f"labels_{spk}.txt"
            with p.open("w", encoding="utf-8") as f:
                for b in arr:
                    f.write(f"{b.start_sec:.3f}\t{b.end_sec:.3f}\t{b.text}\n")
            paths.append(p)
    else:
        p = outdir / "labels_all.txt"
        with p.open("w", encoding="utf-8") as f:
            for b in blocks:
                lab = f"[{b.speaker_id}] {b.text}".strip()
                f.write(f"{b.start_sec:.3f}\t{b.end_sec:.3f}\t{lab}\n")
        paths.append(p)
    return paths

def export_srt(blocks: Iterable[Block], outpath: Path) -> Path:
    blocks = _normalize_blocks(blocks)
    with outpath.open("w", encoding="utf-8") as f:
        for i, b in enumerate(blocks, start=1):
            f.write(f"{i}\n")
            f.write(f"{_sec_to_srt_time(b.start_sec)} --> {_sec_to_srt_time(b.end_sec)}\n")
            line = f"{b.speaker_id}: {b.text}".strip()
            f.write(line + "\n\n")
    return outpath

def import_audacity_labels(label_path: Path, speaker_id: Optional[str] = None) -> List[Block]:
    blocks: List[Block] = []
    with label_path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                st = float(parts[0])
                en = float(parts[1])
                lab = parts[2]
                sid = speaker_id if speaker_id is not None else "spk_0"
                if label_path.stem.startswith("labels_") and speaker_id is None:
                    sid = label_path.stem.split("labels_")[-1]
                blocks.append(Block(speaker_id=sid, start_sec=st, end_sec=en, text=lab))
    return _normalize_blocks(blocks)

def merge_back(original: List[Block], edited: List[Block]) -> List[Block]:
    out: List[Block] = []
    orig_by_spk: dict[str, List[Block]] = {}
    edit_by_spk: dict[str, List[Block]] = {}
    for b in original:
        orig_by_spk.setdefault(b.speaker_id, []).append(b)
    for b in edited:
        edit_by_spk.setdefault(b.speaker_id, []).append(b)
    for spk, olist in orig_by_spk.items():
        elist = edit_by_spk.get(spk, [])
        n = min(len(olist), len(elist))
        for i in range(n):
            o = olist[i]
            e = elist[i]
            out.append(Block(speaker_id=spk, start_sec=e.start_sec, end_sec=e.end_sec, text=o.text))
    return _normalize_blocks(out)
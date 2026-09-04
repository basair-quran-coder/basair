from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path


SURAH_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
    "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
    "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
    "المسد", "الإخلاص", "الفلق", "الناس",
]

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalize_arabic(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}))
    return re.sub(r"\s+", " ", text).strip()


NAME_TO_NUMBER = {normalize_arabic(name): i + 1 for i, name in enumerate(SURAH_NAMES)}


def split_table_row(line: str) -> list[str]:
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in line.strip().strip("|"):
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def clean_text(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = text.replace("**", "").replace("__", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_sources(value: str) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    occupied: list[tuple[int, int]] = []
    for match in re.finditer(r"\[([^\]]+)\]\((https?://[^)]+)\)", value):
        sources.append({"label": clean_text(match.group(1)), "url": match.group(2).strip()})
        occupied.append(match.span())
    chars = list(value)
    for start, end in occupied:
        chars[start:end] = " " * (end - start)
    remainder = "".join(chars)
    for part in re.split(r"\s*[؛;]\s*", remainder):
        part = clean_text(part).strip(" .،؛")
        if part:
            sources.append({"label": part, "url": ""})
    return sources or [{"label": "المصدر مثبت في ملف السورة", "url": ""}]


def extract_verses(label: str, surah_name: str) -> list[int]:
    label = label.translate(ARABIC_DIGITS)
    normalized_label = normalize_arabic(label)
    normalized_name = normalize_arabic(surah_name)
    segment = label
    pos = normalized_label.find(normalized_name)
    if pos >= 0:
        # The normalization used above preserves practical character offsets for these labels.
        colon = label.find(":", pos)
        if colon >= 0:
            segment = label[colon + 1 :]
    segment = re.split(r"[،,؛;](?=\s*[\u0600-\u06ff])", segment, maxsplit=1)[0]
    verses: set[int] = set()
    for a, b in re.findall(r"(\d+)\s*[-–—]\s*(\d+)", segment):
        start, end = int(a), int(b)
        if 0 < start <= end <= 300 and end - start <= 300:
            verses.update(range(start, end + 1))
    without_ranges = re.sub(r"\d+\s*[-–—]\s*\d+", " ", segment)
    verses.update(int(n) for n in re.findall(r"\d+", without_ranges) if 0 < int(n) <= 300)
    return sorted(verses)


def surah_name_from_header(text: str, path: Path) -> str:
    first = text.splitlines()[0] if text.splitlines() else ""
    match = re.search(r"سورة\s+(.+?)(?:\s*[—:|]|$)", first)
    if not match:
        raise ValueError(f"Could not read surah name: {path.name}")
    return clean_text(match.group(1))


def parse_file(path: Path) -> tuple[int, str, list[dict]]:
    text = path.read_text(encoding="utf-8")
    surah_name = surah_name_from_header(text, path)
    surah_number = NAME_TO_NUMBER.get(normalize_arabic(surah_name))
    if not surah_number:
        raise ValueError(f"Unknown surah {surah_name!r} in {path.name}")
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.startswith("|") and "السؤال" in line and "الجواب" in line), None)
    if header_index is None:
        if re.search(r"(?:المرشحات|المرشحات المثبتة).*?\*\*\s*0", text, flags=re.S):
            return surah_number, surah_name, []
        raise ValueError(f"No question table in {path.name}")
    headers = split_table_row(lines[header_index])
    verse_col = next(i for i, h in enumerate(headers) if "الآية" in h)
    question_col = next(i for i, h in enumerate(headers) if "السؤال" in h)
    answer_col = next(i for i, h in enumerate(headers) if "الجواب" in h)
    source_col = next(i for i, h in enumerate(headers) if "المصدر" in h)
    number_col = 0
    rows: list[dict] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = split_table_row(line)
        if len(cells) < len(headers):
            continue
        number_match = re.search(r"\d+", cells[number_col].translate(ARABIC_DIGITS))
        number = int(number_match.group()) if number_match else len(rows) + 1
        verse_label = clean_text(cells[verse_col])
        verses = extract_verses(verse_label, surah_name)
        if not verses and ("السورة" in verse_label or "–" in verse_label or "-" in verse_label):
            verses = [1]
        question = clean_text(cells[question_col])
        answer = clean_text(cells[answer_col])
        if not verses or not question or not answer:
            continue
        rows.append({
            "id": f"s{surah_number}-{number}",
            "number": number,
            "surah": surah_number,
            "verses": verses,
            "verseLabel": verse_label,
            "question": question,
            "answer": answer,
            "sources": parse_sources(cells[source_col]),
        })
    return surah_number, surah_name, rows


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_questions_from_backup.py /path/to/basair_full_backup")
    backup = Path(sys.argv[1]).resolve()
    files = sorted(p for p in backup.glob("*.md") if p.name != "README_BASAIR_BACKUP.md")
    all_questions: list[dict] = []
    seen_surahs: dict[int, tuple[str, int, str]] = {}
    for path in files:
        number, name, questions = parse_file(path)
        if number in seen_surahs:
            raise ValueError(f"Duplicate surah {number}: {path.name}")
        seen_surahs[number] = (name, len(questions), path.name)
        all_questions.extend(questions)
    missing = sorted(set(range(1, 115)) - set(seen_surahs))
    if missing:
        raise ValueError(f"Missing surahs: {missing}")
    output = Path(__file__).resolve().parent / "questions.js"
    payload = "window.BASAIR_QUESTIONS=" + json.dumps(all_questions, ensure_ascii=False, separators=(",", ":")) + ";\n"
    payload += "window.BASAIR_COUNTS=" + json.dumps({str(k): v[1] for k, v in seen_surahs.items()}, ensure_ascii=False, separators=(",", ":")) + ";\n"
    output.write_text(payload, encoding="utf-8")
    print(f"surahs={len(seen_surahs)} questions={len(all_questions)} bytes={output.stat().st_size}")
    for number in range(1, 115):
        name, count, filename = seen_surahs[number]
        print(f"{number:03d}\t{name}\t{count}\t{filename}")


if __name__ == "__main__":
    main()

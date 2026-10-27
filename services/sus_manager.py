import os
import csv
import json
from datetime import datetime
from pathlib import Path

# 10 Pertanyaan Standar System Usability Scale (SUS) - John Brooke (1986)
# Diterjemahkan secara baku ke Bahasa Indonesia dengan pendamping teks Bahasa Inggris
SUS_QUESTIONS = [
    {
        "id": 1,
        "text_id": "Saya rasa saya akan sering menggunakan sistem transkrip ini.",
        "text_en": "I think that I would like to use this transcription system frequently.",
        "type": "positive"
    },
    {
        "id": 2,
        "text_id": "Saya merasa sistem ini terlalu rumit, padahal bisa dibuat lebih sederhana.",
        "text_en": "I found the system unnecessarily complex.",
        "type": "negative"
    },
    {
        "id": 3,
        "text_id": "Saya merasa sistem ini mudah untuk digunakan.",
        "text_en": "I thought the system was easy to use.",
        "type": "positive"
    },
    {
        "id": 4,
        "text_id": "Saya rasa saya membutuhkan bantuan orang teknis untuk dapat menggunakan sistem ini.",
        "text_en": "I think that I would need the support of a technical person to be able to use this system.",
        "type": "negative"
    },
    {
        "id": 5,
        "text_id": "Saya merasa berbagai fungsi/fitur dalam sistem ini terintegrasi dengan sangat baik.",
        "text_en": "I found the various functions in this system were well integrated.",
        "type": "positive"
    },
    {
        "id": 6,
        "text_id": "Saya merasa ada terlalu banyak hal yang tidak konsisten pada sistem ini.",
        "text_en": "I thought there was too much inconsistency in this system.",
        "type": "negative"
    },
    {
        "id": 7,
        "text_id": "Saya rasa kebanyakan orang akan dapat mempelajari sistem ini dengan sangat cepat.",
        "text_en": "I would imagine that most people would learn to use this system very quickly.",
        "type": "positive"
    },
    {
        "id": 8,
        "text_id": "Saya merasa sistem ini sangat janggal atau membingungkan saat digunakan.",
        "text_en": "I found the system very cumbersome/awkward to use.",
        "type": "negative"
    },
    {
        "id": 9,
        "text_id": "Saya merasa sangat percaya diri saat menggunakan sistem ini.",
        "text_en": "I felt very confident using the system.",
        "type": "positive"
    },
    {
        "id": 10,
        "text_id": "Saya perlu membiasakan atau mempelajari banyak hal terlebih dahulu sebelum dapat menggunakan sistem ini.",
        "text_en": "I needed to learn a lot of things before I could get going with this system.",
        "type": "negative"
    }
]

def calculate_sus_score(responses: list) -> dict:
    """
    Menghitung skor SUS berdasarkan aturan baku John Brooke:
    - Item bernomor ganjil (1, 3, 5, 7, 9): skor kontribusi = nilai_jawaban - 1
    - Item bernomor genap (2, 4, 6, 8, 10): skor kontribusi = 5 - nilai_jawaban
    - Total skor kontribusi dikalikan 2.5 sehingga bernilai antara 0 hingga 100.
    """
    if len(responses) != 10:
        raise ValueError("Evaluasi SUS memerlukan tepat 10 jawaban kuesioner.")

    contributions = []
    for i, val in enumerate(responses):
        v = int(val)
        if not (1 <= v <= 5):
            raise ValueError(f"Nilai jawaban harus berada dalam rentang 1-5, diterima: {v}")
        if i % 2 == 0:  # Item ganjil (indeks 0, 2, 4, 6, 8 -> pertanyaan 1, 3, 5, 7, 9)
            contributions.append(v - 1)
        else:           # Item genap (indeks 1, 3, 5, 7, 9 -> pertanyaan 2, 4, 6, 8, 10)
            contributions.append(5 - v)

    raw_sum = sum(contributions)
    sus_score = round(raw_sum * 2.5, 2)

    # Penilaian Grade Scale (Bangor, Kortum, & Miller, 2008; Sauro & Lewis, 2012)
    if sus_score >= 80.3:
        grade = "A"
        adjective = "Excellent (Sangat Memuaskan)"
        acceptability = "Acceptable (Diterima Penuh)"
    elif sus_score >= 68.0:
        grade = "B"
        adjective = "Good (Baik / Di Atas Rata-rata)"
        acceptability = "Acceptable (Diterima)"
    elif sus_score >= 51.0:
        grade = "C"
        adjective = "OK (Cukup / Marginal)"
        acceptability = "Marginal (Perlu Penyempurnaan)"
    else:
        grade = "F"
        adjective = "Poor (Kurang / Tidak Memuaskan)"
        acceptability = "Not Acceptable (Tidak Diterima)"

    return {
        "score": sus_score,
        "grade": grade,
        "adjective": adjective,
        "acceptability": acceptability,
        "contributions": contributions,
        "benchmark_comparison": "Di Atas Standar Rata-rata Industri (68.0)" if sus_score >= 68.0 else "Di Bawah Standar Rata-rata Industri (68.0)"
    }

def get_evaluasi_dir(base_dir: str = None) -> Path:
    if base_dir is None:
        base_dir = Path(__file__).parent.parent
    else:
        base_dir = Path(base_dir)
    target = base_dir / "evaluasi_sus"
    target.mkdir(parents=True, exist_ok=True)
    return target

def save_sus_evaluation(
    respondent_name: str,
    role: str,
    responses: list,
    feedback: str = "",
    base_dir: str = None
) -> dict:
    """Menyimpan data evaluasi responden ke format CSV dan JSON."""
    calc = calculate_sus_score(responses)
    eval_dir = get_evaluasi_dir(base_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "timestamp": timestamp,
        "respondent_name": respondent_name.strip() or "Anonim",
        "role": role.strip() or "Pengguna",
        "sus_score": calc["score"],
        "grade": calc["grade"],
        "adjective": calc["adjective"],
        "acceptability": calc["acceptability"],
        "feedback": feedback.strip(),
        "q1": responses[0],
        "q2": responses[1],
        "q3": responses[2],
        "q4": responses[3],
        "q5": responses[4],
        "q6": responses[5],
        "q7": responses[6],
        "q8": responses[7],
        "q9": responses[8],
        "q10": responses[9],
    }

    # Simpan ke CSV (Append)
    csv_file = eval_dir / "hasil_evaluasi_sus.csv"
    file_exists = csv_file.exists()
    fieldnames = list(record.keys())

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    # Simpan riwayat ke JSON
    json_file = eval_dir / "hasil_evaluasi_sus.json"
    existing_records = []
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                existing_records = json.load(f)
        except Exception:
            existing_records = []

    existing_records.append(record)
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(existing_records, f, indent=2, ensure_ascii=False)

    return {"record": record, "calculation": calc, "total_records": len(existing_records)}

def load_sus_statistics(base_dir: str = None) -> dict:
    """Membaca statistik akumulasi skor SUS dari seluruh responden yang sudah mengisi."""
    eval_dir = get_evaluasi_dir(base_dir)
    json_file = eval_dir / "hasil_evaluasi_sus.json"

    if not json_file.exists():
        return {
            "total_respondents": 0,
            "average_score": 0.0,
            "overall_grade": "-",
            "records": []
        }

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception:
        records = []

    if not records:
        return {
            "total_respondents": 0,
            "average_score": 0.0,
            "overall_grade": "-",
            "records": []
        }

    scores = [r["sus_score"] for r in records if "sus_score" in r]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    if avg_score >= 80.3:
        overall_grade = "Grade A (Excellent)"
    elif avg_score >= 68.0:
        overall_grade = "Grade B (Good)"
    elif avg_score >= 51.0:
        overall_grade = "Grade C (OK)"
    else:
        overall_grade = "Grade F (Poor)"

    return {
        "total_respondents": len(records),
        "average_score": avg_score,
        "overall_grade": overall_grade,
        "records": records
    }

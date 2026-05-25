import os
import re
import json
import time
import warnings
from flask import Flask, render_template, request, jsonify

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import google.generativeai as genai

app = Flask(__name__)

API_KEY = (
    os.getenv('GEMINI_API_KEY')
    or os.getenv('GOOGLE_API_KEY')
    or os.getenv('OPENAI_API_KEY')
)
if not API_KEY:
    raise RuntimeError(
        'Environment variable GEMINI_API_KEY or GOOGLE_API_KEY is required. '
        'Set one before running NutriMind.'
    )
genai.configure(api_key=API_KEY)

CACHED_WORKING_MODEL = None


def extract_json_from_text(text):
    """
    Membersihkan teks respons dari AI dan mengonversinya menjadi objek JSON.
    Menggunakan algoritma Balanced Stack-based Parser yang sangat kuat untuk memisahkan
    dan mengisolasi blok JSON yang valid, terlepas dari adanya teks basa-basi,
    markdown, backticks, koma gantung, maupun duplikasi blok JSON dari model AI.
    """
    try:
        cleaned_text = text.strip()
        
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(cleaned_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                if brace_count > 0:
                    brace_count -= 1
                    if brace_count == 0:
                        potential_json = cleaned_text[start_idx:i + 1]
                        potential_json = re.sub(r',\s*([\]}])', r'\1', potential_json)
                        potential_json = re.sub(r'[\x00-\x1F\x7F]', '', potential_json)
                        
                        try:
                            return json.loads(potential_json)
                        except Exception:
                            pass

        json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
        for block in json_blocks:
            try:
                block_clean = re.sub(r',\s*([\]}])', r'\1', block)
                block_clean = re.sub(r'[\x00-\x1F\x7F]', '', block_clean)
                return json.loads(block_clean)
            except Exception:
                pass

        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            fallback_str = cleaned_text[start_idx:end_idx + 1]
            fallback_str = re.sub(r',\s*([\]}])', r'\1', fallback_str)
            fallback_str = re.sub(r'[\x00-\x1F\x7F]', '', fallback_str)
            return json.loads(fallback_str)

        raise ValueError("Tidak mendeteksi adanya struktur data JSON yang valid di dalam respons AI.")

    except Exception as e:
        print(f"[Error Parsing JSON]: {e}\nTeks asli dari Gemini:\n{text}")
        raise ValueError(f"Gagal memformat data gizi dari AI: {str(e)}")


def resolve_best_model():
    """
    Kembalikan daftar model Gemini yang valid berdasarkan urutan prioritas.
    Menghindari model lama yang sering tidak tersedia pada API v1beta.
    """
    global CACHED_WORKING_MODEL
    
    if CACHED_WORKING_MODEL:
        return [CACHED_WORKING_MODEL]

    return [
        'models/gemini-2.5-flash',
        'models/gemini-2.5-flash-latest',
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-latest',
        'models/gemini-1.5-flash-8b'
    ]


def generate_with_model(model_name, system_prompt, user_prompt):
    prompt_text = f"{system_prompt}\n\n{user_prompt}"
    if hasattr(genai, 'generate_text'):
        return genai.generate_text(
            model=model_name,
            prompt=prompt_text,
            temperature=0.3,
            max_output_tokens=1500,
        )

    model = genai.GenerativeModel(model_name=model_name)
    return model.generate_content([system_prompt, user_prompt])


@app.route('/')
def home():
    """Menampilkan halaman utama aplikasi NutriMind."""
    try:
        return render_template('index.html')
    except Exception as e:
        return (
            f"<h3>Error: Pastikan file 'index.html' berada di dalam folder "
            f"bernama 'templates'</h3><br>Detail: {str(e)}"
        ), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Endpoint utama: Menerima jurnal pengguna dan mood dari frontend,
    mengirimkannya ke Gemini dengan sistem instruksi terstruktur,
    dan mengembalikan data JSON terstruktur yang cocok dengan index.html.
    """
    global CACHED_WORKING_MODEL
    data = request.get_json()

    if not data or not data.get('journal'):
        return jsonify({"error": "Jurnal tidak boleh kosong."}), 400

    journal_text = data['journal'].strip()
    mood = data.get('mood', 'Netral')

    if len(journal_text) < 10:
        return jsonify({"error": "Ceritakan lebih detail ya, minimal 10 karakter."}), 400

    try:
        system_prompt = (
            "Anda adalah NutriMind AI, ahli gizi dan wellness coach yang ramah, hangat, dan suportif.\n"
            "Tugas Anda adalah menganalisis keluhan fisik, mood, dan makanan harian pengguna.\n"
            "Gunakan bahasa Indonesia yang empatik, santai, dan mudah dimengerti.\n\n"
            "Anda WAJIB memberikan respons HANYA dalam format JSON mentah tanpa backtick (```), tanpa markdown, "
            "dan tanpa penjelasan teks tambahan di luar blok JSON tersebut.\n"
            "Struktur JSON Anda harus persis seperti template berikut:\n"
            "{\n"
            '  "ringkasan": "Ulasan singkat 1-2 kalimat bernada hangat tentang kondisi mereka hari ini.",\n'
            '  "skor_nutrisi": 70,\n'
            '  "kalori_estimasi": "~1500 kkal",\n'
            '  "kekurangan": [\n'
            '    {\n'
            '      "nutrisi": "Nama Zat Gizi/Nutrisi",\n'
            '      "dampak": "Mengapa kekurangan zat ini memicu keluhan fisik yang ditulis user.",\n'
            '      "icon": "Emoji yang relevan"\n'
            '    }\n'
            '  ],\n'
            '  "insight": "Penjelasan edukatif ringan menghubungkan makanan dengan keluhan fisik.",\n'
            '  "saran_makanan": [\n'
            '    {\n'
            '      "nama": "Nama Makanan Alternatif Sehat",\n'
            '      "alasan": "Mengapa makanan ini membantu memulihkan energi/kondisi user.",\n'
            '      "mudah_didapat": true\n'
            '    }\n'
            '  ],\n'
            '  "pesan_motivasi": "Satu kalimat penyemangat hangat agar mereka terus menjaga pola makan sehat."\n'
            "}"
        )

        user_prompt = (
            f"Kondisi Mood Pengguna: {mood}\n"
            f"Catatan Konsumsi & Kondisi Tubuh Pengguna:\n\"{journal_text}\""
        )

        model_candidates = resolve_best_model()
        response = None
        last_exception = None

        max_retries = 2
        retry_delays = [1]

        for model_name in model_candidates:
            success = False
            for attempt in range(max_retries):
                try:
                    print(f"[NutriMind]: Mengirim ke Gemini ({model_name}) - Percobaan ke-{attempt + 1}...")
                    response = generate_with_model(model_name, system_prompt, user_prompt)
                    response_text = None

                    if isinstance(response, str):
                        response_text = response
                    else:
                        response_text = getattr(response, 'text', None)
                        if not response_text and isinstance(response, dict):
                            response_text = response.get('text') or response.get('output')
                        if not response_text and hasattr(response, 'output'):
                            response_text = str(response.output)

                    if response_text:
                        print(f"[NutriMind]: Sukses menggunakan model {model_name}!")
                        CACHED_WORKING_MODEL = model_name
                        response = response_text
                        success = True
                        break
                except Exception as ex:
                    last_exception = ex
                    err_str = str(ex)
                    
                    if any(err in err_str for err in ["400", "403", "404", "INVALID_ARGUMENT", "PERMISSION_DENIED", "NOT_FOUND"]):
                        break
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delays[attempt])
            
            if success:
                break

        if not response:
            raise last_exception if last_exception else Exception("Semua kandidat model Gemini gagal diakses.")
        
        parsed_result = extract_json_from_text(response)
        return jsonify(parsed_result)

    except Exception as e:
        error_msg = str(e)
        print(f"[NutriMind Server Error]: {error_msg}")
        
        if "503" in error_msg or "overloaded" in error_msg.lower():
            return jsonify({
                "error": "Server Google Gemini saat ini sedang sangat sibuk (Error 503). Sistem telah mencoba mengirim ulang otomatis tetapi server masih belum merespon. Mohon kirimkan ulang kembali dalam beberapa detik."
            }), 503
        elif "404" in error_msg or "not found" in error_msg.lower():
            return jsonify({
                "error": "Layanan Gemini tidak dapat mendeteksi model yang kompatibel pada API Key Anda. Pastikan API Key dibuat langsung melalui Google AI Studio."
            }), 404
        return jsonify({"error": f"Terjadi kendala saat menganalisis data: {error_msg}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
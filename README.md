# 🥗 NutriMind — AI Food Journal & Wellness Tracker

> Mini Competition (Minicomp) GDGoC Universitas Esa Unggul
> Tema: "Build Impactful Solutions with Artificial Intelligence"

---

## 💡 Tentang Proyek

**NutriMind** adalah aplikasi web pencatat makanan harian yang menghubungkan
nutrisi dengan kondisi fisik dan suasana hati pengguna.

Proyek ini dibangun menggunakan **Google AI Studio** sebagai platform untuk
mengelola model dan panggilan API Gemini.

Pengguna cukup mengetik secara bebas apa yang mereka makan hari ini dan
bagaimana kondisi tubuh mereka. Sistem akan mengirimkan data ke model **Gemini Flash**
(dapat menggunakan versi terbaru yang tersedia, seperti **Gemini 2.5 Flash**),
yang kemudian akan menganalisis pola tersebut dan memberikan:

- 📊 Skor nutrisi harian (1–100)
- ⚠️ Kekurangan nutrisi beserta dampaknya pada tubuh
- 🧠 Insight yang menghubungkan makanan dengan kondisi fisik
- 🥦 Saran makanan pengganti yang lebih sehat & mudah didapat
- 💪 Pesan motivasi yang personal

---

## 🛠️ Teknologi

| Teknologi          | Kegunaan                        |
|--------------------|---------------------------------|
| Python 3.8+        | Runtime backend                 |
| Flask              | Web framework                   |
| Gemini Flash       | Analisis teks nutrisi (AI)      |
| Tailwind CSS       | Styling responsif               |
| HTML + CSS + JS    | Frontend UI                     |

---

## 📁 Struktur Folder

```
nutrimind-v2/
├── app.py               ← Backend Flask
├── package.json         ← Dependensi Node.js (Tailwind CSS)
├── templates/
│   └── index.html       ← Seluruh UI dalam 1 file
└── static/
    ├── css/
    │   ├── input.css    ← Tailwind source
    │   └── main.css     ← Custom styles + tokens
    └── js/
        └── main.js      ← Frontend logic
```

---

## 🚀 Cara Menjalankan

### 1. (Disarankan) Setup Virtual Environment

Langkah ini direkomendasikan untuk menjaga dependensi Python tetap terisolasi, tetapi tidak wajib.

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Linux / Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Jika Anda sudah menggunakan environment Python tersendiri di Codespaces atau mesin lokal, langkah ini bisa dilewati.

### 2. Install Dependensi Python
```bash
pip install -r requirements.txt
```

### 3. Install Dependensi Node.js (Tailwind CSS)
```bash
npm install
```

### 4. Setup API Key
Aplikasi akan memuat nilai dari file `.env` secara otomatis jika `python-dotenv` sudah terpasang.

- Salin `.env` dari file contoh atau buat sendiri di folder proyek.
- Tambahkan API key Anda ke dalam `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Anda juga masih bisa menggunakan environment variable langsung:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

atau di Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

### 5. Jalankan Server
```bash
python app.py
```

### 6. Buka di Browser / HP Android
- **Laptop:** `http://localhost:5000`
- **HP Android (WiFi sama):**
  - **Windows:** Buka CMD, ketik `ipconfig` → cari "IPv4 Address"
  - **Linux:** Ketik `hostname -I` atau `ip addr show`
  - Buka di HP: `http://[IP_LAPTOP]:5000`

---

## 🔌 Alur Kerja

```
User ketik jurnal makanan + kondisi tubuh
           │
           ▼ POST /analyze (JSON)
      Flask app.py
           │
           ▼ Prompt + teks ke Gemini API
    Gemini Flash (model terbaik/terbaru otomatis)
           │
           ▼ JSON: skor, insight, kekurangan, saran
      Flask → response
           │
           ▼
   index.html menampilkan hasil
```

---

## 👥 Tim

| Nama                    | Peran                          |
|-------------------------|--------------------------------|
| Farrel Gian             | Backend Flask + Gemini API     |
| Bimo Rajendra Fassah    | UI/UX (index.html)             |

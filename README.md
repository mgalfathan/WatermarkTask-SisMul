# DWTSS-watermark
Python library dan CLI tool untuk menyisipkan **invisible watermark** pada citra digital menggunakan metode **DWT dengan Spread Spectrum** (Discrete Wavelet Transform + Spread Spectrum).

Watermark berupa citra biner 64x64 yang memuat nama **Muhammad Ghiffary Alfathan**, disisipkan pada sub-band LH kanal Y (YCrCb) sehingga warna foto tidak berubah. 

---

## Instalasi

```bash
pip install -r requirements.txt
```

atau dari source:

```bash
git clone https://github.com/username/dwt-watermark.git
cd dwt-watermark
pip install -e .
```

**Dependencies:** `opencv-python`, `numpy`, `PyWavelets`, `matplotlib`

---

## Penggunaan — CLI

### Embed watermark

```bash
python -m dwt_watermark encode -i foto.jpeg -o foto_wm.jpeg
```

### Decode watermark

```bash
python -m dwt_watermark decode -i foto_wm.jpeg
```

### Evaluasi robustness terhadap JPEG

```bash
python -m dwt_watermark evaluate -i foto.jpeg -o hasil/
```

---

## Penggunaan — Library API

### Embed watermark

```python
import cv2
from dwt_watermark import WatermarkEncoder, create_watermark

host = cv2.imread('foto.jpeg')
host = cv2.resize(host, (512, 512))

wm      = create_watermark()           # citra biner 64x64
encoder = WatermarkEncoder()
stego   = encoder.encode(host, wm)

cv2.imwrite('foto_wm.jpeg', stego, [cv2.IMWRITE_JPEG_QUALITY, 100])
```

### Decode watermark

```python
import cv2
from dwt_watermark import WatermarkDecoder

stego   = cv2.imread('foto_wm.jpeg')
decoder = WatermarkDecoder()
wm_rec  = decoder.decode(stego)       # returns ndarray 64x64

cv2.imwrite('wm_extracted.png', wm_rec * 255)
```

---

## Cara Kerja

```
Host (BGR)
    |
    v
Konversi ke YCrCb
    |
    +-- kanal Y ──> DWT Haar level-1 ──> sub-band LH
    |                                         |
    |                              Spread Spectrum embedding
    |                              bit=1 : +alpha * pn[k]
    |                              bit=0 : -alpha * pn[k]
    |                                         |
    +-- kanal Cr, Cb (tidak disentuh) --------+
    |                                         |
    v                                     IDWT
Stego JPEG <── konversi balik YCrCb <────────+
```

**Watermark** dibangkitkan sebagai matriks biner 64x64 (noise acak seed=42) dengan nama "M.Ghiffary / Alfathan" di-overlay sebagai teks (area teks = bit 1).

**Embedding:** tiap bit dikodekan ke chunk koefisien LH menggunakan PN vector Gaussian ternormalisasi (seed=100).

**Extraction (blind):** korelasikan tiap chunk dengan PN vector yang sama. Korelasi >= 0 → bit 1, negatif → bit 0.

---

## Hasil Evaluasi

Foto host: 512×512 px | Alpha: 20.0 | PSNR stego: **39.91 dB**

### 1. Watermark yang Disisipkan

Watermark berupa citra biner 64×64 berisi noise acak (seed=42) dengan overlay teks
"M.Ghiffary / Alfathan". Area teks = bit 1, sisanya = bit 0.

<img width="431" height="460" alt="watermark_original" src="https://github.com/user-attachments/assets/2984722c-e1d5-497d-bdfc-4dabc931dba7" />

### 2. Imperceptibility — Host vs Stego

Stego JPEG (kanan) secara visual tidak dapat dibedakan dari host asli (kiri),
dengan PSNR **39.91 dB** (di atas ambang 35 dB yang dianggap *invisible*).

<img width="1915" height="701" alt="imperceptibility" src="https://github.com/user-attachments/assets/dfc1e739-ca1a-4b60-94b7-00daac22ef7a" />

### 3. Watermark Hasil Ekstraksi

Hasil decode dari stego image, watermark dapat direkonstruksi dengan benar
secara blind (tanpa membutuhkan host asli).

<img width="64" height="64" alt="foto_wm_wm_extracted" src="https://github.com/user-attachments/assets/55e1d6cb-d0fe-4c98-8262-475d825f9a67" />

### 4. Tabel Robustness terhadap Kompresi JPEG

| QF | PSNR (dB) | BER (%) | NC | Status |
|----|-----------|---------|----|--------|
| 95 | 36.94 | 1.56 | 0.9844 | OK |
| 90 | 35.77 | 1.71 | 0.9829 | OK |
| 80 | 34.85 | 4.44 | 0.9556 | OK (noise kecil) |
| 70 | 34.42 | 8.74 | 0.9130 | OK (noise sedang) |
| 60 | 34.05 | 13.11 | 0.8703 | GAGAL |
| <= 50 | <= 33.76 | >= 19.70 | <= 0.81 | GAGAL |

Breaking point: **QF <= 60**. Degradasi bersifat gradual (berbeda dari cliff transition pada DCT-QIM).
Note: Percobaan ini menggunakan Threshold BER di 10% untuk penentuan keberhasilan 

### 5. Grafik PSNR vs Quality Factor

PSNR menurun secara linear seiring turunnya QF, mencerminkan derajat distorsi
yang ditambahkan oleh kompresi JPEG ke stego image.

<img width="1336" height="583" alt="plot_psnr" src="https://github.com/user-attachments/assets/b5ce1de6-700b-4041-ad5a-4e1a175d7333" />

### 6. Grafik BER & NC vs Quality Factor

Bit Error Rate (BER) naik dan Normalized Correlation (NC) turun seiring QF
mengecil. Threshold robust: NC ≥ 0.85 (tercapai sampai QF=70).

<img width="1786" height="667" alt="plot_ber_nc" src="https://github.com/user-attachments/assets/e249f5fe-2911-42a2-b36a-066dd6ef6801" />

### 7. Visualisasi Watermark Hasil Ekstraksi per QF

Grid berikut menunjukkan watermark hasil ekstraksi pada berbagai level kompresi.
Pada QF tinggi (≥70) teks "M.Ghiffary / Alfathan" masih terbaca jelas; pada
QF ≤ 50 noise mendominasi dan watermark mulai tidak dapat dikenali.

<img width="1654" height="721" alt="extracted_watermarks_grid" src="https://github.com/user-attachments/assets/6df52ecd-edd3-4736-abc1-0091807b2dc9" />

---

## Struktur Repo

```
dwt-watermark/
├── dwt_watermark/
│   ├── __init__.py       # export utama
│   ├── encoder.py        # WatermarkEncoder
│   ├── decoder.py        # WatermarkDecoder
│   ├── watermark.py      # create_watermark()
│   ├── utils.py          # psnr, ber, nc
│   └── __main__.py       # CLI: encode / decode / evaluate
├── evaluate.py           # skrip evaluasi standalone
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

---

## Lisensi

MIT License — lihat [LICENSE](LICENSE)

---

## Author

Muhammad Ghiffary Alfathan (18224084)
Sistem dan Teknologi Informasi, Institut Teknologi Bandung

# dwt-watermark

![Python](https://img.shields.io/badge/python-%3E%3D3.8-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey.svg)

Python library and CLI tool untuk menyisipkan **invisible watermark** pada citra digital menggunakan metode **DWT Spread Spectrum** (Discrete Wavelet Transform + Spread Spectrum).

Watermark disisipkan pada sub-band LH kanal luminance (Y) dalam ruang warna YCrCb sehingga warna foto tidak berubah secara kasat mata. Ekstraksi bersifat **blind** — tidak memerlukan citra asli.

---

## Fitur

- Embedding pada kanal Y (YCrCb) — warna foto tetap terjaga
- Blind extraction — tidak butuh citra asli saat dekode
- Watermark berupa string teks yang dikodekan sebagai bit biner
- Evaluasi robustness terhadap kompresi JPEG (berbagai Quality Factor)
- CLI dan library API

---

## Instalasi

```bash
pip install -r requirements.txt
```

atau langsung install dari source:

```bash
git clone https://github.com/username/dwt-watermark.git
cd dwt-watermark
pip install -e .
```

**Dependencies:** `opencv-python`, `numpy`, `pywavelets`, `matplotlib`

---

## Penggunaan — Library API

### Embed watermark

```python
import cv2
from dwt_watermark import WatermarkEncoder

bgr = cv2.imread('foto.jpg')

encoder = WatermarkEncoder()
encoder.set_watermark('Muhammad Ghiffary Alfathan')
bgr_encoded = encoder.encode(bgr)

cv2.imwrite('foto_wm.jpg', bgr_encoded, [cv2.IMWRITE_JPEG_QUALITY, 100])
```

### Decode watermark

```python
import cv2
from dwt_watermark import WatermarkDecoder

bgr = cv2.imread('foto_wm.jpg')

decoder = WatermarkDecoder(wm_length=200)  # panjang bit watermark
text = decoder.decode(bgr)
print(text)  # "Muhammad Ghiffary Alfathan"
```

---

## Penggunaan — CLI

```bash
# Embed
python -m dwt_watermark encode -i foto.jpg -w "Muhammad Ghiffary Alfathan" -o foto_wm.jpg

# Decode
python -m dwt_watermark decode -i foto_wm.jpg -l 200

# Evaluasi robustness terhadap JPEG
python -m dwt_watermark evaluate -i foto.jpg -w "Muhammad Ghiffary Alfathan" -o hasil/
```

### Opsi lengkap

```
positional arguments:
  {encode,decode,evaluate}

optional arguments:
  -i, --input     Path foto input
  -w, --watermark Teks watermark yang akan disisipkan
  -o, --output    Path output (file atau folder)
  -l, --length    Panjang bit watermark (diperlukan saat decode)
  -a, --alpha     Skala penyisipan, default=20.0
  -s, --seed      PN seed, default=100
  -v, --verbose   Tampilkan info proses
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
    |                              (PN sequence x alpha x bit)
    |                                         |
    +-- kanal Cr, Cb (tidak dimodifikasi) ----+
    |                                         |
    v                                     IDWT
Stego (BGR) <── konversi balik YCrCb <───────+
```

**Embedding:** tiap bit dikodekan ke chunk koefisien LH menggunakan PN vector Gaussian ternormalisasi. Bit 1 → +alpha × pn, Bit 0 → −alpha × pn.

**Extraction (blind):** korelasikan tiap chunk dengan PN vector yang sama. Korelasi ≥ 0 → bit 1, korelasi < 0 → bit 0.

---

## Hasil Evaluasi

Foto host: 512×512 px | Watermark: "Muhammad Ghiffary Alfathan" | Alpha: 20.0

| QF | PSNR (dB) | BER (%) | NC | Status |
|----|-----------|---------|----|--------|
| 95 | 36.94 | 1.56 | 0.9844 | OK |
| 90 | 35.77 | 1.71 | 0.9829 | OK |
| 80 | 34.85 | 4.44 | 0.9556 | OK (noise kecil) |
| 70 | 34.42 | 8.74 | 0.9130 | OK (noise sedang) |
| 60 | 34.05 | 13.11 | 0.8703 | GAGAL |
| 50 | 33.76 | 19.70 | 0.8089 | GAGAL |
| ≤40 | ≤33.47 | ≥28.86 | ≤0.74 | GAGAL |

- PSNR stego (tanpa kompresi): **39.91 dB**
- Breaking point: **QF ≤ 60**
- Pola degradasi: **gradual** (berbeda dari cliff transition pada DCT-QIM)

---

## Struktur Repo

```
dwt-watermark/
├── dwt_watermark/
│   ├── __init__.py
│   ├── encoder.py       # WatermarkEncoder
│   ├── decoder.py       # WatermarkDecoder
│   ├── utils.py         # konversi teks <-> bit, metrik
│   └── __main__.py      # CLI entry point
├── evaluate.py          # skrip evaluasi robustness lengkap
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

---

## Metrik

| Metrik | Keterangan |
|--------|------------|
| PSNR | Peak Signal-to-Noise Ratio antara host dan stego. > 35 dB masih dapat diterima secara visual. |
| BER | Bit Error Rate — persentase bit yang salah saat ekstraksi. 0% = sempurna, 50% = acak. |
| NC | Normalized Correlation antara watermark asli dan hasil ekstraksi. ≥ 0.75 dianggap valid. |

---

## Lisensi

MIT License — lihat [LICENSE](LICENSE)

---

## Author

Muhammad Ghiffary Alfathan  
Sistem dan Teknologi Informasi, Institut Teknologi Bandung

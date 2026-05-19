import cv2
import numpy as np
import pywt


class WatermarkDecoder:
    """
    Mengekstraksi watermark biner dari citra stego secara blind.

    Tidak memerlukan citra asli — hanya butuh pn_seed yang sama
    dengan yang digunakan saat embedding.

    Parameters
    ----------
    wm_size : int
        Ukuran sisi watermark (default 64 -> matriks 64x64 = 4096 bit).
    alpha : float
        Skala penyisipan. Harus sama dengan nilai saat encode. Default: 20.0
    pn_seed : int
        Seed pseudo-noise. Harus sama dengan nilai saat encode. Default: 100
    wavelet : str
        Jenis wavelet. Default: 'haar'
    """

    def __init__(self, wm_size: int = 64, alpha: float = 20.0,
                 pn_seed: int = 100, wavelet: str = 'haar'):
        self.wm_size = wm_size
        self.alpha   = alpha
        self.pn_seed = pn_seed
        self.wavelet = wavelet

    def decode(self, stego_bgr: np.ndarray) -> np.ndarray:
        """
        Ekstraksi watermark dari citra stego.

        Parameters
        ----------
        stego_bgr : np.ndarray
            Citra stego BGR (bisa sudah terkompresi JPEG).

        Returns
        -------
        np.ndarray
            Watermark biner uint8, shape (wm_size, wm_size). Nilai 0 atau 1.
        """
        n_bits = self.wm_size * self.wm_size

        # Ambil kanal Y dari YCrCb
        ycrcb   = cv2.cvtColor(stego_bgr, cv2.COLOR_BGR2YCrCb).astype(np.float64)
        Y       = ycrcb[:, :, 0]
        LH      = pywt.dwt2(Y, self.wavelet)[1][0]

        lh_flat = LH.flatten()
        chunk   = len(lh_flat) // n_bits

        # Korelasi dengan PN sequence yang sama
        np.random.seed(self.pn_seed)
        wm_rec = np.zeros(n_bits, dtype=np.uint8)

        for k in range(n_bits):
            pn   = np.random.randn(chunk)
            pn  /= (np.linalg.norm(pn) + 1e-12)
            corr = np.dot(lh_flat[k * chunk:(k + 1) * chunk], pn)
            wm_rec[k] = 1 if corr >= 0 else 0

        return wm_rec.reshape(self.wm_size, self.wm_size)

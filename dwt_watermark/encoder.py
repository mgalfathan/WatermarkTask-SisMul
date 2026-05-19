import cv2
import numpy as np
import pywt


class WatermarkEncoder:
    """
    Menyisipkan watermark citra biner ke foto menggunakan DWT Spread Spectrum.

    Teknik:
    - DWT Haar level-1 pada kanal Y (luminance) dalam ruang warna YCrCb
    - Spread Spectrum pada sub-band LH
    - Kanal Cr dan Cb tidak dimodifikasi -> warna foto tetap terjaga
    - Stego disimpan sebagai JPEG

    Parameters
    ----------
    alpha : float
        Skala penyisipan. Lebih besar = lebih robust, PSNR lebih rendah.
        Nilai laporan: 20.0
    pn_seed : int
        Seed pseudo-noise sequence. Harus sama saat ekstraksi.
        Nilai laporan: 100
    wavelet : str
        Jenis wavelet. Nilai laporan: 'haar'
    """

    def __init__(self, alpha: float = 20.0, pn_seed: int = 100,
                 wavelet: str = 'haar'):
        self.alpha   = alpha
        self.pn_seed = pn_seed
        self.wavelet = wavelet

    def encode(self, host_bgr: np.ndarray,
               watermark: np.ndarray) -> np.ndarray:
        """
        Sisipkan watermark biner ke citra host.

        Parameters
        ----------
        host_bgr : np.ndarray
            Citra host BGR (output cv2.imread, sudah di-resize ke 512x512).
        watermark : np.ndarray
            Watermark biner uint8, shape (64, 64). Nilai 0 atau 1.
            Gunakan create_watermark() dari dwt_watermark.watermark.

        Returns
        -------
        np.ndarray
            Citra stego BGR.
        """
        H, W = host_bgr.shape[:2]

        # Konversi ke YCrCb, ambil kanal Y
        ycrcb = cv2.cvtColor(host_bgr, cv2.COLOR_BGR2YCrCb).astype(np.float64)
        Y     = ycrcb[:, :, 0]

        # DWT Haar level-1
        LL, (LH, HL, HH) = pywt.dwt2(Y, self.wavelet)

        # Spread Spectrum embedding pada LH
        lh_flat = LH.flatten()
        n_bits  = watermark.size
        chunk   = len(lh_flat) // n_bits

        np.random.seed(self.pn_seed)
        lh_wm = lh_flat.copy()

        for k, bit in enumerate(watermark.flatten()):
            pn   = np.random.randn(chunk)
            pn  /= (np.linalg.norm(pn) + 1e-12)
            sign = 1.0 if bit == 1 else -1.0
            lh_wm[k * chunk:(k + 1) * chunk] += self.alpha * sign * pn

        # Rekonstruksi Y
        LH_wm   = lh_wm.reshape(LH.shape)
        Y_stego = pywt.idwt2((LL, (LH_wm, HL, HH)), self.wavelet)
        Y_stego = np.clip(Y_stego[:H, :W], 0, 255)

        # Gabung Y_stego + Cr + Cb asli -> BGR
        ycrcb_out          = ycrcb.copy()
        ycrcb_out[:, :, 0] = Y_stego
        return cv2.cvtColor(ycrcb_out.astype(np.uint8), cv2.COLOR_YCrCb2BGR)

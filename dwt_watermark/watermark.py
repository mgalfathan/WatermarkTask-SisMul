import cv2
import numpy as np


def create_watermark(size: int = 64, seed: int = 42) -> np.ndarray:
    """
    Buat watermark biner 64x64 berisi nama Muhammad Ghiffary Alfathan
    di atas noise acak — sama persis dengan yang dipakai di laporan.

    Langkah:
    1. Bangkitkan matriks biner acak dari Bernoulli(p=0.5) dengan seed tetap.
    2. Overlay teks "M.Ghiffary" dan "Alfathan" — area teks dipaksa ke bit=1.
    3. Bingkai luar (1 piksel) dipaksa ke 0 sebagai marker orientasi.

    Parameters
    ----------
    size : int
        Ukuran watermark (default 64 -> 64x64 = 4096 bit).
    seed : int
        Random seed untuk reproducibility (default 42).

    Returns
    -------
    np.ndarray
        Matriks biner uint8 berukuran (size, size). Nilai 0 atau 1.
    """
    np.random.seed(seed)
    wm = np.random.randint(0, 2, (size, size), dtype=np.uint8)

    # Overlay nama sebagai teks putih di canvas kosong
    wm_vis = np.zeros((size, size), dtype=np.uint8)
    cv2.putText(wm_vis, 'M.Ghiffary', (1, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.28, 255, 1)
    cv2.putText(wm_vis, 'Alfathan',   (5, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.28, 255, 1)

    # Area teks dipaksa bit=1
    wm[wm_vis > 128] = 1

    # Bingkai luar = 0 sebagai marker orientasi
    wm[0, :]  = 0
    wm[-1, :] = 0
    wm[:, 0]  = 0
    wm[:, -1] = 0

    return wm

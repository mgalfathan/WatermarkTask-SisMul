import numpy as np


def psnr(original: np.ndarray, modified: np.ndarray) -> float:
    """PSNR antara dua citra (dB)."""
    mse = np.mean((original.astype(np.float64) - modified.astype(np.float64)) ** 2)
    return 100.0 if mse == 0 else 10.0 * np.log10(255.0 ** 2 / mse)


def ber(wm_original: np.ndarray, wm_recovered: np.ndarray) -> float:
    """Bit Error Rate (%). 0% = sempurna, ~50% = acak."""
    return float(np.mean(wm_original.flatten() != wm_recovered.flatten()) * 100)


def nc(wm_original: np.ndarray, wm_recovered: np.ndarray) -> float:
    """Normalized Correlation [-1, 1]. >= 0.75 dianggap valid."""
    a = wm_original.flatten().astype(np.float64)
    b = wm_recovered.flatten().astype(np.float64)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return 0.0 if denom < 1e-12 else float(np.dot(a, b) / denom)

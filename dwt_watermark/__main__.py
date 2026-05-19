
import argparse
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from . import WatermarkEncoder, WatermarkDecoder, create_watermark
from .utils import psnr, ber, nc

QF_LIST = [95, 90, 80, 70, 60, 50, 40, 30, 20, 10]

plt.rcParams.update({
    'font.family': 'serif',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': '--',
})


def cmd_encode(args):
    img = cv2.imread(args.input)
    if img is None:
        sys.exit(f"[ERROR] Tidak dapat membaca: {args.input}")
    img = cv2.resize(img, (512, 512))
    wm  = create_watermark()

    encoder = WatermarkEncoder(alpha=args.alpha, pn_seed=args.seed)
    stego   = encoder.encode(img, wm)

    out = args.output or args.input.rsplit('.', 1)[0] + '_wm.jpg'
    cv2.imwrite(out, stego, [cv2.IMWRITE_JPEG_QUALITY, 100])

    if args.verbose:
        p = psnr(img, stego)
        print(f"[INFO] Output   : {out}")
        print(f"[INFO] PSNR     : {p:.2f} dB")
        print(f"[INFO] WM size  : {wm.shape} ({wm.size} bit)")


def cmd_decode(args):
    img = cv2.imread(args.input)
    if img is None:
        sys.exit(f"[ERROR] Tidak dapat membaca: {args.input}")

    decoder = WatermarkDecoder(alpha=args.alpha, pn_seed=args.seed)
    wm_rec  = decoder.decode(img)

    out = args.output or args.input.rsplit('.', 1)[0] + '_wm_extracted.png'
    cv2.imwrite(out, wm_rec * 255)
    print(f"[INFO] Watermark tersimpan: {out}")

    if args.verbose:
        print(f"[INFO] Shape      : {wm_rec.shape}")
        print(f"[INFO] Bit-1 ratio: {wm_rec.mean():.3f}")


def cmd_evaluate(args):
    img = cv2.imread(args.input)
    if img is None:
        sys.exit(f"[ERROR] Tidak dapat membaca: {args.input}")

    img     = cv2.resize(img, (512, 512))
    wm      = create_watermark()
    out_dir = args.output or 'hasil_evaluasi'
    os.makedirs(out_dir, exist_ok=True)

    cv2.imwrite(os.path.join(out_dir, 'host.png'), img)
    cv2.imwrite(os.path.join(out_dir, 'watermark.png'), wm * 255)

    # Visualisasi watermark
    fig, ax = plt.subplots(figsize=(3.2, 3.2), facecolor='#FAFAFA')
    ax.imshow(wm, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    ax.set_title('Watermark Asli (64x64)', fontsize=10, pad=8)
    ax.set_xlabel('kolom piksel', fontsize=7)
    ax.set_ylabel('baris piksel', fontsize=7)
    ax.tick_params(labelsize=6)
    fig.tight_layout(pad=1.2)
    fig.savefig(os.path.join(out_dir, 'watermark_original.png'),
                dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close()

    # Embed & simpan stego sebagai JPEG
    encoder    = WatermarkEncoder(alpha=args.alpha, pn_seed=args.seed)
    stego      = encoder.encode(img, wm)
    psnr_embed = psnr(img, stego)
    cv2.imwrite(os.path.join(out_dir, 'stego.jpg'), stego,
                [cv2.IMWRITE_JPEG_QUALITY, 100])

    # Imperceptibility figure
    diff_amp = np.clip(
        np.abs(img.astype(float) - stego.astype(float)).mean(axis=2) * 8,
        0, 255).astype(np.uint8)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), facecolor='white')
    axes[0].imshow(cv2.cvtColor(img,   cv2.COLOR_BGR2RGB))
    axes[0].set_title('Host (Asli)', fontsize=11, fontweight='bold', pad=8)
    axes[0].axis('off')
    axes[1].imshow(cv2.cvtColor(stego, cv2.COLOR_BGR2RGB))
    axes[1].set_title(f'Stego\nPSNR = {psnr_embed:.2f} dB',
                      fontsize=11, fontweight='bold', pad=8)
    axes[1].axis('off')
    im = axes[2].imshow(diff_amp, cmap='hot', vmin=0, vmax=80)
    axes[2].set_title('|Host - Stego| x8\n(heatmap)',
                      fontsize=11, fontweight='bold', pad=8)
    axes[2].axis('off')
    fig.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04,
                 label='intensitas selisih')
    fig.suptitle('Analisis Imperceptibility Watermark DWT-SS',
                 fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'imperceptibility.png'),
                dpi=150, bbox_inches='tight')
    plt.close()

    # Evaluasi robustness: re-encode ke berbagai QF JPEG
    decoder = WatermarkDecoder(alpha=args.alpha, pn_seed=args.seed)
    results = []
    wm_recs = []

    print(f"\n{'QF':>4} | {'PSNR':>8} | {'BER':>7} | {'NC':>7} | {'KB':>7} | Status")
    print("-" * 65)

    for qf in QF_LIST:
        _, enc     = cv2.imencode('.jpg', stego, [cv2.IMWRITE_JPEG_QUALITY, qf])
        size_kb    = len(enc) / 1024
        stego_jpeg = cv2.imdecode(enc, cv2.IMREAD_COLOR)

        wm_rec = decoder.decode(stego_jpeg)
        b = ber(wm, wm_rec)
        n = nc(wm, wm_rec)
        p = psnr(img, stego_jpeg)

        status = ('GAGAL' if b >= 10 or n < 0.5
                  else 'Terbaca, sedikit noise' if b > 2
                  else 'Terbaca sempurna')
        results.append({'QF': qf, 'PSNR': p, 'BER': b,
                        'NC': n, 'Size_KB': size_kb, 'Status': status})
        wm_recs.append(wm_rec)
        print(f"{qf:>4} | {p:>8.2f} | {b:>6.2f}% | {n:>7.4f} | "
              f"{size_kb:>6.1f} | {status}")

    qfs   = [r['QF']   for r in results]
    bers  = [r['BER']  for r in results]
    ncs   = [r['NC']   for r in results]
    psnrs = [r['PSNR'] for r in results]

    # Plot BER & NC
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), facecolor='white')
    bar_colors = ['#E53935' if b >= 10 else '#FB8C00' if b > 2 else '#43A047'
                  for b in bers]
    bars = ax1.bar(range(len(qfs)), bers, color=bar_colors,
                   edgecolor='white', linewidth=0.8)
    ax1.axhline(10, color='black', ls='--', lw=1.2, label='Threshold 10%')
    ax1.set_xticks(range(len(qfs)))
    ax1.set_xticklabels([str(q) for q in qfs])
    ax1.set_xlabel('JPEG Quality Factor (QF)', fontsize=11)
    ax1.set_ylabel('BER (%)', fontsize=11)
    ax1.set_title('Bit Error Rate per QF', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, 65)
    ax1.legend(fontsize=9)
    for bar, b in zip(bars, bers):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                 f'{b:.1f}%', ha='center', va='bottom', fontsize=7)

    ax2.fill_between(range(len(qfs)), ncs, 0.5,
                     where=[n >= 0.5 for n in ncs],
                     alpha=0.15, color='#1565C0', label='NC valid (>= 0.5)')
    ax2.fill_between(range(len(qfs)), ncs, 0.5,
                     where=[n < 0.5 for n in ncs],
                     alpha=0.15, color='#B71C1C', label='NC gagal (< 0.5)')
    ax2.plot(range(len(qfs)), ncs, 'o-', color='#1565C0', lw=2, ms=7)
    ax2.axhline(0.5,  color='black', ls='--', lw=1.2, label='Threshold NC=0.5')
    ax2.axhline(0.75, color='gray',  ls=':',  lw=1,   label='NC=0.75 (valid)')
    ax2.set_xticks(range(len(qfs)))
    ax2.set_xticklabels([str(q) for q in qfs])
    ax2.set_xlabel('JPEG Quality Factor (QF)', fontsize=11)
    ax2.set_ylabel('Normalized Correlation (NC)', fontsize=11)
    ax2.set_title('Normalized Correlation per QF', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 1.1)
    ax2.legend(fontsize=8)
    fig.suptitle('Robustness Watermark DWT-SS terhadap Kompresi JPEG',
                 fontsize=13, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'plot_ber_nc.png'),
                dpi=150, bbox_inches='tight')
    plt.close()

    # Plot PSNR
    fig, ax = plt.subplots(figsize=(9, 4), facecolor='white')
    ax.step(range(len(qfs)), psnrs, where='mid', color='#2E7D32', lw=2)
    ax.fill_between(range(len(qfs)), psnrs, 29, step='mid',
                    alpha=0.12, color='#2E7D32')
    ax.axhline(35, color='#F57F17', ls='--', lw=1.2, label='Batas visual 35 dB')
    ax.axhline(40, color='#1565C0', ls=':',  lw=1.2, label='Batas sangat baik 40 dB')
    for i, (q, p) in enumerate(zip(qfs, psnrs)):
        ax.annotate(f'{p:.1f}', (i, p), textcoords='offset points',
                    xytext=(0, 6), ha='center', fontsize=7.5, color='#1B5E20')
    ax.set_xticks(range(len(qfs)))
    ax.set_xticklabels([str(q) for q in qfs])
    ax.set_xlabel('JPEG Quality Factor (QF)', fontsize=11)
    ax.set_ylabel('PSNR (dB)', fontsize=11)
    ax.set_title('PSNR Host vs Stego setelah Kompresi JPEG',
                 fontsize=12, fontweight='bold')
    ax.set_ylim(28, 42)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'plot_psnr.png'),
                dpi=150, bbox_inches='tight')
    plt.close()

    # Grid watermark hasil ekstraksi
    fig, axes = plt.subplots(2, 5, figsize=(13, 5.5), facecolor='white')
    fig.suptitle('Watermark Hasil Ekstraksi pada Berbagai QF JPEG',
                 fontsize=12, fontweight='bold')
    for idx, (ax, qf, wm_rec) in enumerate(zip(axes.flat, QF_LIST, wm_recs)):
        r   = results[idx]
        col = ('#C62828' if r['Status'] == 'GAGAL'
               else '#E65100' if 'noise' in r['Status']
               else '#2E7D32')
        ax.imshow(wm_rec, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
        ax.set_title(f'QF = {qf}', fontsize=9, color=col,
                     fontweight='bold', pad=3)
        ax.set_xlabel(f"BER = {r['BER']:.1f}%", fontsize=8,
                      color=col, labelpad=3)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor(col); sp.set_linewidth(2)
    fig.tight_layout(pad=1.0, h_pad=1.5, w_pad=0.8)
    fig.savefig(os.path.join(out_dir, 'extracted_watermarks_grid.png'),
                dpi=130, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"\n[INFO] PSNR stego : {psnr_embed:.2f} dB")
    print(f"[INFO] Output     : {out_dir}/")


def main():
    parser = argparse.ArgumentParser(
        prog='dwt_watermark',
        description='DWT Spread Spectrum invisible watermark'
    )
    sub = parser.add_subparsers(dest='action')

    # encode — tidak ada -w karena watermark sudah hardcoded (citra biner 64x64)
    enc = sub.add_parser('encode', help='Sisipkan watermark ke foto')
    enc.add_argument('-i', '--input',   required=True,
                     help='Path foto input (JPEG/PNG)')
    enc.add_argument('-o', '--output',  default=None,
                     help='Path foto output (default: <input>_wm.jpg)')
    enc.add_argument('-a', '--alpha',   type=float, default=20.0,
                     help='Skala penyisipan (default: 20.0)')
    enc.add_argument('-s', '--seed',    type=int,   default=100,
                     help='PN seed (default: 100)')
    enc.add_argument('-v', '--verbose', action='store_true')

    # decode — tidak ada -l karena wm_size sudah tetap 64x64
    dec = sub.add_parser('decode', help='Ekstrak watermark dari foto')
    dec.add_argument('-i', '--input',   required=True,
                     help='Path foto stego')
    dec.add_argument('-o', '--output',  default=None,
                     help='Path output watermark PNG (default: <input>_wm_extracted.png)')
    dec.add_argument('-a', '--alpha',   type=float, default=20.0)
    dec.add_argument('-s', '--seed',    type=int,   default=100)
    dec.add_argument('-v', '--verbose', action='store_true')

    # evaluate — tidak ada -w, evaluasi pakai watermark biner bawaan
    ev = sub.add_parser('evaluate',
                        help='Evaluasi robustness watermark terhadap kompresi JPEG')
    ev.add_argument('-i', '--input',   required=True,
                    help='Path foto host')
    ev.add_argument('-o', '--output',  default=None,
                    help='Folder output (default: hasil_evaluasi)')
    ev.add_argument('-a', '--alpha',   type=float, default=20.0)
    ev.add_argument('-s', '--seed',    type=int,   default=100)

    args = parser.parse_args()

    if   args.action == 'encode':   cmd_encode(args)
    elif args.action == 'decode':   cmd_decode(args)
    elif args.action == 'evaluate': cmd_evaluate(args)
    else: parser.print_help()


if __name__ == '__main__':
    main()

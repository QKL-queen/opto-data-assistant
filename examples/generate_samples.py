# -*- coding: utf-8 -*-
"""示例实验数据生成脚本

基于真实物理参数生成三组模拟实验数据（带随机测量误差），
便于直接体验「数据拟合」与「报告生成」功能。

运行方式：python examples/generate_samples.py
输出：examples/ 下的三个 CSV 文件（UTF-8 BOM 编码，Excel 可直接打开）

数据来源说明：
1. 杨氏双缝干涉 —— 钠黄光 λ=589.3 nm，缝屏距 L=1.0 m，缝间距 d=0.5 mm
   理论条纹间距 Δx = λL/d = 1.1786 mm
2. 单缝衍射     —— He-Ne 激光 λ=632.8 nm，缝宽 a=0.1 mm，缝屏距 L=1.0 m
   暗纹间距 = λL/a = 6.328 mm
3. 光电效应     —— 截止频率ν0=4.837e14 Hz，逸出功 W=2.0 eV，h/e=4.1357e-15 V·s
   遏止电压 U = (h/e)·ν - W/e，斜率理论值 0.4136 V/(10^14 Hz)
"""

import csv
import os
import random

random.seed(20261005)  # 固定随机种子，保证每次生成的数据一致


def write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"已生成：{path}（{len(rows)} 行）")


def gen_young():
    """杨氏双缝干涉：条纹位置 x 与级次 m 的线性关系。"""
    lam, L, d = 589.3, 1.0, 0.5          # nm, m, mm
    dx = lam * L * 1e-3 / d              # mm ≈ 1.1786
    rows = []
    for m in range(1, 11):
        x = m * dx + random.gauss(0, 0.02)
        rows.append([m, round(x, 4)])
    write_csv(os.path.join(BASE, "杨氏双缝干涉.csv"),
              ["级次 m", "条纹位置 x/mm"], rows)
    print(f"  理论条纹间距 Δx = {dx:.4f} mm（拟合斜率应接近该值）")


def gen_single_slit():
    """单缝衍射：暗纹位置与级次的线性关系。"""
    lam, a, L = 632.8, 0.1, 1.0          # nm, mm, m
    step = lam * 1e-9 * L / (a * 1e-3) * 1000  # mm ≈ 6.328
    rows = []
    for m in range(1, 9):
        x = m * step + random.gauss(0, 0.08)
        rows.append([m, round(x, 4)])
    write_csv(os.path.join(BASE, "单缝衍射.csv"),
              ["暗纹级次 m", "暗纹位置 x/mm"], rows)
    print(f"  理论暗纹间距 = {step:.4f} mm（拟合斜率应接近该值）")


def gen_photoelectric():
    """光电效应：遏止电压 U 与入射光频率 ν 的线性关系。"""
    h_e = 4.1357e-15                      # h/e，V·s
    W_eV = 2.0                            # 逸出功，eV
    rows = []
    for nu_14 in [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]:
        U = h_e * nu_14 * 1e14 - W_eV
        U = U + random.gauss(0, 0.008)
        rows.append([nu_14, round(U, 4)])
    write_csv(os.path.join(BASE, "光电效应.csv"),
              ["频率 ν/(10^14 Hz)", "遏止电压 U/V"], rows)
    print(f"  理论斜率 = {h_e * 1e14:.4f} V/(10^14 Hz)，截距 = -{W_eV} V")


BASE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    gen_young()
    gen_single_slit()
    gen_photoelectric()
    print("示例数据生成完毕。")

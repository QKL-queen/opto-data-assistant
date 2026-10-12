# -*- coding: utf-8 -*-
"""一次性验证脚本：用示例 CSV 数据完整跑一遍拟合，并输出演示图。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.abspath(__file__))

from core.fitting import parse_xy, fit_data, plot_fit  # noqa: E402

FILES = ["杨氏双缝干涉.csv", "单缝衍射.csv", "光电效应.csv"]
for name in FILES:
    path = os.path.join(BASE, "examples", name)
    with open(path, encoding="utf-8-sig") as fp:
        x, y, dy = parse_xy(fp.read())
    res = fit_data(x, y, kind="linear")
    print("=" * 50)
    print(f"文件：{name}")
    print(res["text"])
    fig = plot_fit(x, y, res["y_fit"], res["text"],
                   xlabel="级次 m", ylabel="位置/mm", title=name.replace(".csv", ""))
    out = os.path.join(BASE, "docs", "demo_" + name.replace(".csv", ".png"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    print(f"演示图：{out}")

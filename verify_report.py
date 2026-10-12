# -*- coding: utf-8 -*-
"""一次性验证：用示例数据走完整报告生成链路，并回读校验 docx 内容。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.abspath(__file__))

from core.fitting import parse_xy, fit_data, plot_fit  # noqa: E402
from core.report import build_report  # noqa: E402
from core.uncertainty import parse_values, direct_uncertainty  # noqa: E402

with open(os.path.join(BASE, "examples", "杨氏双缝干涉.csv"), encoding="utf-8-sig") as fp:
    x, y, dy = parse_xy(fp.read())
res = fit_data(x, y, kind="linear")

fig = plot_fit(x, y, res["y_fit"], res["text"], xlabel="级次 m", ylabel="条纹位置/mm")
fig_path = os.path.join(BASE, "docs", "report_demo_fig.png")
fig.savefig(fig_path, bbox_inches="tight")

_, unc_text = direct_uncertainty([1.18, 1.17, 1.19, 1.18, 1.16], delta_instrument=0.02)

meta = {
    "实验名称": "杨氏双缝干涉实验", "姓名": "张三", "学号": "2026000000",
    "班级": "光电2401", "日期": "2026-10-05", "指导教师": "李老师",
    "实验目的": "观察双缝干涉现象，测量钠黄光波长。",
    "实验原理": "杨氏双缝干涉条纹间距 Δx = λL/d，测出 Δx、L、d 后由 λ = Δx·d/L 计算波长。",
    "实验仪器": "钠光灯、双缝、测微目镜、米尺。",
}
out = build_report(meta, data_table=(["级次 m", "条纹位置 x/mm"], list(zip(x, y))),
                   fit_text=res["text"], fit_fig_path=fig_path,
                   uncertainty_text=unc_text,
                   conclusion=f"拟合得到条纹间距 Δx = {res['params'][0]:.4f} mm，"
                              f"代入 λ = Δx·d/L 得 λ ≈ {res['params'][0] * 0.5 / 1.0 * 1e6:.1f} nm，"
                              "与钠黄光标准值 589.3 nm 相符。")
print("报告已生成：", out)
print("文件大小：", os.path.getsize(out), "字节")

# 回读校验
from docx import Document  # noqa: E402

doc = Document(out)
paras = [p.text for p in doc.paragraphs if p.text.strip()]
tables = doc.tables
has_img = len(doc.inline_shapes)
print("段落数：", len(paras))
print("表格数：", len(tables))
print("图片数：", has_img)
for key in ["杨氏双缝干涉实验", "一、实验目的", "五、数据处理", "七、结论"]:
    assert any(key in p for p in paras), f"缺少章节 {key}"
    print("包含章节：", key)
assert any(len(t.rows) > 2 for t in tables), "数据表异常（信息表为 2 行，数据表应多于 2 行）"
assert has_img >= 1, "缺少拟合图"
print("[PASS] docx 报告内容完整（章节/表格/图片均在）")

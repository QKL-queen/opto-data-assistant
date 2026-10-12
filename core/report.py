# -*- coding: utf-8 -*-
"""Word 实验报告生成模块

把「基本信息 + 实验数据 + 拟合结果 + 误差分析 + 结论」一键整理为
可直接提交的标准实验报告（.docx 格式），结构为：

    实验名称
    姓名/学号/班级/日期/指导教师
    一、实验目的
    二、实验原理
    三、实验仪器与装置
    四、实验数据
    五、数据处理（拟合结果 + 拟合图 + 不确定度）
    六、结果与分析
    七、结论

依赖：python-docx。中文字体通过 eastAsia 属性设置为宋体/黑体。
"""

import os
import re
import tempfile
from datetime import date

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


def _set_run_font(run, cn_font="宋体", en_font="Times New Roman", size=12, bold=False, color=None):
    """设置 run 的中英文字体。"""
    run.font.name = en_font
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), cn_font)


def _add_para(doc, text, cn_font="宋体", size=12, bold=False, align=None,
              indent=False, space_after=6):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Pt(size * 2)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    _set_run_font(run, cn_font=cn_font, size=size, bold=bold)
    return p


def _add_heading(doc, text):
    """章节标题：黑体小三加粗，左侧编号由调用方传入。"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    _set_run_font(run, cn_font="黑体", size=15, bold=True)
    return p


def build_report(meta, data_table=None, fit_text="", fit_fig_path=None,
                 uncertainty_text="", conclusion="", out_path=None):
    """生成实验报告 .docx。

    参数：
        meta             基本信息字典：
                         {实验名称, 姓名, 学号, 班级, 日期, 指导教师,
                          实验目的, 实验原理, 实验仪器, 备注}
        data_table       [(表头列表, 行列表)] 或 None
        fit_text        数据处理拟合结果文本（纯文本，\n 分隔）
        fit_fig_path    拟合图片路径（PNG），可选
        uncertainty_text 不确定度分析文本，可选
        conclusion      结果与分析/结论文本，可选
        out_path        输出路径；None 时保存到临时目录

    返回：生成的 docx 文件路径。
    """
    doc = Document()

    # 页面边距
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.8)

    # ---- 标题 ----
    title = meta.get("实验名称") or "实验报告"
    _add_para(doc, title, cn_font="黑体", size=18, bold=True,
              align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    _add_para(doc, "实验报告", cn_font="宋体", size=14,
              align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    # ---- 信息表 ----
    info_rows = [
        ("姓名", meta.get("姓名", "")), ("学号", meta.get("学号", "")),
        ("班级", meta.get("班级", "")), ("日期", meta.get("日期", str(date.today()))),
        ("指导教师", meta.get("指导教师", "")),
    ]
    table = doc.add_table(rows=2, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate(info_rows):
        cell_k = table.cell(0, i)
        cell_v = table.cell(1, i)
        cell_k.text = ""
        cell_v.text = ""
        p_k = cell_k.paragraphs[0]
        p_v = cell_v.paragraphs[0]
        p_k.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_v.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rk = p_k.add_run(k)
        rv = p_v.add_run(v)
        _set_run_font(rk, size=11, bold=True)
        _set_run_font(rv, size=11)

    # ---- 各章节 ----
    _add_heading(doc, "一、实验目的")
    _add_para(doc, meta.get("实验目的") or "（待填写：本实验要验证的规律 / 要测量的物理量）",
              indent=True)

    _add_heading(doc, "二、实验原理")
    _add_para(doc, meta.get("实验原理") or "（待填写：主要公式、物理模型与测量方法）",
              indent=True)

    _add_heading(doc, "三、实验仪器与装置")
    _add_para(doc, meta.get("实验仪器") or "（待填写：仪器名称、型号、精度等级）",
              indent=True)

    _add_heading(doc, "四、实验数据")
    if data_table and data_table[1]:
        headers, rows = data_table
        t = doc.add_table(rows=1 + len(rows), cols=len(headers))
        t.style = "Table Grid"
        for j, h in enumerate(headers):
            cell = t.cell(0, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(h))
            _set_run_font(run, size=11, bold=True)
        for i, row in enumerate(rows, start=1):
            for j, val in enumerate(row):
                cell = t.cell(i, j)
                cell.text = ""
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(_fmt_num(val))
                _set_run_font(run, size=11)
    else:
        _add_para(doc, "（待填写：实验数据表格）", indent=True)

    _add_heading(doc, "五、数据处理")
    if fit_text:
        for line in fit_text.strip().splitlines():
            if line.strip():
                _add_para(doc, line, indent=True, space_after=2)
    else:
        _add_para(doc, "（待填写：计算过程与拟合结果）", indent=True)

    if fit_fig_path and os.path.exists(fit_fig_path):
        _add_para(doc, "拟合曲线图：", indent=True, space_after=2)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(fit_fig_path, width=Cm(13.0))

    if uncertainty_text:
        _add_para(doc, "不确定度分析：", bold=False, space_after=2)
        for line in uncertainty_text.strip().splitlines():
            if line.strip():
                _add_para(doc, line, indent=True, space_after=2)

    _add_heading(doc, "六、结果与分析")
    _add_para(doc, conclusion or "（待填写：结果与理论值的比较、误差来源分析）",
              indent=True)

    _add_heading(doc, "七、结论")
    _add_para(doc, "（待填写：本实验的最终结论与收获）", indent=True)

    # ---- 保存 ----
    if out_path is None:
        out_path = os.path.join(tempfile.gettempdir(),
                                f"实验报告_{re.sub(r'[\\/:*?\"<>|]', '_', title)}_{date.today().strftime('%Y%m%d')}.docx")
    doc.save(out_path)
    return out_path


def _fmt_num(v):
    """数字格式化：去掉多余小数位。"""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(f - round(f)) < 1e-10:
        return str(int(round(f)))
    return f"{f:.6g}"


if __name__ == "__main__":
    # 简单自检：生成一个示例报告
    p = build_report(
        {"实验名称": "杨氏双缝干涉实验", "姓名": "张三", "学号": "2026000000",
         "班级": "光电2401", "日期": "2026-10-05", "指导教师": "李老师",
         "实验目的": "观察干涉条纹，测量钠黄光波长。",
         "实验原理": "杨氏双缝干涉条纹间距 Δx = λL/d，测出 Δx、L、d 即可算得 λ。",
         "实验仪器": "钠光灯、双缝、测微目镜、米尺。"},
        data_table=(["级次 m", "位置 x/mm"], [[1, 1.18], [2, 2.36], [3, 3.54]]),
        fit_text="斜率 k = 1.1786 mm，R² = 0.9999",
        conclusion="测得波长 λ = 589.3 nm，与钠黄光标准值 589.3 nm 相符。",
    )
    print("报告已生成：", p)

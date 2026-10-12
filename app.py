# -*- coding: utf-8 -*-
"""光电实验数据处理助手 —— 主程序（Gradio 图形界面）

运行方式：
    python app.py
然后浏览器会自动打开 http://127.0.0.1:7860

功能页：
    1. 公式计算器     —— 14 个光电基础公式，任意缺一项自动求解
    2. 数据拟合       —— 线性 / 多项式 / 自定义函数拟合 + 绘图
    3. 误差分析       —— A/B 类不确定度评定 + 误差传递
    4. 报告生成       —— 一键生成 Word 实验报告草稿
    5. 使用帮助       —— 快速上手说明

本项目依赖 core/ 下的四个算法模块，修改功能时建议先看
docs/设计制作流程与修缮指南.md。
"""

import os
import tempfile

import gradio as gr

from core.formulas import FORMULA_NAMES, get_formula
from core.fitting import parse_xy, fit_data, plot_fit
from core.uncertainty import parse_values, direct_uncertainty, parse_vars_text, error_propagation
from core.report import build_report

APP_TITLE = "光电实验数据处理助手"
APP_SUBTITLE = "面向光电专业本科实验：公式计算 · 数据拟合 · 不确定度评定 · 实验报告生成"

# 每个公式给出一组示例输入，便于快速体验
FORMULA_EXAMPLES = {
    "薄透镜成像公式": "示例：物距 u = 20，像距 v = 30 → 焦距 f = 12 cm",
    "折射定律（斯涅耳定律）": "示例：n1 = 1.0，θ1 = 30，n2 = 1.5 → θ2 ≈ 19.47°",
    "光栅方程": "示例：d = 1.0 μm，m = 1，λ = 500 nm → θ = 30°",
    "杨氏双缝干涉条纹间距": "示例：λ = 589.3 nm，L = 1.0 m，d = 0.5 mm → Δx = 1.179 mm",
    "单缝衍射暗纹条件": "示例：a = 0.1 mm，m = 1，λ = 632.8 nm → θ ≈ 0.363°",
    "光子能量": "示例：λ = 500 nm → E = 2.48 eV",
    "波长-频率关系": "示例：λ = 500 nm → ν = 599.6 THz",
    "瑞利判据（角分辨率）": "示例：λ = 550 nm，D = 100 mm → θ ≈ 1.39″",
    "数值孔径": "示例：n = 1.0，α = 30° → NA = 0.5",
    "布儒斯特角": "示例：n1 = 1.0，n2 = 1.5 → θB ≈ 56.31°",
    "全反射临界角": "示例：n1 = 1.5，n2 = 1.0 → θC ≈ 41.81°",
    "密贴透镜组等效焦距": "示例：f1 = 10 cm，f2 = 15 cm → f = 6 cm",
    "薄透镜横向放大率": "示例：u = 20 cm，v = 40 cm → M = 2",
    "朗伯-比尔吸收定律": "示例：I0 = 1.0，μ = 0.5 /cm，x = 2 cm → I = 0.3679",
}

MAX_SYMBOLS = 4  # 单条公式最多物理量个数（用于预留输入框）


# ============================================================
# 页面 1：公式计算器
# ============================================================
def formula_guide_html(name):
    """生成公式说明 Markdown。"""
    f = get_formula(name)
    lines = [f"### {f['name']}", "", f"**公式：** `{f['formula']}`", "", "**物理量：**"]
    for key, cn, unit in f["symbols"]:
        lines.append(f"- {cn}（单位：{unit}）")
    lines.append("")
    lines.append("**用法：** 留空**一个**待求物理量，其余全部填数值，点「计算」。")
    ex = FORMULA_EXAMPLES.get(name)
    if ex:
        lines.append("")
        lines.append(ex)
    return "\n".join(lines)


def compute_formula(name, *values):
    """点击「计算」：收集 4 个输入框，恰好 1 个为空则求解。"""
    f = get_formula(name)
    n_syms = len(f["symbols"])
    kwargs = {}
    blank = []
    for i, (key, cn, unit) in enumerate(f["symbols"]):
        v = values[i]
        if v is None or (isinstance(v, str) and not v.strip()):
            blank.append(key)
        else:
            kwargs[key] = float(v)
    if not blank:
        return "请留空一个待求物理量（其余全部填写数值）。"
    if len(blank) > 1:
        return "一次只能求一个未知量：请只留空一个输入框。"
    try:
        filled, extras = f["solve"](**kwargs)
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        return f"❌ 计算失败：{e}"

    lines = [f"### {f['name']} 计算结果", ""]
    for key, cn, unit in f["symbols"]:
        v = filled.get(key)
        if v is None:
            continue
        text = f"- **{cn}** = {v:.6g} {unit}".rstrip()
        lines.append(text)
    for extra in extras:
        lines.append(f"- {extra}")
    lines.append("")
    lines.append("> 说明：输入值已按公式内单位自动换算。")
    return "\n".join(lines)


def build_formula_tab():
    with gr.Column():
        gr.Markdown("### 光学公式计算器\n选择公式 → 填写已知量 → 留空待求量 → 计算")
        formula_dd = gr.Dropdown(choices=FORMULA_NAMES, value=FORMULA_NAMES[0],
                                 label="选择公式")
        guide_md = gr.Markdown(formula_guide_html(FORMULA_NAMES[0]))
        with gr.Row():
            inputs = []
            for i in range(MAX_SYMBOLS):
                inp = gr.Number(value=None, label=f"物理量 {i + 1}", visible=(i < 2))
                inputs.append(inp)
        calc_btn = gr.Button("计算", variant="primary")
        result_md = gr.Markdown("")

    def on_formula_change(name):
        f = get_formula(name)
        updates = []
        for i in range(MAX_SYMBOLS):
            if i < len(f["symbols"]):
                key, cn, unit = f["symbols"][i]
                updates.append(gr.update(visible=True, label=f"{cn}（{unit}）", value=None))
            else:
                updates.append(gr.update(visible=False, label="", value=None))
        return [formula_guide_html(name)] + updates

    formula_dd.change(on_formula_change, inputs=[formula_dd],
                      outputs=[guide_md] + inputs)
    calc_btn.click(compute_formula, inputs=[formula_dd] + inputs, outputs=[result_md])
    return formula_dd, inputs, result_md


# ============================================================
# 页面 2：数据拟合
# ============================================================
def do_fit(data_text, kind, degree, expr, p0, xlabel, ylabel):
    """执行拟合并返回 (结果文本, 图, 图片下载路径)。"""
    if not data_text or not data_text.strip():
        return "请先粘贴数据或导入文件。", None, None
    try:
        x, y, dy = parse_xy(data_text)
    except ValueError as e:
        return f"❌ 数据解析失败：{e}", None, None
    try:
        res = fit_data(x, y, kind=kind, degree=int(degree), expr=expr, p0_text=p0)
    except Exception as e:
        return f"❌ 拟合失败：{e}", None, None
    fig = plot_fit(x, y, res["y_fit"], res["text"], xlabel=xlabel or "x", ylabel=ylabel or "y")
    # 保存图片用于下载
    fig_path = os.path.join(tempfile.gettempdir(), "拟合结果.png")
    fig.savefig(fig_path, bbox_inches="tight")
    return res["text"], fig, fig_path


def load_file_to_text(filepath):
    """把上传的 CSV 文件内容填入输入框。"""
    if not filepath:
        return "未选择文件。"
    try:
        with open(filepath, "r", encoding="utf-8-sig") as fp:
            return fp.read()
    except (UnicodeDecodeError, OSError):
        try:
            with open(filepath, "r", encoding="gbk") as fp:
                return fp.read()
        except Exception as e:
            return f"❌ 读取文件失败：{e}"


def build_fit_tab():
    with gr.Column():
        gr.Markdown("### 实验数据拟合\n每行一组：`x, y` 或 `x, y, dy`（dy 为误差，画误差棒）。支持逗号/空格/制表符分隔。")
        with gr.Row():
            with gr.Column(scale=1):
                data_tb = gr.Textbox(label="粘贴数据（每行 x, y 或 x, y, dy）",
                                     lines=10, placeholder="示例：\n1, 2.1\n2, 4.0\n3, 5.9\n4, 8.2\n5, 10.1")
                file_in = gr.File(label="或上传 CSV 文件", type="filepath")
                load_btn = gr.Button("读取文件内容到上方输入框")
            with gr.Column(scale=1):
                kind_rd = gr.Radio(
                    choices=[("线性拟合 y = kx + b", "linear"), ("多项式拟合", "poly"), ("自定义函数拟合", "custom")],
                    value="linear", label="拟合方式")
                degree_sl = gr.Slider(1, 6, value=2, step=1, label="多项式阶数", visible=False)
                expr_tb = gr.Textbox(label="自定义函数表达式（参数自动识别）", value="a*exp(-b*x)+c",
                                     placeholder="示例：a*exp(-b*x)+c", visible=False)
                p0_tb = gr.Textbox(label="参数初值（逗号分隔，可留空自动取 1）", value="",
                                   placeholder="示例：1, 0.01, 0", visible=False)
                xlabel_tb = gr.Textbox(label="x 轴名称", value="")
                ylabel_tb = gr.Textbox(label="y 轴名称", value="")
                fit_btn = gr.Button("开始拟合", variant="primary")

        result_md = gr.Markdown("")
        plot_out = gr.Plot(label="拟合曲线图")
        fig_file = gr.File(label="下载拟合图（PNG）")

    def on_kind_change(kind):
        return (gr.update(visible=(kind == "poly")),
                gr.update(visible=(kind == "custom")),
                gr.update(visible=(kind == "custom")))

    kind_rd.change(on_kind_change, inputs=[kind_rd], outputs=[degree_sl, expr_tb, p0_tb])
    load_btn.click(load_file_to_text, inputs=[file_in], outputs=[data_tb])
    fit_btn.click(do_fit,
                  inputs=[data_tb, kind_rd, degree_sl, expr_tb, p0_tb, xlabel_tb, ylabel_tb],
                  outputs=[result_md, plot_out, fig_file])
    return data_tb


# ============================================================
# 页面 3：误差分析
# ============================================================
def do_direct_uncertainty(data_text, delta, use_t, k):
    if not data_text or not data_text.strip():
        return "请粘贴测量数据（每行一个数值）。"
    try:
        values = parse_values(data_text)
        result, text = direct_uncertainty(values, delta_instrument=float(delta or 0),
                                          use_t=bool(use_t), k=float(k or 2))
    except (ValueError, ZeroDivisionError) as e:
        return f"❌ 计算失败：{e}"
    lines = text.splitlines()
    out = ["### 直接测量不确定度评定", ""]
    for line in lines:
        out.append(f"- {line}")
    out.append("")
    out.append(f"**结果表示：** x = x̄ ± U = {result['mean']:.6g} ± {result['U']:.6g}")
    return "\n".join(out)


def do_propagation(expr, var_text):
    if not expr or not expr.strip():
        return "请输入表达式，例如：u*v/(u+v)"
    try:
        var_data = parse_vars_text(var_text)
        y, uy, partials, text = error_propagation(expr, var_data)
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        return f"❌ 计算失败：{e}"
    out = ["### 间接测量误差传递", ""]
    for line in text.splitlines():
        out.append(f"- {line}")
    return "\n".join(out)


def build_uncertainty_tab():
    with gr.Tab("直接测量不确定度"):
        gr.Markdown("按大学物理实验流程：平均值 → 标准偏差 → A 类（t 因子）→ B 类（Δ/√3）→ 合成 → 扩展。")
        with gr.Row():
            data_tb = gr.Textbox(label="测量数据（每行一个数值）", lines=6,
                                 placeholder="示例：\n10.02\n10.01\n10.03\n10.00\n10.02")
            with gr.Column():
                delta_num = gr.Number(value=0.02, label="仪器允差 Δ（不填则 B 类为 0）")
                use_t_cb = gr.Checkbox(value=True, label="A 类使用 t 因子（95%）")
                k_num = gr.Number(value=2, label="扩展不确定度因子 k")
                unc_btn = gr.Button("评定不确定度", variant="primary")
        unc_md = gr.Markdown("")
    with gr.Tab("误差传递"):
        gr.Markdown("对任意函数 y = f(x1, x2, ...) 计算误差传递。变量格式每行一个：`变量名 = 数值, 不确定度`")
        with gr.Row():
            expr_tb = gr.Textbox(label="表达式（支持 exp/log/sqrt/sin/cos/tan/pi 等）",
                                 value="u*v/(u+v)", placeholder="示例：u*v/(u+v)")
            var_tb = gr.Textbox(label="变量数值与不确定度", lines=6,
                                placeholder="示例：\nu = 12.3, 0.2\nv = 30.0, 0.4")
        prop_btn = gr.Button("计算误差传递", variant="primary")
        prop_md = gr.Markdown("")
    unc_btn.click(do_direct_uncertainty, inputs=[data_tb, delta_num, use_t_cb, k_num], outputs=[unc_md])
    prop_btn.click(do_propagation, inputs=[expr_tb, var_tb], outputs=[prop_md])
    return None


# ============================================================
# 页面 4：报告生成
# ============================================================
def gen_report(name, student, sid, cls, date_str, teacher,
               purpose, principle, instruments, conclusion,
               data_text, kind, degree, expr, p0,
               xlabel, ylabel,
               repeat_text, delta):
    """一键生成 Word 实验报告草稿。"""
    if not name or not name.strip():
        return "请填写实验名称。", None
    if not data_text or not data_text.strip():
        return "请粘贴实验数据（x, y 每行一组）。", None
    try:
        x, y, dy = parse_xy(data_text)
        res = fit_data(x, y, kind=kind, degree=int(degree), expr=expr, p0_text=p0)
    except Exception as e:
        return f"❌ 数据处理失败：{e}", None

    # 拟合图
    fig = plot_fit(x, y, res["y_fit"], res["text"],
                   xlabel=xlabel or "x", ylabel=ylabel or "y",
                   title=f"{name} 拟合结果")
    fig_path = os.path.join(tempfile.gettempdir(), f"报告图_{abs(hash(name))}.png")
    fig.savefig(fig_path, bbox_inches="tight")

    # 不确定度（可选）
    unc_text = ""
    if repeat_text and repeat_text.strip():
        try:
            values = parse_values(repeat_text)
            _, unc_text = direct_uncertainty(values, delta_instrument=float(delta or 0))
        except Exception as e:
            unc_text = f"（不确定度分析失败：{e}）"

    if not conclusion or not conclusion.strip():
        conclusion = (
            f"本实验采用{res['kind']}方式处理数据，拟合结果如下：\n{res['text']}\n"
            "（请补充：与理论值/标准值的比较及误差来源分析。）"
        )

    meta = {
        "实验名称": name.strip(), "姓名": student.strip(), "学号": sid.strip(),
        "班级": cls.strip(), "日期": date_str.strip() or None, "指导教师": teacher.strip(),
        "实验目的": purpose, "实验原理": principle, "实验仪器": instruments,
    }
    data_table = (["x", "y"], list(zip(x, y)))
    out_path = build_report(meta, data_table=data_table, fit_text=res["text"],
                            fit_fig_path=fig_path, uncertainty_text=unc_text,
                            conclusion=conclusion)
    preview = [
        f"### 报告预览：{name}",
        f"- 姓名：{student or '（未填）'}　学号：{sid or '（未填）'}　班级：{cls or '（未填）'}",
        f"- 拟合方式：{res['kind']}，R² = {res['r2']:.4f}",
        f"- 数据点数：{len(x)}",
        f"- 报告文件：{os.path.basename(out_path)}",
    ]
    return "\n".join(preview), out_path


def build_report_tab():
    with gr.Column():
        gr.Markdown("### 实验报告生成\n填写基本信息与实验数据，一键生成可直接编辑的 Word 报告草稿。")
        with gr.Accordion("基本信息", open=True):
            with gr.Row():
                name_tb = gr.Textbox(label="实验名称", value="杨氏双缝干涉实验")
                student_tb = gr.Textbox(label="姓名", value="")
                sid_tb = gr.Textbox(label="学号", value="")
            with gr.Row():
                cls_tb = gr.Textbox(label="班级", value="")
                date_tb = gr.Textbox(label="日期", value="")
                teacher_tb = gr.Textbox(label="指导教师", value="")
        with gr.Accordion("实验内容（可留空，生成后用 Word 补充）", open=False):
            purpose_tb = gr.Textbox(label="一、实验目的", lines=2)
            principle_tb = gr.Textbox(label="二、实验原理", lines=3)
            instruments_tb = gr.Textbox(label="三、实验仪器与装置", lines=2)
            conclusion_tb = gr.Textbox(label="六、结果与分析（留空则自动生成草稿）", lines=3)

        with gr.Accordion("实验数据与拟合", open=True):
            rep_data_tb = gr.Textbox(label="实验数据（每行 x, y 或 x, y, dy）", lines=6,
                                     placeholder="示例：\n1, 2.1\n2, 4.0\n3, 5.9")
            with gr.Row():
                rep_kind = gr.Radio(choices=[("线性", "linear"), ("多项式", "poly"), ("自定义", "custom")],
                                    value="linear", label="拟合方式")
                rep_degree = gr.Slider(1, 6, value=2, step=1, label="多项式阶数", visible=False)
                rep_expr = gr.Textbox(label="自定义表达式", value="a*exp(-b*x)+c", visible=False)
                rep_p0 = gr.Textbox(label="参数初值", value="", visible=False)
            rep_xlabel = gr.Textbox(label="x 轴名称（图）", value="x")
            rep_ylabel = gr.Textbox(label="y 轴名称（图）", value="y")
            rep_repeat_tb = gr.Textbox(label="（可选）重复测量数据：用于不确定度分析，每行一个", lines=3)
            rep_delta = gr.Number(value=0.02, label="（可选）仪器允差 Δ")

        gen_btn = gr.Button("生成实验报告（Word）", variant="primary")
        rep_preview = gr.Markdown("")
        rep_file = gr.File(label="下载报告（.docx）")

    def on_kind_change(kind):
        return (gr.update(visible=(kind == "poly")),
                gr.update(visible=(kind == "custom")),
                gr.update(visible=(kind == "custom")))

    rep_kind.change(on_kind_change, inputs=[rep_kind], outputs=[rep_degree, rep_expr, rep_p0])
    gen_btn.click(gen_report,
                  inputs=[name_tb, student_tb, sid_tb, cls_tb, date_tb, teacher_tb,
                          purpose_tb, principle_tb, instruments_tb, conclusion_tb,
                          rep_data_tb, rep_kind, rep_degree, rep_expr, rep_p0,
                          rep_xlabel, rep_ylabel,
                          rep_repeat_tb, rep_delta],
                  outputs=[rep_preview, rep_file])
    return None


# ============================================================
# 主程序
# ============================================================
HELP_MD = """## 快速上手

### 1. 公式计算器
选择公式 → 填已知量 → **留空一个待求量** → 点「计算」。
例如薄透镜：u = 20，v = 30，留空 f，得到 f = 12 cm。

### 2. 数据拟合
每行一组数据：`x, y` 或 `x, y, dy`（dy 画误差棒）。
- 线性拟合：直接出斜率 k、截距 b、各自不确定度与 R²；
- 多项式拟合：选阶数；
- 自定义拟合：写 Python 风格表达式，参数自动识别，如 `a*exp(-b*x)+c`。

### 3. 误差分析
- 直接测量：粘贴多次测量值 + 仪器允差 → 得到 x̄ ± U；
- 误差传递：输入表达式与各变量（数值, 不确定度）→ 自动求偏导合成。

### 4. 报告生成
填基本信息 → 贴数据 → 选拟合方式 → 点「生成实验报告」→ 下载 .docx。

### 示例数据
在 `examples/` 目录下有三个可直接导入的示例：
- `杨氏双缝干涉.csv`（线性拟合 → 条纹间距）
- `单缝衍射.csv`（线性拟合 → 暗纹间距）
- `光电效应.csv`（线性拟合 → 斜率 = h/e，截距 = 逸出功）

详细说明见项目根目录 `README.md`。
"""


def create_demo():
    """构建 Gradio 界面对象（供 main 启动，也便于自动化测试）。

    说明：Gradio 6 起 theme 参数移到 launch() 中，这里不传。
    """
    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown(f"# {APP_TITLE}\n{APP_SUBTITLE}")
        with gr.Tabs():
            with gr.Tab("公式计算器"):
                build_formula_tab()
            with gr.Tab("数据拟合"):
                build_fit_tab()
            with gr.Tab("误差分析"):
                build_uncertainty_tab()
            with gr.Tab("报告生成"):
                build_report_tab()
            with gr.Tab("使用帮助"):
                gr.Markdown(HELP_MD)
    return demo


def main():
    demo = create_demo()
    demo.launch(server_name="127.0.0.1", server_port=7860,
                inbrowser=True, show_error=True, theme=gr.themes.Soft())


if __name__ == "__main__":
    main()

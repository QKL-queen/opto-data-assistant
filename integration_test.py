# -*- coding: utf-8 -*-
"""集成测试：直接调用 app.py 的界面处理函数，代入真实数据模拟页面点击。

覆盖：公式计算（14 式全未知量方向）、数据拟合（三种方式+CSV导入+异常行）、
不确定度（A/B 类、误差传递）、报告生成（三种拟合方式+回读 docx）。

运行方式：venv\\Scripts\\python.exe integration_test.py
"""
import math
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.abspath(__file__))

PASSED = 0
FAILED = 0


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name}  {detail}")


def extract_value(text, cn_name):
    """从计算结果文本中按中文物理量名提取数值。"""
    for line in text.splitlines():
        if cn_name in line and "=" in line:
            val = line.split("=", 1)[1].strip().split()[0]
            try:
                return float(val)
            except ValueError:
                return None
    return None


# ============ 1. 公式计算器（compute_formula 全流程） ============
def test_formula_ui():
    print("[1/6] 公式计算器（界面层 compute_formula）")
    from app import compute_formula
    from core.formulas import get_formula

    def symbol_cn(formula_name, key):
        for k, cn, _ in get_formula(formula_name)["symbols"]:
            if k == key:
                return cn
        return None

    cases = [
        # (公式名, 输入(按 symbols 顺序，None=待求), 期望键, 期望值, 容差)
        ("薄透镜成像公式", (None, 20, 30), "f", 12.0, 1e-6),
        ("薄透镜成像公式", (12, None, 30), "u", 20.0, 1e-6),
        ("薄透镜成像公式", (12, 20, None), "v", 30.0, 1e-6),
        ("折射定律（斯涅耳定律）", (1.0, 30.0, 1.5, None), "theta2", 19.47122063449069, 1e-3),
        ("折射定律（斯涅耳定律）", (1.0, 30.0, None, 19.47122063449069), "n2", 1.5, 1e-6),
        ("折射定律（斯涅耳定律）", (None, 30.0, 1.5, 19.47122063449069), "n1", 1.0, 1e-6),
        ("折射定律（斯涅耳定律）", (1.0, None, 1.5, 19.47122063449069), "theta1", 30.0, 1e-6),
        ("光栅方程", (1.0, None, 1, 500.0), "theta", 30.0, 1e-6),
        ("光栅方程", (None, 30.0, 1, 500.0), "d", 1.0, 1e-6),
        ("光栅方程", (1.0, 30.0, 1, None), "lam", 500.0, 1e-6),
        ("光栅方程", (1.0, 30.0, None, 500.0), "m", 1.0, 1e-6),
        ("杨氏双缝干涉条纹间距", (589.3, 1.0, 0.5, None), "dx", 1.1786, 1e-3),
        ("杨氏双缝干涉条纹间距", (None, 1.0, 0.5, 1.1786), "lam", 589.3, 1e-3),
        ("杨氏双缝干涉条纹间距", (589.3, None, 0.5, 1.1786), "L", 1.0, 1e-6),
        ("杨氏双缝干涉条纹间距", (589.3, 1.0, None, 1.1786), "d", 0.5, 1e-6),
        ("单缝衍射暗纹条件", (0.1, None, 1, 632.8), "theta", 0.362797, 1e-3),
        ("单缝衍射暗纹条件", (None, 0.362568, 1, 632.8), "a", 0.1, 1e-3),
        ("单缝衍射暗纹条件", (0.1, 0.362568, 1, None), "lam", 632.8, 1e-2),
        ("单缝衍射暗纹条件", (0.1, 0.362568, None, 632.8), "m", 1.0, 1e-6),
        ("光子能量", (500.0, None), "E_eV", 2.479685, 1e-3),
        ("光子能量", (None, 2.479685), "lam", 500.0, 1e-3),
        ("波长-频率关系", (500.0, None), "nu", 599.584916, 1e-3),
        ("波长-频率关系", (None, 599.584916), "lam", 500.0, 1e-3),
        ("瑞利判据（角分辨率）", (550.0, 100.0, None), "theta", 1.384037, 1e-3),
        ("瑞利判据（角分辨率）", (None, 100.0, 1.384037), "lam", 550.0, 1e-2),
        ("瑞利判据（角分辨率）", (550.0, None, 1.384037), "D", 100.0, 1e-2),
        ("数值孔径", (1.0, 30.0, None), "NA", 0.5, 1e-6),
        ("数值孔径", (None, 30.0, 0.5), "n", 1.0, 1e-6),
        ("数值孔径", (1.0, None, 0.5), "alpha", 30.0, 1e-6),
        ("布儒斯特角", (None, 1.0, 1.5), "thetaB", 56.309932, 1e-3),
        ("布儒斯特角", (56.309932, None, 1.5), "n1", 1.0, 1e-6),
        ("布儒斯特角", (56.309932, 1.0, None), "n2", 1.5, 1e-6),
        ("全反射临界角", (None, 1.5, 1.0), "thetaC", 41.810315, 1e-3),
        ("全反射临界角", (41.810315, None, 1.0), "n1", 1.5, 1e-6),
        ("全反射临界角", (41.810315, 1.5, None), "n2", 1.0, 1e-6),
        ("密贴透镜组等效焦距", (10.0, 15.0, None), "f", 6.0, 1e-6),
        ("密贴透镜组等效焦距", (None, 15.0, 6.0), "f1", 10.0, 1e-6),
        ("密贴透镜组等效焦距", (10.0, None, 6.0), "f2", 15.0, 1e-6),
        ("薄透镜横向放大率", (None, 40.0, 20.0), "M", 2.0, 1e-6),
        ("薄透镜横向放大率", (2.0, None, 20.0), "v", 40.0, 1e-6),
        ("薄透镜横向放大率", (2.0, 40.0, None), "u", 20.0, 1e-6),
        ("朗伯-比尔吸收定律", (None, 1.0, 0.5, 2.0), "I", 0.367879, 1e-4),
        ("朗伯-比尔吸收定律", (0.367879, None, 0.5, 2.0), "I0", 1.0, 1e-4),
        ("朗伯-比尔吸收定律", (0.367879, 1.0, None, 2.0), "mu", 0.5, 1e-4),
        ("朗伯-比尔吸收定律", (0.367879, 1.0, 0.5, None), "x", 2.0, 1e-4),
    ]
    for name, inputs, key, expect, tol in cases:
        out = compute_formula(name, *inputs)
        if out.startswith("❌"):
            check(f"{name} 求 {key} 失败", False, out)
            continue
        cn = symbol_cn(name, key)
        val = extract_value(out, cn)
        if val is None:
            check(f"{name} 求 {key} 有输出", False, out)
            continue
        check(f"{name} → {key} ≈ {expect}", abs(val - expect) < tol, f"{val}")

    # 非法输入拦截（注意：参数展开传入）
    check("全反射场景被拦截", "❌" in compute_formula("折射定律（斯涅耳定律）", 1.5, 60.0, 1.0, None))
    check("两个空框被拦截", "一次只能求一个" in compute_formula("薄透镜成像公式", None, None, 30))
    check("无空框被拦截", "请留空一个" in compute_formula("薄透镜成像公式", 12, 20, 30))


# ============ 2. 数据拟合（do_fit 界面层） ============
def test_fit_ui():
    print("[2/6] 数据拟合（界面层 do_fit）")
    from app import do_fit, load_file_to_text

    with open(os.path.join(BASE, "examples", "杨氏双缝干涉.csv"), encoding="utf-8-sig") as fp:
        csv_text = fp.read()
    txt, fig, fpath = do_fit(csv_text, "linear", 2, "a*exp(-b*x)+c", "", "级次 m", "位置/mm")
    check("线性拟合文本含斜率", "斜率 k" in txt, txt[:80])
    check("线性拟合文本含 R²", "R²" in txt)
    check("线性拟合返回图", fig is not None)
    check("线性拟合图已落盘", fpath and os.path.exists(fpath))
    k_line = [l for l in txt.splitlines() if l.startswith("斜率 k")][0]
    check("线性拟合斜率≈1.1786（±1%）", abs(float(k_line.split("=")[1].split()[0]) - 1.1786) < 0.012, k_line)

    xs = [i / 10 for i in range(0, 11)]
    ys = [1 + 2 * x + 0.5 * x * x for x in xs]
    data = "\n".join(f"{x:.1f}, {y:.6f}" for x, y in zip(xs, ys))
    txt2, _, _ = do_fit(data, "poly", 2, "", "", "x", "y")
    r2_line = [l for l in txt2.splitlines() if l.startswith("决定系数")][0]
    check("多项式拟合 R²≈1", float(r2_line.split("=")[1].strip()) > 0.999999, txt2[:120])

    xs3 = [i / 10 for i in range(0, 11)]
    ys3 = [3 * math.exp(-0.8 * x) + 0.5 for x in xs3]
    data3 = "\n".join(f"{x:.1f}, {y:.6f}, 0.05" for x, y in zip(xs3, ys3))
    txt3, fig3, fpath3 = do_fit(data3, "custom", 2, "a*exp(-b*x)+c", "1, 0.1, 1", "x", "y")
    check("自定义拟合输出参数", "参数" in txt3, txt3[:120])
    p_line = [l for l in txt3.splitlines() if l.startswith("参数")][0]
    a_val = float(p_line.split("：")[1].split("，")[0].split("=")[1].split()[0])
    check("自定义拟合参数 a≈3", abs(a_val - 3.0) < 0.1, p_line)
    r2c_line = [l for l in txt3.splitlines() if l.startswith("决定系数")][0]
    check("自定义拟合 R²>0.999", float(r2c_line.split("=")[1].strip()) > 0.999, txt3)
    check("自定义拟合带误差棒出图", fig3 is not None and os.path.exists(fpath3))

    csv_path = os.path.join(BASE, "examples", "单缝衍射.csv")
    text = load_file_to_text(csv_path)
    check("CSV 导入读取内容", text and ("," in text), text[:60])
    check("CSV 导入失败返回", "未选择文件" in load_file_to_text(""))

    txt_e, _, _ = do_fit("", "linear", 2, "", "", "x", "y")
    check("空数据提示", "请先粘贴" in txt_e, txt_e)
    txt_e2, _, _ = do_fit("1, 2\n2, 4", "linear", 2, "", "", "x", "y")
    check("数据点不足提示", "不足" in txt_e2 or "❌" in txt_e2, txt_e2)
    txt_e3, _, _ = do_fit("a, b\n1, 2\n2, 4\n3, 6", "linear", 2, "", "", "x", "y")
    check("表头行自动跳过", "斜率 k" in txt_e3, txt_e3[:80])


# ============ 3. 不确定度 / 误差传递（界面层） ============
def test_uncertainty_ui():
    print("[3/6] 不确定度与误差传递（界面层）")
    from app import do_direct_uncertainty, do_propagation

    txt = do_direct_uncertainty("10.02\n10.01\n10.03\n10.00\n10.02", 0.02, True, 2)
    check("直接测量含平均值", "平均值" in txt, txt)
    check("直接测量含扩展不确定度", "扩展不确定度" in txt, txt)
    check("直接测量结果式", "10.016" in txt, txt)
    txt2 = do_direct_uncertainty("", 0.02, True, 2)
    check("空数据提示", "请粘贴" in txt2, txt2)

    txt3 = do_propagation("u*v/(u+v)", "u = 12.3, 0.2\nv = 30.0, 0.4")
    check("误差传递含合成不确定度", "合成不确定度" in txt3, txt3)
    check("误差传递 y≈8.723", "8.723" in txt3, txt3)
    txt4 = do_propagation("u*w", "u = 1.0, 0.1")
    check("未定义变量被拦截", "未定义" in txt4, txt4)
    txt5 = do_propagation("", "u = 1.0, 0.1")
    check("空表达式提示", "请输入表达式" in txt5, txt5)


# ============ 4. 报告生成（gen_report 界面层，三种拟合方式） ============
def test_report_ui():
    print("[4/6] 报告生成（界面层 gen_report，三种拟合方式）")
    from app import gen_report

    with open(os.path.join(BASE, "examples", "杨氏双缝干涉.csv"), encoding="utf-8-sig") as fp:
        data = fp.read()

    def run_case(kind, degree, expr, p0, tag):
        preview, out_path = gen_report(
            f"杨氏双缝干涉实验-{tag}", "王子骞", "2025270487", "2025级光电01班",
            "2026-10-12", "指导教师",
            "观察双缝干涉条纹，测量钠黄光波长。", "Δx = λL/d，由拟合斜率求条纹间距。",
            "钠光灯、双缝、测微目镜、米尺。", "",  # 结论留空→自动生成
            data, kind, degree, expr, p0, "级次 m", "位置/mm",
            "1.18\n1.17\n1.19\n1.18\n1.16", 0.02)
        check(f"{tag} 生成预览", preview.startswith("### 报告预览"), preview[:60])
        check(f"{tag} 生成 docx", out_path and os.path.exists(out_path), str(out_path))
        return out_path

    p1 = run_case("linear", 2, "", "", "线性")
    p2 = run_case("poly", 2, "", "", "多项式")
    p3 = run_case("custom", 2, "a*exp(-b*x)+c", "1, 1, 1", "自定义")
    check("三份报告均已生成", p1 and p2 and p3)

    from docx import Document
    doc = Document(p1)
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    check("报告含七节结构", all(k in "\n".join(paras) for k in
                                ["一、实验目的", "二、实验原理", "三、实验仪器与装置",
                                 "四、实验数据", "五、数据处理", "六、结果与分析", "七、结论"]))
    check("报告含拟合结果文本", any("斜率 k" in p for p in paras), paras[:5])
    check("报告含不确定度分析", any("不确定度分析" in p for p in paras))
    check("报告含自动结论草稿", any("请补充" in p for p in paras))
    check("报告嵌入拟合图", len(doc.inline_shapes) >= 1, len(doc.inline_shapes))
    check("报告含数据表", any(len(t.rows) > 2 for t in doc.tables))

    preview_e, out_e = gen_report("", "王子骞", "2025270487", "2025级光电01班",
                                  "2026-10-12", "", "", "", "", "", data,
                                  "linear", 2, "", "", "x", "y", "", 0.02)
    check("缺实验名称被拦截", "请填写实验名称" in preview_e and out_e is None, preview_e)


# ============ 5. 示例数据全量跑通（三种 CSV 线性拟合） ============
def test_examples():
    print("[5/6] 示例数据全量拟合")
    from core.fitting import parse_xy, fit_data

    expect = {
        "杨氏双缝干涉.csv": (1.1786, "mm/级次"),
        "单缝衍射.csv": (6.328, "mm/级次"),
        "光电效应.csv": (0.4136, "V/(10^14 Hz)"),
    }
    for fname, (k0, unit) in expect.items():
        with open(os.path.join(BASE, "examples", fname), encoding="utf-8-sig") as fp:
            x, y, dy = parse_xy(fp.read())
        res = fit_data(x, y, kind="linear")
        k = res["params"][0]
        rel = abs(k - k0) / k0
        check(f"{fname} 斜率相对误差 < 3%", rel < 0.03, f"k={k} 理论≈{k0}")


# ============ 6. 边界与健壮性 ============
def test_edge():
    print("[6/6] 边界与健壮性")
    from core.fitting import parse_xy, fit_data
    from core.uncertainty import parse_values, parse_vars_text, error_propagation

    # 回归：custom 拟合结果必须带 kind 字段（gen_report 依赖）
    xs = [i / 10 for i in range(0, 11)]
    ys = [3 * math.exp(-0.8 * x) + 0.5 for x in xs]
    res = fit_data(xs, ys, kind="custom", expr="a*exp(-b*x)+c", p0_text="1, 0.1, 1")
    check("custom 拟合结果含 kind 字段", res.get("kind") == "custom", res.keys())
    check("linear 拟合结果含 kind 字段", fit_data(xs, ys, kind="linear").get("kind") == "linear")
    check("poly 拟合结果含 kind 字段", fit_data(xs, ys, kind="poly", degree=2).get("kind") == "poly")

    # 混合 2/3 列（部分行带 dy）→ 应明确报错而非静默错位
    try:
        parse_xy("1, 2.0, 0.1\n2, 4.0\n3, 6.0, 0.2")
        check("混合列 dy 不完整被拦截", False)
    except ValueError as e:
        check("混合列 dy 不完整被拦截", "dy" in str(e), str(e))
    # 全部行带 dy → 正常解析且顺序正确
    x, y, dy = parse_xy("1, 2.0, 0.1\n2, 4.0, 0.2\n3, 6.0, 0.3")
    check("完整 dy 正常解析", len(x) == 3 and dy == [0.1, 0.2, 0.3], dy)

    try:
        parse_values("5.0")
        check("单点测量被拦截", False)
    except ValueError:
        check("单点测量被拦截", True)

    y, uy, partials, _ = error_propagation("u*v", {"u": (3.0, 0.1), "v": (4.0, 0.2)})
    check("偏导 ∂y/∂u = v", abs(partials["u"] - 4.0) < 1e-6, partials)
    check("y = u*v = 12", abs(y - 12.0) < 1e-12, y)

    try:
        parse_vars_text("u 值 = 1, 0.1")
        check("非法变量名被拦截", False)
    except ValueError:
        check("非法变量名被拦截", True)


if __name__ == "__main__":
    print("=" * 50)
    print("集成测试开始（真实数据，模拟界面点击）")
    print("=" * 50)
    try:
        test_formula_ui()
        test_fit_ui()
        test_uncertainty_ui()
        test_report_ui()
        test_examples()
        test_edge()
    except Exception:
        traceback.print_exc()
        FAILED += 1
    print("=" * 50)
    print(f"结果：通过 {PASSED} 项，失败 {FAILED} 项")
    print("=" * 50)
    sys.exit(1 if FAILED else 0)

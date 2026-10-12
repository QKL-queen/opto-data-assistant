# -*- coding: utf-8 -*-
"""项目自检脚本

运行方式：
    python self_test.py

逐个验证公式计算、数据拟合、不确定度评定、误差传递、报告生成，
全部通过后打印 PASS；任一步失败会抛出异常并提示问题模块。
这也是修改代码后最快速的回归验证方式。
"""

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


def test_formulas():
    print("[1/5] 公式计算")
    from core.formulas import (solve_thin_lens, solve_snell, solve_grating,
                               solve_young, solve_single_slit, solve_photon,
                               solve_rayleigh, solve_brewster, solve_critical)

    r, _ = solve_thin_lens(f=None, u=20.0, v=30.0)
    check("薄透镜 f = 12", abs(r["f"] - 12.0) < 1e-9, r)

    r, _ = solve_snell(n1=1.0, theta1=30.0, n2=1.5, theta2=None)
    check("折射角 θ2 ≈ 19.471", abs(r["theta2"] - 19.47122063449069) < 1e-3, r)

    r, _ = solve_grating(d=1.0, theta=None, m=1, lam=500.0)
    check("光栅衍射角 θ = 30", abs(r["theta"] - 30.0) < 1e-6, r)

    r, _ = solve_young(lam=589.3, L=1.0, d=0.5, dx=None)
    check("杨氏双缝 Δx ≈ 1.1786 mm", abs(r["dx"] - 1.1786) < 1e-3, r)

    r, _ = solve_single_slit(a=0.1, theta=None, m=1, lam=632.8)
    expect = 632.8e-9 / (0.1e-3)
    check("单缝衍射 θ 自洽", abs(math.sin(math.radians(r["theta"])) - expect) < 1e-9, r)

    r, extras = solve_photon(lam=500.0, E_eV=None)
    check("光子能量 λ=500nm → 2.479 eV", abs(r["E_eV"] - 2.4790) < 1e-2, r)

    r, _ = solve_rayleigh(lam=550.0, D=100.0, theta=None)
    check("瑞利判据 θ ≈ 1.386″", abs(r["theta"] - 1.3864) < 1e-2, r)

    r, _ = solve_brewster(thetaB=None, n1=1.0, n2=1.5)
    check("布儒斯特角 ≈ 56.31", abs(r["thetaB"] - 56.3099) < 1e-2, r)

    r, _ = solve_critical(thetaC=None, n1=1.5, n2=1.0)
    check("全反射临界角 ≈ 41.81", abs(r["thetaC"] - 41.8103) < 1e-2, r)

    try:
        solve_snell(n1=1.5, theta1=60.0, n2=1.0, theta2=None)  # 全反射，sin 值 >1
        check("折射定律非法输入被拦截", False)
    except ValueError:
        check("折射定律非法输入被拦截", True)


def test_fitting():
    import math
    print("[2/5] 数据拟合")
    from core.fitting import linear_fit, poly_fit, custom_fit, parse_xy, fit_data

    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.1, 4.0, 5.9, 8.2, 10.1]   # 接近 y = 2x + 0.1
    k, b, dk, db, r2, res = linear_fit(xs, ys)
    check("线性拟合斜率 k ≈ 2", abs(k - 2.0) < 0.05, k)
    check("线性拟合 R² 接近 1", r2 > 0.998, r2)

    # 多项式拟合：y = 1 + 2x + 0.5x²
    xs2 = [i / 10 for i in range(0, 11)]
    ys2 = [1 + 2 * x + 0.5 * x * x for x in xs2]
    coeffs, r2p, _ = poly_fit(xs2, ys2, 2)
    check("多项式拟合系数正确", max(abs(c - t) for c, t in zip(coeffs, [0.5, 2.0, 1.0])) < 1e-6, coeffs)

    # 自定义拟合：指数衰减
    import math as m
    xs3 = [i / 10 for i in range(0, 11)]
    ys3 = [3 * m.exp(-0.8 * x) + 0.5 for x in xs3]
    r = custom_fit(xs3, ys3, "a*exp(-b*x)+c", p0_text="1, 0.1, 1")
    check("自定义拟合参数接近真值", abs(r["params"][0] - 3) < 0.1 and abs(r["params"][1] - 0.8) < 0.05, r["params"])
    check("自定义拟合 R² 接近 1", r["r2"] > 0.999, r["r2"])

    # 解析函数
    x, y, dy = parse_xy("1, 2.1\n2, 4.0\n3, 5.9")
    check("数据解析 3 点", len(x) == 3 and len(y) == 3)
    res = fit_data(xs, ys, kind="linear")
    check("fit_data 统一入口", "斜率 k" in res["text"])


def test_uncertainty():
    print("[3/5] 不确定度")
    from core.uncertainty import direct_uncertainty, error_propagation, parse_values

    values = [10.02, 10.01, 10.03, 10.00, 10.02]
    r, txt = direct_uncertainty(values, delta_instrument=0.02)
    check("平均值 ≈ 10.016", abs(r["mean"] - 10.016) < 1e-9, r["mean"])
    check("标准偏差为正", r["std"] > 0)
    check("合成 ≥ A 类", r["u"] >= r["uA"] - 1e-12)
    check("扩展 = k·u", abs(r["U"] - 2 * r["u"]) < 1e-12)

    y, uy, partials, txt2 = error_propagation("u*v/(u+v)", {"u": (12.3, 0.2), "v": (30.0, 0.4)})
    check("误差传递 y ≈ 8.723", abs(y - 8.7234) < 1e-3, y)
    check("误差传递 uy > 0", uy > 0, uy)

    try:
        parse_values("1\nabc\n3")
        check("非法数据被拦截", False)
    except ValueError:
        check("非法数据被拦截", True)


def test_report():
    print("[4/5] 报告生成")
    from core.report import build_report
    import tempfile
    out = build_report(
        {"实验名称": "自检报告", "姓名": "测试", "学号": "000", "班级": "光电2401",
         "日期": "2026-10-05", "实验目的": "目的", "实验原理": "原理", "实验仪器": "仪器"},
        data_table=(["x", "y"], [[1, 2], [2, 4]]),
        fit_text="斜率 k = 2.0",
    )
    check("报告 docx 已生成", os.path.exists(out) and out.endswith(".docx"), out)
    check("报告非空", os.path.getsize(out) > 0)


def test_app_import():
    print("[5/5] 主程序导入")
    try:
        import gradio
        check("gradio 可用", True, gradio.__version__)
    except ImportError:
        check("gradio 可用", False, "未安装，请运行 pip install -r requirements.txt")
        return
    try:
        import app  # noqa: F401
        check("app.py 可导入", True)
    except Exception as e:
        check("app.py 可导入", False, f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    import math
    print("=" * 50)
    print("光电实验数据处理助手 自检开始")
    print("=" * 50)
    try:
        test_formulas()
        test_fitting()
        test_uncertainty()
        test_report()
        test_app_import()
    except Exception:
        traceback.print_exc()
        FAILED += 1
    print("=" * 50)
    print(f"结果：通过 {PASSED} 项，失败 {FAILED} 项")
    print("=" * 50)
    sys.exit(1 if FAILED else 0)

# -*- coding: utf-8 -*-
"""实验数据拟合模块

支持三种拟合方式：
1. 线性拟合   y = k·x + b        —— 最小二乘，给出斜率/截距及其不确定度、R²
2. 多项式拟合 y = c0 + c1·x + ... —— 基于 numpy.polyfit，阶数可调
3. 自定义函数 y = f(x, 参数)       —— Levenberg-Marquardt 算法（纯 numpy 实现），
                                      表达式用 Python 语法书写，例如：
                                      "a*exp(-b*x)+c"（参数按字母序 a,b,c 自动识别）

数据输入格式（parse_xy）：
- 每行一组数据，支持逗号 / 制表符 / 空格 / 分号分隔；
- 每行 2 列：x, y；每行 3 列：x, y, dy（dy 为 y 的误差，用于绘图误差棒）；
- 首行若含非数字字符会自动跳过（可写表头）。

依赖：numpy, matplotlib（scipy 可选，未安装时自动使用内置 LM 算法）。
"""

import math
import re

import numpy as np
import matplotlib

matplotlib.use("Agg")  # 不依赖图形界面，直接输出图片
import matplotlib.pyplot as plt

# 中文字体设置（Windows 常见中文字体，按顺序回退）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

try:
    from scipy.optimize import curve_fit
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# 自定义表达式中允许使用的数学函数
_MATH_FUNCS = {
    "exp": math.exp, "log": math.log, "log10": math.log10, "ln": math.log,
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "abs": abs, "pi": math.pi, "e": math.e, "pow": pow,
}


# ---------- 数据解析 ----------
def parse_xy(text):
    """解析用户粘贴的多行数据，返回 (x 列表, y 列表, dy 列表或 None)。

    每行格式：x, y 或 x, y, dy；分隔符为逗号/制表符/空格/分号。
    """
    xs, ys, dys = [], [], []
    if not text or not text.strip():
        raise ValueError("数据为空，请先粘贴数据或上传文件。")
    for lineno, line in enumerate(text.strip().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"[,;\t\s]+", line.strip())
        parts = [p for p in parts if p != ""]
        if not parts:
            continue
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            # 遇到表头等非数字行直接跳过
            continue
        if len(nums) == 2:
            xs.append(nums[0])
            ys.append(nums[1])
        elif len(nums) == 3:
            xs.append(nums[0])
            ys.append(nums[1])
            dys.append(abs(nums[2]))
        else:
            raise ValueError(f"第 {lineno} 行数据列数不合法（应 2 或 3 列）：{line}")
    if len(xs) < 3:
        raise ValueError(f"有效数据点不足（仅 {len(xs)} 个），至少需要 3 个数据点。")
    return xs, ys, (dys if dys else None)


def _r_squared(y, y_fit):
    """计算决定系数 R² = 1 - SS_res / SS_tot。"""
    ss_res = float(np.sum((np.asarray(y) - np.asarray(y_fit)) ** 2))
    ss_tot = float(np.sum((np.asarray(y) - np.mean(y)) ** 2))
    if ss_tot == 0:
        return 1.0
    return 1.0 - ss_res / ss_tot


# ---------- 1. 线性拟合 ----------
def linear_fit(x, y):
    """线性最小二乘拟合 y = kx + b。

    返回：k, b, dk（斜率标准误差）, db（截距标准误差）, r2, 残差列表
    公式来源：大学物理实验教材「最小二乘法与线性拟合」。
    """
    n = len(x)
    sx = sum(x)
    sy = sum(y)
    sxx = sum(xi * xi for xi in x)
    sxy = sum(xi * yi for xi, yi in zip(x, y))
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-15:
        raise ValueError("所有 x 值相同，无法进行线性拟合（x 无变化）。")
    k = (n * sxy - sx * sy) / denom
    b = (sy - k * sx) / n

    y_fit = [k * xi + b for xi in x]
    r2 = _r_squared(y, y_fit)
    residuals = [yi - yfi for yi, yfi in zip(y, y_fit)]
    s2 = sum(r * r for r in residuals) / (n - 2) if n > 2 else 0.0
    dk = math.sqrt(s2 / (sxx - sx * sx / n))
    db = dk * math.sqrt(sxx / n) if n > 0 else float("nan")
    return k, b, dk, db, r2, residuals


# ---------- 2. 多项式拟合 ----------
def poly_fit(x, y, degree=2):
    """多项式拟合，返回 (系数列表[从高次到常数], R², 残差)。"""
    if degree < 1:
        raise ValueError("多项式阶数必须 ≥ 1。")
    if len(x) <= degree:
        raise ValueError(f"数据点（{len(x)} 个）必须多于阶数（{degree}），请降低阶数或补充数据。")
    coeffs = np.polyfit(x, y, degree)
    y_fit = np.polyval(coeffs, x)
    r2 = _r_squared(y, y_fit)
    residuals = list(np.asarray(y) - y_fit)
    return list(coeffs), r2, residuals


# ---------- 3. 自定义函数拟合 ----------
def _extract_params(expr):
    """从表达式文本中提取参数名（排除 x 和数学函数/常数）。"""
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr)
    reserved = set(_MATH_FUNCS.keys()) | {"x"}
    params = []
    for t in tokens:
        if t not in reserved and t not in params:
            params.append(t)
    return params


def _build_func(expr, param_names):
    """把用户表达式编译成 callable：f(x, params)->y。

    说明：仅允许使用数学函数（exp/log/sqrt/sin 等）与常数（pi/e），
    表达式用 eval 求值，内置函数已禁用，避免任意代码执行风险。
    """
    ns = dict(_MATH_FUNCS)
    ns["__builtins__"] = {}
    code = compile(expr, "<用户表达式>", "eval")

    def func(xv, p):
        ns["x"] = xv
        for name, val in zip(param_names, p):
            ns[name] = val
        return eval(code, ns)

    return func


def _lm_fit(x, y, func, p0, max_iter=300, tol=1e-10):
    """Levenberg-Marquardt 非线性最小二乘（纯 numpy 实现）。

    返回 (最优参数, 参数标准误差, 协方差矩阵, 拟合值列表)。
    """
    xa = np.asarray(x, dtype=float)
    ya = np.asarray(y, dtype=float)
    p = np.asarray(p0, dtype=float)
    m = len(p)
    n = len(xa)
    lam = 1e-3

    def residuals(pp):
        return ya - np.asarray([func(xi, pp) for xi in xa], dtype=float)

    r = residuals(p)
    chi2 = float(r @ r)

    for _ in range(max_iter):
        # 数值 Jacobian（中心差分）
        J = np.zeros((n, m))
        for j in range(m):
            h = 1e-6 * max(1.0, abs(p[j]))
            pp1, pp2 = p.copy(), p.copy()
            pp1[j] += h
            pp2[j] -= h
            J[:, j] = (residuals(pp1) - residuals(pp2)) / (2 * h)

        JtJ = J.T @ J
        g = J.T @ r
        solved = False
        for _lam_scale in range(8):
            try:
                A = JtJ + lam * np.diag(np.diag(JtJ) + 1e-12)
                # 高斯-牛顿步：δ = -(JᵀJ + λD)⁻¹·Jᵀr（注意负号）
                delta = -np.linalg.solve(A, g)
            except np.linalg.LinAlgError:
                lam *= 10
                continue
            p_new = p + delta
            r_new = residuals(p_new)
            chi2_new = float(r_new @ r_new)
            if chi2_new < chi2:
                lam = max(lam * 0.3, 1e-12)
                p, r, chi2 = p_new, r_new, chi2_new
                solved = True
                break
            lam *= 10
        if not solved:
            break
        if float(np.max(np.abs(delta))) < tol:
            break

    # 参数不确定度：协方差 = (JᵀJ)⁻¹ · s²
    J = np.zeros((n, m))
    for j in range(m):
        h = 1e-6 * max(1.0, abs(p[j]))
        pp1, pp2 = p.copy(), p.copy()
        pp1[j] += h
        pp2[j] -= h
        J[:, j] = (residuals(pp1) - residuals(pp2)) / (2 * h)
    try:
        cov = np.linalg.inv(J.T @ J)
    except np.linalg.LinAlgError:
        cov = None
    s2 = chi2 / (n - m) if n > m else 0.0
    if cov is not None:
        p_std = np.sqrt(np.abs(np.diag(cov) * s2))
    else:
        p_std = np.full(m, float("nan"))
    y_fit = [func(xi, p) for xi in xa]
    return p, p_std, cov, y_fit


def custom_fit(x, y, expr, p0_text=""):
    """自定义函数拟合入口。

    expr 示例："a*exp(-b*x)+c"
    p0_text 示例："1, 0.01, 0"（与参数个数一致；为空时自动取 1.0 初值）
    """
    param_names = _extract_params(expr)
    if not param_names:
        raise ValueError("表达式中未识别到参数（如 a、b、c）。示例：a*exp(-b*x)+c")
    if p0_text and p0_text.strip():
        p0 = [float(t) for t in re.split(r"[,;\s]+", p0_text.strip()) if t]
        if len(p0) != len(param_names):
            raise ValueError(
                f"初值个数（{len(p0)}）与参数个数（{len(param_names)}，"
                f"按字母序 {param_names}）不一致，请检查。")
    else:
        p0 = [1.0] * len(param_names)

    func = _build_func(expr, param_names)
    # 初值校验：先试算一遍，表达式有误会立即暴露
    try:
        y0 = np.asarray([func(xi, p0) for xi in x[:3]], dtype=float)
        if not np.all(np.isfinite(y0)):
            raise ValueError("表达式在当前初值下产生 NaN/无穷，请检查初值。")
    except Exception as e:
        raise ValueError(f"表达式求值失败：{e}")

    p, p_std, cov, y_fit = _lm_fit(x, y, func, p0)
    r2 = _r_squared(y, y_fit)
    residuals = list(np.asarray(y) - np.asarray(y_fit))
    return {
        "expr": expr,
        "params": list(p),
        "param_names": param_names,
        "param_std": list(p_std),
        "r2": r2,
        "residuals": residuals,
        "y_fit": y_fit,
    }


# ---------- 统一拟合入口 ----------
def fit_data(x, y, kind="linear", degree=2, expr="", p0_text=""):
    """按类型执行拟合，返回统一结构的字典：
    {
        "kind": 类型, "params": 参数值, "param_names": 参数名,
        "param_std": 参数不确定度, "r2": R², "residuals": 残差,
        "y_fit": 拟合值, "expr": 表达式(自定义时), "text": 结果说明文本,
    }
    """
    x = [float(v) for v in x]
    y = [float(v) for v in y]
    if kind == "linear":
        k, b, dk, db, r2, res = linear_fit(x, y)
        y_fit = [k * xi + b for xi in x]
        text = (
            f"拟合方程：y = {k:.6g}·x + ({b:.6g})\n"
            f"斜率 k = {k:.6g} ± {dk:.6g}\n"
            f"截距 b = {b:.6g} ± {db:.6g}\n"
            f"决定系数 R² = {r2:.6f}\n"
            f"数据点数 n = {len(x)}"
        )
        return {"kind": "linear", "params": [k, b], "param_names": ["k", "b"],
                "param_std": [dk, db], "r2": r2, "residuals": res,
                "y_fit": y_fit, "text": text}
    if kind == "poly":
        coeffs, r2, res = poly_fit(x, y, degree)
        y_fit = list(np.polyval(coeffs, x))
        expr_str = " + ".join(
            f"{c:.6g}·x^{len(coeffs) - 1 - i}" if len(coeffs) - 1 - i > 0 else f"{c:.6g}"
            for i, c in enumerate(coeffs)
        )
        text = (
            f"多项式阶数：{degree}\n"
            f"拟合方程：y = {expr_str}\n"
            f"系数（从高次到常数）：{', '.join(f'{c:.6g}' for c in coeffs)}\n"
            f"决定系数 R² = {r2:.6f}"
        )
        return {"kind": "poly", "params": list(coeffs), "param_names": [f"c{i}" for i in range(degree + 1)],
                "param_std": [], "r2": r2, "residuals": res,
                "y_fit": y_fit, "text": text}
    if kind == "custom":
        res = custom_fit(x, y, expr, p0_text)
        names = res["param_names"]
        stds = res["param_std"]
        param_lines = "，".join(
            f"{n} = {v:.6g} ± {s:.3g}" if s == s else f"{n} = {v:.6g}"
            for n, v, s in zip(names, res["params"], stds)
        )
        res["text"] = (
            f"拟合函数：y = f(x; {', '.join(names)})\n"
            f"表达式：{expr}\n"
            f"参数：{param_lines}\n"
            f"决定系数 R² = {res['r2']:.6f}\n"
            f"算法：{'SciPy curve_fit' if HAS_SCIPY else '内置 Levenberg-Marquardt'}"
        )
        return res
    raise ValueError(f"未知拟合类型：{kind}")


# ---------- 绘图 ----------
def plot_fit(x, y, y_fit, text, xlabel="x", ylabel="y", dy=None, title="数据拟合结果"):
    """绘制数据点（可选误差棒）与拟合曲线，返回 matplotlib Figure。"""
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=130)
    if dy is not None:
        ax.errorbar(x, y, yerr=dy, fmt="o", ms=4, capsize=2,
                    color="#2f6fb3", label="实验数据", zorder=3)
    else:
        ax.scatter(x, y, s=22, color="#2f6fb3", label="实验数据", zorder=3)
    # 拟合曲线：按 x 排序绘制光滑曲线
    order = np.argsort(x)
    xs = np.asarray(x)[order]
    ys = np.asarray(y_fit)[order]
    ax.plot(xs, ys, "-", color="#d94f45", lw=1.8, label="拟合曲线")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best")
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    # 简单自检
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.1, 4.0, 5.9, 8.2, 10.1]
    k, b, dk, db, r2, _ = linear_fit(xs, ys)
    print(f"线性拟合：k={k:.4f}（期望≈2.0） b={b:.4f}（期望≈0.06） R²={r2:.4f}")

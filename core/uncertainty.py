# -*- coding: utf-8 -*-
"""不确定度 / 误差分析模块

包含两部分：
1. 直接测量不确定度评定（大学物理实验标准流程）：
   - 平均值 x̄、标准偏差 s（贝塞尔公式）、平均值的标准误差 s/√n
   - A 类不确定度 uA = t_p(n-1) · s/√n（t 因子表，默认 95% 置信概率）
   - B 类不确定度 uB = Δ仪/√3（仪器允差按均匀分布）
   - 合成不确定度 u = √(uA² + uB²)，扩展不确定度 U = k·u（默认 k=2）
   - 结果表示：x = x̄ ± U（单位）

2. 间接测量误差传递：
   - 对任意表达式 y = f(x1, x2, ...)，用数值偏导数计算
     uy = √( Σ (∂f/∂xi · uxi)² )

t 因子表（置信概率 95%，自由度 ν = n-1）来源：大学物理实验教材附录。
"""

import math
import re

# t 分布因子表（95% 置信概率，ν = n - 1）
_T_TABLE = {
    1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57,
    6: 2.45, 7: 2.37, 8: 2.31, 9: 2.26, 10: 2.23,
    11: 2.20, 12: 2.18, 13: 2.16, 14: 2.14, 15: 2.13,
    16: 2.12, 17: 2.11, 18: 2.10, 19: 2.09, 20: 2.09,
    25: 2.06, 30: 2.04, 40: 2.02, 60: 2.00, 100: 1.98,
}


def t_factor(n):
    """根据测量次数 n 取 t 因子（95%）。n 过大时取 1.96。"""
    nu = n - 1
    best = None
    for key in sorted(_T_TABLE.keys()):
        if key >= nu:
            best = key
            break
    if best is None:
        return 1.96
    return _T_TABLE[best]


def parse_values(text):
    """解析一列测量数据（每行一个数字，支持逗号/空格/制表符分隔）。"""
    nums = []
    if not text or not text.strip():
        raise ValueError("数据为空，请粘贴测量数据。")
    for line in text.strip().splitlines():
        for part in re.split(r"[,;\t\s]+", line.strip()):
            if part == "":
                continue
            try:
                nums.append(float(part))
            except ValueError:
                raise ValueError(f"无法解析为数字：{part!r}")
    if len(nums) < 2:
        raise ValueError(f"有效数据点仅 {len(nums)} 个，至少需要 2 个测量值。")
    return nums


def direct_uncertainty(values, delta_instrument=0.0, use_t=True, k=2.0):
    """直接测量不确定度评定。

    参数：
        values            测量数据列表
        delta_instrument  仪器允差 Δ（B 类来源；不填则 B 类为 0）
        use_t             是否使用 t 因子计算 A 类（否则用 s/√n）
        k                 扩展不确定度因子（默认 2，约 95%）

    返回：汇总字典 + 说明文本。
    """
    n = len(values)
    mean = sum(values) / n
    s = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else 0.0
    s_mean = s / math.sqrt(n)

    uA = (t_factor(n) * s_mean) if use_t else s_mean
    uB = delta_instrument / math.sqrt(3.0) if delta_instrument and delta_instrument > 0 else 0.0
    u = math.sqrt(uA * uA + uB * uB)
    U = k * u

    lines = [
        f"测量次数 n = {n}",
        f"平均值 x̄ = {mean:.6g}",
        f"标准偏差 s = {s:.6g}（贝塞尔公式）",
        f"平均值标准误差 s(x̄) = {s_mean:.6g}",
    ]
    if use_t:
        lines.append(f"A 类不确定度 uA = t({n - 1})·s(x̄) = {t_factor(n):.2f} × {s_mean:.6g} = {uA:.6g}")
    else:
        lines.append(f"A 类不确定度 uA = s(x̄) = {uA:.6g}")
    if uB > 0:
        lines.append(f"B 类不确定度 uB = Δ/√3 = {delta_instrument:.6g}/{math.sqrt(3):.4f} = {uB:.6g}")
    else:
        lines.append("B 类不确定度 uB = 0（未提供仪器允差）")
    lines.append(f"合成不确定度 u = √(uA²+uB²) = {u:.6g}")
    lines.append(f"扩展不确定度 U = k·u = {k:.3g} × {u:.6g} = {U:.6g}")

    result = {
        "n": n, "mean": mean, "std": s, "std_err": s_mean,
        "uA": uA, "uB": uB, "u": u, "U": U, "k": k,
    }
    return result, "\n".join(lines)


# ---------- 误差传递 ----------
_MATH_FUNCS = {
    "exp": math.exp, "log": math.log, "log10": math.log10, "ln": math.log,
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "abs": abs, "pi": math.pi, "e": math.e, "pow": pow,
}


def _safe_eval(expr, var_values):
    """安全求值：只允许数学函数与给定的变量名。"""
    ns = dict(_MATH_FUNCS)
    ns["__builtins__"] = {}
    ns.update(var_values)
    return eval(compile(expr, "<用户表达式>", "eval"), ns)


def parse_vars_text(text):
    """解析变量输入："u=12.3,0.2" 每行一个，返回 {变量名: (数值, 不确定度)}。"""
    data = {}
    if not text or not text.strip():
        raise ValueError("变量数据为空。格式示例（每行一个）：\nu = 12.3, 0.2\nv = 30.0, 0.4")
    for lineno, line in enumerate(text.strip().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"第 {lineno} 行缺少等号：{line}（格式：u=12.3,0.2）")
        name, _, rest = line.partition("=")
        name = name.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise ValueError(f"第 {lineno} 行变量名不合法：{name}")
        nums = [t for t in re.split(r"[,;\s]+", rest.strip()) if t]
        if len(nums) != 2:
            raise ValueError(f"第 {lineno} 行应为「数值,不确定度」两个值：{line}")
        try:
            val, unc = float(nums[0]), abs(float(nums[1]))
        except ValueError:
            raise ValueError(f"第 {lineno} 行数值无法解析：{line}")
        data[name] = (val, unc)
    if len(data) < 1:
        raise ValueError("未解析到任何变量。")
    return data


def error_propagation(expr, var_data):
    """间接测量误差传递：uy = √(Σ(∂f/∂xi·ui)²)，数值中心差分求偏导。

    var_data: {变量名: (测量值, 不确定度)}
    返回 (y, uy, 偏导数字典, 说明文本)。
    """
    # 校验表达式中出现的变量都在 var_data 中
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr))
    reserved = set(_MATH_FUNCS.keys())
    unknown = tokens - reserved - set(var_data.keys())
    if unknown:
        raise ValueError(f"表达式中存在未定义的变量：{sorted(unknown)}。"
                         "请先在变量输入框填写这些变量的数值与不确定度。")

    vals = {name: data[0] for name, data in var_data.items()}
    uncs = {name: data[1] for name, data in var_data.items()}
    y = _safe_eval(expr, vals)

    partials = {}
    for name, v in vals.items():
        h = 1e-5 * max(1.0, abs(v))
        vals_plus = dict(vals)
        vals_minus = dict(vals)
        vals_plus[name] = v + h
        vals_minus[name] = v - h
        f_plus = _safe_eval(expr, vals_plus)
        f_minus = _safe_eval(expr, vals_minus)
        partials[name] = (f_plus - f_minus) / (2 * h)

    uy = math.sqrt(sum((partials[name] * uncs[name]) ** 2 for name in vals))

    lines = [f"表达式：y = {expr}"]
    lines.append(f"计算结果：y = {y:.6g}")
    for name in vals:
        lines.append(f"  ∂y/∂{name} = {partials[name]:.6g}，u({name}) = {uncs[name]:.6g}")
    lines.append(f"合成不确定度：uy = {uy:.6g}")
    lines.append(f"结果表示：y = {y:.6g} ± {uy:.6g}")
    return y, uy, partials, "\n".join(lines)


if __name__ == "__main__":
    # 简单自检
    r, txt = direct_uncertainty([10.02, 10.01, 10.03, 10.00, 10.02], delta_instrument=0.02)
    print(txt)
    y, uy, _, txt2 = error_propagation("u*v/(u+v)", {"u": (12.3, 0.2), "v": (30.0, 0.4)})
    print(txt2)

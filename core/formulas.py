# -*- coding: utf-8 -*-
"""光学公式计算模块

本模块收录光电专业基础实验中常用的光学公式，每条公式支持：
给定其中任意 N-1 个物理量，求解剩余 1 个未知量。

公式统一以「注册表」形式组织（FORMULAS 列表），每条记录包含：
- key        : 唯一标识
- name       : 中文名称
- formula    : 显示用公式文本
- symbols    : 物理量列表，每个元素为 (键, 中文名, 单位)
- solve      : 求解函数，参数为各物理量数值（未知量传 None），
               返回 (填充后的数值字典, 附加说明行列表)

单位约定（已内置换算，使用者只需按提示输入）：
- 波长 λ   ：纳米 nm
- 长度     ：厘米 cm（透镜）、毫米 mm（缝宽/缝距/条纹间距）、米 m（缝屏距）
- 角度     ：度 °
- 频率     ：太赫兹 THz
- 能量     ：电子伏 eV（同时输出焦耳 J）

扩展方法：仿照下方函数实现 solve 函数并追加一条记录即可，界面会自动识别。
"""

import math

# ---------- 物理常数 ----------
H = 6.62607015e-34       # 普朗克常数  J·s
C = 299792458.0          # 真空光速    m/s
E_CHARGE = 1.602176634e-19  # 元电荷  C


def _check_positive(name, value):
    """校验物理量必须为正数，否则给出明确中文报错。"""
    if value is None:
        return
    if value <= 0:
        raise ValueError(f"{name} 必须为正数，当前输入为 {value}。")


def _check_angle_sin(ratio, name):
    """校验 sin 值不超过 1，否则说明无实数解的原因。"""
    if abs(ratio) > 1.0 + 1e-12:
        raise ValueError(
            f"无法求解：{name} 计算得到 sin 值为 {ratio:.4f}（>1），"
            "说明物理上不存在实数解，请检查输入数据。"
        )


# ================= 1. 薄透镜成像公式 =================
def solve_thin_lens(f=None, u=None, v=None):
    """1/f = 1/u + 1/v（高斯公式）。f 焦距，u 物距，v 像距（单位 cm）。"""
    _check_positive("焦距 f", f)
    _check_positive("物距 u", u)
    _check_positive("像距 v", v)
    if f is None:
        if u is None or v is None:
            raise ValueError("薄透镜公式：请至少给出 u、v 两个值。")
        f = u * v / (u + v)
    elif u is None:
        if v == f:
            raise ValueError("薄透镜公式：v = f 时物距为无穷大（u → ∞）。")
        u = f * v / (v - f)
    elif v is None:
        if u == f:
            raise ValueError("薄透镜公式：u = f 时像距为无穷大（v → ∞）。")
        v = f * u / (u - f)
    return {"f": f, "u": u, "v": v}, []


# ================= 2. 折射定律（斯涅耳定律）=================
def solve_snell(n1=None, theta1=None, n2=None, theta2=None):
    """n1·sinθ1 = n2·sinθ2。角度单位：度。"""
    _check_positive("折射率 n1", n1)
    _check_positive("折射率 n2", n2)
    if (n1 is None) + (theta1 is None) + (n2 is None) + (theta2 is None) != 1:
        raise ValueError("折射定律：请恰好留空一个待求量，其余填数值。")
    r1 = n1 * math.sin(math.radians(theta1)) if (n1 is not None and theta1 is not None) else None
    r2 = n2 * math.sin(math.radians(theta2)) if (n2 is not None and theta2 is not None) else None
    if n1 is None:
        n1 = r2 / math.sin(math.radians(theta1))
    elif n2 is None:
        n2 = r1 / math.sin(math.radians(theta2))
    elif theta1 is None:
        ratio = r2 / n1
        _check_angle_sin(ratio, "入射角 θ1")
        theta1 = math.degrees(math.asin(ratio))
    elif theta2 is None:
        ratio = r1 / n2
        _check_angle_sin(ratio, "折射角 θ2")
        theta2 = math.degrees(math.asin(ratio))
    return {"n1": n1, "theta1": theta1, "n2": n2, "theta2": theta2}, []


# ================= 3. 光栅方程 =================
def solve_grating(d=None, theta=None, m=None, lam=None):
    """d·sinθ = m·λ。d 光栅常数(μm)，θ 衍射角(°)，m 级次(整数)，λ 波长(nm)。"""
    _check_positive("光栅常数 d", d)
    _check_positive("衍射角 θ", theta)
    _check_positive("波长 λ", lam)
    if m is not None:
        if m <= 0 or abs(m - round(m)) > 1e-9:
            raise ValueError("光谱级次 m 必须为正整数（如 1、2、3）。")
        m = round(m)
    if lam is None:
        if d is None or theta is None or m is None:
            raise ValueError("光栅方程：至少给出 d、θ、m 三个值。")
        lam = d * 1000 * math.sin(math.radians(theta)) / m   # nm
    elif d is None:
        d = m * lam / (1000 * math.sin(math.radians(theta)))  # μm
    elif theta is None:
        ratio = m * lam / (d * 1000)
        _check_angle_sin(ratio, "衍射角 θ")
        theta = math.degrees(math.asin(ratio))
    elif m is None:
        m_val = d * 1000 * math.sin(math.radians(theta)) / lam
        m = int(round(m_val))
        if abs(m_val - m) > 1e-3:
            raise ValueError(f"计算得到 m = {m_val:.4f}，不是整数，说明给定数据不自洽，请检查。")
    return {"d": d, "theta": theta, "m": m, "lam": lam}, []


# ================= 4. 杨氏双缝干涉条纹间距 =================
def solve_young(lam=None, L=None, d=None, dx=None):
    """Δx = λL/d。λ 波长(nm)，L 缝屏距离(m)，d 缝间距(mm)，Δx 条纹间距(mm)。"""
    _check_positive("波长 λ", lam)
    _check_positive("缝屏距离 L", L)
    _check_positive("缝间距 d", d)
    _check_positive("条纹间距 Δx", dx)
    if dx is None:
        dx = lam * L * 1e-3 / d                      # mm
    elif d is None:
        d = lam * L * 1e-3 / dx                      # mm
    elif L is None:
        L = dx * d * 1e3 / lam                       # m
    elif lam is None:
        lam = dx * d * 1e3 / L                       # nm
    return {"lam": lam, "L": L, "d": d, "dx": dx}, []


# ================= 5. 单缝衍射暗纹条件 =================
def solve_single_slit(a=None, theta=None, m=None, lam=None):
    """a·sinθ = m·λ。a 缝宽(mm)，θ 衍射角(°)，m 暗纹级次(整数)，λ 波长(nm)。"""
    _check_positive("缝宽 a", a)
    _check_positive("衍射角 θ", theta)
    _check_positive("波长 λ", lam)
    if m is not None:
        if m <= 0 or abs(m - round(m)) > 1e-9:
            raise ValueError("暗纹级次 m 必须为正整数（如 1、2、3）。")
        m = round(m)
    if lam is None:
        if a is None or theta is None or m is None:
            raise ValueError("单缝衍射：至少给出 a、θ、m 三个值。")
        lam = a * 1e6 * math.sin(math.radians(theta)) / m   # nm
    elif a is None:
        a = m * lam / (1e6 * math.sin(math.radians(theta)))  # mm
    elif theta is None:
        ratio = m * lam * 1e-9 / (a * 1e-3)
        _check_angle_sin(ratio, "衍射角 θ")
        theta = math.degrees(math.asin(ratio))
    elif m is None:
        m_val = a * 1e6 * math.sin(math.radians(theta)) / lam
        m = int(round(m_val))
        if abs(m_val - m) > 1e-3:
            raise ValueError(f"计算得到 m = {m_val:.4f}，不是整数，说明给定数据不自洽，请检查。")
    return {"a": a, "theta": theta, "m": m, "lam": lam}, []


# ================= 6. 光子能量 =================
def solve_photon(lam=None, E_eV=None):
    """E = hc/λ。λ 波长(nm)，E 光子能量(eV)，同时输出焦耳值。"""
    _check_positive("波长 λ", lam)
    if E_eV is not None and E_eV <= 0:
        raise ValueError("光子能量 E 必须为正数。")
    if lam is None:
        lam = H * C / (E_eV * E_CHARGE) * 1e9        # nm
    E_J = H * C / (lam * 1e-9)                       # J
    E_eV = E_J / E_CHARGE                            # eV
    extras = [f"光子能量（焦耳）E = {E_J:.6g} J"]
    return {"lam": lam, "E_eV": E_eV}, extras


# ================= 7. 波长-频率关系 =================
def solve_wave_freq(lam=None, nu=None):
    """λ·ν = c。λ 波长(nm)，ν 频率(THz)。"""
    _check_positive("波长 λ", lam)
    _check_positive("频率 ν", nu)
    if lam is None:
        lam = C * 1e-3 / nu                          # nm
    else:
        nu = C / (lam * 1e3)                         # THz
    return {"lam": lam, "nu": nu}, []


# ================= 8. 瑞利判据（角分辨率）=================
def solve_rayleigh(lam=None, D=None, theta=None):
    """θ = 1.22λ/D。λ 波长(nm)，D 通光孔径(mm)，θ 角分辨率(角秒″)。"""
    _check_positive("波长 λ", lam)
    _check_positive("孔径 D", D)
    _check_positive("角分辨率 θ", theta)
    if theta is None:
        theta_rad = 1.22 * lam * 1e-9 / (D * 1e-3)
        theta = theta_rad * 180 / math.pi * 3600     # 角秒
    elif lam is None:
        theta_rad = theta / 3600 * math.pi / 180
        lam = theta_rad * D * 1e-3 / 1.22 * 1e9      # nm
    elif D is None:
        theta_rad = theta / 3600 * math.pi / 180
        D = 1.22 * lam * 1e-9 / theta_rad * 1e3      # mm
    extras = [f"角分辨率（弧度）θ = {theta / 3600 * math.pi / 180:.6g} rad"]
    return {"lam": lam, "D": D, "theta": theta}, extras


# ================= 9. 数值孔径 =================
def solve_na(n=None, alpha=None, NA=None):
    """NA = n·sinα。n 介质折射率，α 孔径角(°)，NA 数值孔径。"""
    _check_positive("介质折射率 n", n)
    _check_positive("孔径角 α", alpha)
    _check_positive("数值孔径 NA", NA)
    if NA is None:
        NA = n * math.sin(math.radians(alpha))
    elif n is None:
        n = NA / math.sin(math.radians(alpha))
    elif alpha is None:
        ratio = NA / n
        _check_angle_sin(ratio, "孔径角 α")
        alpha = math.degrees(math.asin(ratio))
    return {"n": n, "alpha": alpha, "NA": NA}, []


# ================= 10. 布儒斯特角 =================
def solve_brewster(thetaB=None, n1=None, n2=None):
    """tanθB = n2/n1。θB 布儒斯特角(°)，n1 入射介质折射率，n2 出射介质折射率。"""
    _check_positive("折射率 n1", n1)
    _check_positive("折射率 n2", n2)
    _check_positive("布儒斯特角 θB", thetaB)
    if thetaB is None:
        thetaB = math.degrees(math.atan(n2 / n1))
    elif n2 is None:
        n2 = n1 * math.tan(math.radians(thetaB))
    elif n1 is None:
        n1 = n2 / math.tan(math.radians(thetaB))
    return {"thetaB": thetaB, "n1": n1, "n2": n2}, []


# ================= 11. 全反射临界角 =================
def solve_critical(thetaC=None, n1=None, n2=None):
    """sinθC = n2/n1（要求 n1 > n2）。θC 临界角(°)。"""
    _check_positive("折射率 n1", n1)
    _check_positive("折射率 n2", n2)
    _check_positive("临界角 θC", thetaC)
    if n1 is not None and n2 is not None and n1 <= n2:
        raise ValueError("全反射要求光密介质折射率 n1 > 光疏介质 n2，请检查输入。")
    if thetaC is None:
        ratio = n2 / n1
        _check_angle_sin(ratio, "临界角 θC")
        thetaC = math.degrees(math.asin(ratio))
    elif n2 is None:
        n2 = n1 * math.sin(math.radians(thetaC))
    elif n1 is None:
        n1 = n2 / math.sin(math.radians(thetaC))
    return {"thetaC": thetaC, "n1": n1, "n2": n2}, []


# ================= 12. 密贴透镜组等效焦距 =================
def solve_lens_combo(f1=None, f2=None, f=None):
    """1/f = 1/f1 + 1/f2（薄透镜密贴）。f1、f2 单透镜焦距(cm)，f 等效焦距(cm)。"""
    _check_positive("焦距 f1", f1)
    _check_positive("焦距 f2", f2)
    if f is not None and f <= 0:
        raise ValueError("等效焦距 f 必须为正数。")
    if f is None:
        if f1 is None or f2 is None:
            raise ValueError("密贴透镜组：请至少给出 f1、f2 两个值。")
        f = f1 * f2 / (f1 + f2)
    elif f1 is None:
        if f2 == f:
            raise ValueError("f2 = f 时 f1 为无穷大，请检查输入。")
        f1 = f * f2 / (f2 - f)
    elif f2 is None:
        if f1 == f:
            raise ValueError("f1 = f 时 f2 为无穷大，请检查输入。")
        f2 = f * f1 / (f1 - f)
    return {"f1": f1, "f2": f2, "f": f}, []


# ================= 13. 薄透镜横向放大率 =================
def solve_magnification(M=None, v=None, u=None):
    """M = v/u。M 放大率，v 像距(cm)，u 物距(cm)。"""
    _check_positive("像距 v", v)
    _check_positive("物距 u", u)
    if M is None:
        M = v / u
    elif v is None:
        v = M * u
    elif u is None:
        u = v / M
    return {"M": M, "v": v, "u": u}, []


# ================= 14. 朗伯-比尔吸收定律 =================
def solve_beer(I=None, I0=None, mu=None, x=None):
    """I = I0·exp(-μx)。I 出射光强(相对值)，I0 入射光强(相对值)，μ 吸收系数(1/cm)，x 光程(cm)。"""
    for name, val in (("出射光强 I", I), ("入射光强 I0", I0), ("吸收系数 μ", mu), ("光程 x", x)):
        _check_positive(name, val)
    if I is None:
        I = I0 * math.exp(-mu * x)
    elif I0 is None:
        I0 = I * math.exp(mu * x)
    elif mu is None:
        if I >= I0:
            raise ValueError("吸收介质中 I < I0，当前数据无法计算吸收系数，请检查。")
        mu = math.log(I0 / I) / x
    elif x is None:
        if I >= I0:
            raise ValueError("吸收介质中 I < I0，当前数据无法计算光程，请检查。")
        x = math.log(I0 / I) / mu
    return {"I": I, "I0": I0, "mu": mu, "x": x}, []


# ================= 公式注册表 =================
FORMULAS = [
    {
        "key": "thin_lens",
        "name": "薄透镜成像公式",
        "formula": "1/f = 1/u + 1/v",
        "symbols": [("f", "焦距 f", "cm"), ("u", "物距 u", "cm"), ("v", "像距 v", "cm")],
        "solve": solve_thin_lens,
    },
    {
        "key": "snell",
        "name": "折射定律（斯涅耳定律）",
        "formula": "n1·sinθ1 = n2·sinθ2",
        "symbols": [("n1", "入射介质折射率 n1", ""), ("theta1", "入射角 θ1", "°"),
                    ("n2", "折射介质折射率 n2", ""), ("theta2", "折射角 θ2", "°")],
        "solve": solve_snell,
    },
    {
        "key": "grating",
        "name": "光栅方程",
        "formula": "d·sinθ = m·λ",
        "symbols": [("d", "光栅常数 d", "μm"), ("theta", "衍射角 θ", "°"),
                    ("m", "光谱级次 m", "整数"), ("lam", "波长 λ", "nm")],
        "solve": solve_grating,
    },
    {
        "key": "young",
        "name": "杨氏双缝干涉条纹间距",
        "formula": "Δx = λ·L / d",
        "symbols": [("lam", "波长 λ", "nm"), ("L", "缝屏距离 L", "m"),
                    ("d", "缝间距 d", "mm"), ("dx", "条纹间距 Δx", "mm")],
        "solve": solve_young,
    },
    {
        "key": "single_slit",
        "name": "单缝衍射暗纹条件",
        "formula": "a·sinθ = m·λ",
        "symbols": [("a", "缝宽 a", "mm"), ("theta", "衍射角 θ", "°"),
                    ("m", "暗纹级次 m", "整数"), ("lam", "波长 λ", "nm")],
        "solve": solve_single_slit,
    },
    {
        "key": "photon",
        "name": "光子能量",
        "formula": "E = h·c / λ",
        "symbols": [("lam", "波长 λ", "nm"), ("E_eV", "光子能量 E", "eV")],
        "solve": solve_photon,
    },
    {
        "key": "wave_freq",
        "name": "波长-频率关系",
        "formula": "λ·ν = c",
        "symbols": [("lam", "波长 λ", "nm"), ("nu", "频率 ν", "THz")],
        "solve": solve_wave_freq,
    },
    {
        "key": "rayleigh",
        "name": "瑞利判据（角分辨率）",
        "formula": "θ = 1.22·λ / D",
        "symbols": [("lam", "波长 λ", "nm"), ("D", "通光孔径 D", "mm"),
                    ("theta", "角分辨率 θ", "角秒″")],
        "solve": solve_rayleigh,
    },
    {
        "key": "na",
        "name": "数值孔径",
        "formula": "NA = n·sinα",
        "symbols": [("n", "介质折射率 n", ""), ("alpha", "孔径角 α", "°"), ("NA", "数值孔径 NA", "")],
        "solve": solve_na,
    },
    {
        "key": "brewster",
        "name": "布儒斯特角",
        "formula": "tanθB = n2 / n1",
        "symbols": [("thetaB", "布儒斯特角 θB", "°"), ("n1", "折射率 n1", ""), ("n2", "折射率 n2", "")],
        "solve": solve_brewster,
    },
    {
        "key": "critical",
        "name": "全反射临界角",
        "formula": "sinθC = n2 / n1",
        "symbols": [("thetaC", "临界角 θC", "°"), ("n1", "光密介质折射率 n1", ""), ("n2", "光疏介质折射率 n2", "")],
        "solve": solve_critical,
    },
    {
        "key": "lens_combo",
        "name": "密贴透镜组等效焦距",
        "formula": "1/f = 1/f1 + 1/f2",
        "symbols": [("f1", "透镜1焦距 f1", "cm"), ("f2", "透镜2焦距 f2", "cm"), ("f", "等效焦距 f", "cm")],
        "solve": solve_lens_combo,
    },
    {
        "key": "magnification",
        "name": "薄透镜横向放大率",
        "formula": "M = v / u",
        "symbols": [("M", "放大率 M", ""), ("v", "像距 v", "cm"), ("u", "物距 u", "cm")],
        "solve": solve_magnification,
    },
    {
        "key": "beer",
        "name": "朗伯-比尔吸收定律",
        "formula": "I = I0·exp(-μx)",
        "symbols": [("I", "出射光强 I", "相对值"), ("I0", "入射光强 I0", "相对值"),
                    ("mu", "吸收系数 μ", "1/cm"), ("x", "光程 x", "cm")],
        "solve": solve_beer,
    },
]

# 供界面使用的名称列表
FORMULA_NAMES = [f["name"] for f in FORMULAS]
FORMULA_BY_KEY = {f["key"]: f for f in FORMULAS}


def get_formula(name):
    """按中文名称查找公式记录。"""
    for f in FORMULAS:
        if f["name"] == name:
            return f
    raise KeyError(f"未找到公式：{name}")


if __name__ == "__main__":
    # 简单自检：手动运行 python core/formulas.py 可验证
    res, _ = solve_thin_lens(f=None, u=20.0, v=30.0)
    print("薄透镜 f =", round(res["f"], 4), "cm（期望 12.0）")
    res, _ = solve_snell(n1=1.0, theta1=30.0, n2=1.5, theta2=None)
    print("折射角 θ2 =", round(res["theta2"], 4), "°（期望约 19.4712）")
    res, _ = solve_grating(d=1.0, theta=None, m=1, lam=500.0)
    print("衍射角 θ =", round(res["theta"], 4), "°（期望约 30.0）")

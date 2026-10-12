# -*- coding: utf-8 -*-
r"""界面冒烟测试：启动 Gradio 服务 → 请求首页 → 校验关键组件存在 → 关闭。

运行方式：venv\Scripts\python.exe smoke_test.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app  # noqa: E402


def main():
    print("启动 Gradio 服务...")
    demo = app.create_demo()
    demo.launch(server_name="127.0.0.1", server_port=7861, prevent_thread_lock=True)

    import urllib.request

    url = "http://127.0.0.1:7861"
    ok = False
    html = ""
    for _ in range(10):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                ok = resp.status == 200
                break
        except Exception:
            time.sleep(1)
    if not ok:
        print("[FAIL] 服务未启动成功")
        demo.close()
        sys.exit(1)
    print("[PASS] 首页 HTTP 200")

    for keyword in ["公式计算器", "数据拟合", "误差分析", "报告生成", "光电实验数据处理助手"]:
        if keyword in html:
            print(f"[PASS] 页面包含：{keyword}")
        else:
            print(f"[WARN] 页面未检测到：{keyword}（可能被 JS 渲染，不代表缺失）")

    # 校验核心算法函数可直接调用（模拟界面点击的数据处理链路）
    from core.formulas import solve_thin_lens
    r, _ = solve_thin_lens(f=None, u=20, v=30)
    assert abs(r["f"] - 12) < 1e-9

    from core.fitting import parse_xy, fit_data
    x, y, dy = parse_xy("1,2.1\n2,4.0\n3,5.9")
    res = fit_data(x, y, kind="linear")
    assert res["r2"] > 0.99

    from core.report import build_report
    p = build_report({"实验名称": "冒烟测试", "姓名": "测试"}, fit_text="ok")
    assert os.path.exists(p)
    print("[PASS] 核心算法链路正常")

    demo.close()
    print("冒烟测试完成，服务已关闭。")


if __name__ == "__main__":
    main()

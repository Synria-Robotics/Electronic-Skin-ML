"""
06_demo_recover_calibration — 恢复出厂标定数据
====================================================

【功能】
    将传感器标定数据恢复为固件内置的出厂标定参数。
    适用于以下场景：
    - 运行 02_demo_calibration.py 后标定内容错误，需要撤销
    - 运行 03_demo_configuration.py 清除了标定后需要恢复
    - 设备压力读数不准，怀疑标定被破坏

【原理】
    向寄存器 0x0070 写入命令值 119，固件收到后自动将各压力点的
    ADC-mN 对应关系恢复为出厂烧录的参数。
    恢复操作由固件完成，Python 无需知道具体参数值，因此对任何
    批次/型号的设备均有效。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 直接运行，无需额外操作：
           python 06_demo_recover_calibration.py

【注意事项】
    - 运行后将覆盖当前所有自定义标定数据，不可逆。
    - 如需保留当前自定义标定，请勿运行本脚本。

【依赖】
    pip install -r requirements.txt
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactile_sdk import TactilePressureSDK, CommunicationError

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1

# 11 个拟合点（用于恢复后读回验证）
FITTING_POINT_COUNT = 11


def main() -> None:
    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("设备连接成功！\n")

        # ----------------------------------------------------------------
        # 读取恢复前各拟合点 AD 值（用于对比）
        # ----------------------------------------------------------------
        print("恢复前各拟合点 AD 值：")
        before = []
        for idx in range(1, FITTING_POINT_COUNT + 1):
            sdk.calibration.set_fitting_point(idx)
            ad = sdk.calibration.get_fitting_point_ad()
            before.append(ad)
            print(f"  拟合点 {idx:>2d}: AD = {ad}")
        print()

        # ----------------------------------------------------------------
        # 执行恢复出厂标定
        # ----------------------------------------------------------------
        print("⚠️  警告：此操作将覆盖当前所有自定义标定数据，不可逆。")
        try:
            confirm = input("确认恢复出厂标定？(y/N): ").strip()
        except EOFError:
            confirm = "n"

        if confirm.lower() != "y":
            print("已取消，标定数据未改变。")
            return

        print("\n正在恢复出厂标定数据（写入寄存器 0x0070 = 119）…")
        sdk.calibration.clear()
        print("✓ 恢复命令已发送，等待固件处理…", end="", flush=True)
        time.sleep(0.5)  # 等待固件完成内部参数还原
        print(" 完成\n")

        # ----------------------------------------------------------------
        # 读取恢复后各拟合点 AD 值（验证）
        # ----------------------------------------------------------------
        print("恢复后各拟合点 AD 值：")
        changed = 0
        for idx in range(1, FITTING_POINT_COUNT + 1):
            sdk.calibration.set_fitting_point(idx)
            ad = sdk.calibration.get_fitting_point_ad()
            diff = ad - before[idx - 1]
            mark = f"  ← 变化 {diff:+d}" if diff != 0 else ""
            print(f"  拟合点 {idx:>2d}: AD = {ad}{mark}")
            if diff != 0:
                changed += 1

        print()
        if changed > 0:
            print(f"✓ 恢复完成（{changed} 个拟合点 AD 值发生变化，出厂标定已生效）")
        else:
            print("✓ 恢复完成（各拟合点 AD 值与恢复前一致，标定本已是出厂状态）")


if __name__ == "__main__":
    try:
        main()
    except CommunicationError as exc:
        print(f"\n通信错误: {exc}")
    except KeyboardInterrupt:
        print("\n程序已中断")
    except Exception as exc:
        print(f"\n发生错误: {exc}")
        import traceback
        traceback.print_exc()
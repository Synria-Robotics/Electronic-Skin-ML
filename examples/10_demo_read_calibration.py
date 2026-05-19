"""
10_demo_read_calibration — 读取当前标定参数
============================================

【功能】
    读取传感器当前存储的 11 个拟合点标定参数，包含：
    - pressure_value_type（当前输出模式：0=AD 值，1=标定值 mN）
    - 每个拟合点的 AD 值与对应压力值（mN）

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 运行脚本：
           python 10_demo_read_calibration.py

【依赖】
    pip install -r requirements.txt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactile_sdk import TactilePressureSDK, CommunicationError

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1

FITTING_POINT_COUNT = 11


def main() -> None:
    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("设备连接成功！\n")

        pvt = sdk.config.get_pressure_value_type()
        print(f"pressure_value_type = {pvt}  (0=AD 值, 1=标定值 mN)\n")

        print(f"{'点位':>6}  {'AD 值':>8}  {'pressure (mN)':>14}")
        print("-" * 36)
        for idx in range(1, FITTING_POINT_COUNT + 1):
            sdk.calibration.set_fitting_point(idx)
            ad   = sdk.calibration.get_fitting_point_ad()
            pres = sdk.calibration.get_fitting_point_pressure()
            print(f"point {idx:>2d}:  AD = {ad:>6},   pressure = {pres:>6} mN")


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

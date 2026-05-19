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
    向寄存器 0x0070 写入命令值 119，固件收到后自动将各拟合点的
    ADC 值恢复为出厂烧录的参数。但固件不会同步恢复压力(mN)值，
    因此本脚本在发送恢复命令后，会额外将 11 个拟合点的标准出厂
    压力值（0, 100, 200, … 1000 mN）一并写回设备，确保完整恢复。

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

from tactile_sdk import TactilePressureSDK, CommunicationError, CalibrationMode

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1

# 11 个拟合点（用于恢复后读回验证）
FITTING_POINT_COUNT = 11

# 出厂标准压力值：11 个点，0–1000 mN 等间距
FACTORY_PRESSURES = list(range(0, 1001, 100))  # [0, 100, 200, ..., 1000]


def main() -> None:
    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("设备连接成功！\n")

        # ----------------------------------------------------------------
        # 读取恢复前各拟合点 AD + pressure 值（用于对比）
        # ----------------------------------------------------------------
        print("=== Before recovery ===")
        pvt = sdk.config.get_pressure_value_type()
        print(f"pressure_value_type = {pvt} (0=AD, 1=mN)\n")
        print("before recovery fitting points:")
        before_ad  = []
        before_prs = []
        for idx in range(1, FITTING_POINT_COUNT + 1):
            sdk.calibration.set_fitting_point(idx)
            ad   = sdk.calibration.get_fitting_point_ad()
            pres = sdk.calibration.get_fitting_point_pressure()
            before_ad.append(ad)
            before_prs.append(pres)
            print(f"point {idx:>2d}: AD = {ad:>6}, pressure = {pres:>6} mN")
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
        # 写回出厂 pressure 值（固件恢复命令只恢复 AD，不恢复 pressure）
        # ----------------------------------------------------------------
        print("正在写回出厂压力值（0–1000 mN）…")
        sdk.calibration.set_mode(CalibrationMode.ALL_POINTS)
        for idx in range(1, FITTING_POINT_COUNT + 1):
            sdk.calibration.set_fitting_point(idx)
            ad = sdk.calibration.get_fitting_point_ad()          # 读取刚恢复的出厂 AD
            pres = FACTORY_PRESSURES[idx - 1]                    # 出厂 pressure
            sdk.calibration.set_fitting_point_pressure(pres)
            sdk.calibration.calibrate(ad_value=ad)               # 以出厂 AD + 出厂 pressure 提交
            print(f"  拟合点 {idx:>2d}: AD = {ad:>6}, pressure = {pres:>6} mN  ✓")
        print()

        # ----------------------------------------------------------------
        # 读取恢复后各拟合点 AD + pressure（验证）
        # ----------------------------------------------------------------
        print("=== Recover factory calibration ===")
        pvt_after = sdk.config.get_pressure_value_type()
        print(f"pressure_value_type after clear = {pvt_after} (0=AD, 1=mN)\n")
        print("after recovery fitting points:")
        ad_changed = 0
        for idx in range(1, FITTING_POINT_COUNT + 1):
            sdk.calibration.set_fitting_point(idx)
            ad   = sdk.calibration.get_fitting_point_ad()
            pres = sdk.calibration.get_fitting_point_pressure()
            diff = ad - before_ad[idx - 1]
            mark = f"  (AD {diff:+d})" if diff != 0 else ""
            print(f"point {idx:>2d}: AD = {ad:>6}, pressure = {pres:>6} mN{mark}")
            if diff != 0:
                ad_changed += 1

        print()
        if ad_changed > 0:
            print(f"✓ 恢复完成（{ad_changed} 个拟合点 AD 值发生变化，出厂标定已全部生效）")
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
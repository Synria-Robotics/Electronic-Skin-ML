"""
02_demo_calibration — 传感器标定
==========================================

【功能】
    演示三种标定方式，建立 AD 原始值与实际压力值（mN）之间的映射关系，
    使设备能够输出准确的标定压力值而非原始 AD 值。

    示例1 — 单点标定：
        对指定压力点的指定拟合点单独标定。
        每个压力点最多支持 11 个拟合点，施加已知压力后让设备采样记录 AD 值。

    示例2 — 多拟合点全部标定：
        不指定单个压力点，对所有压力点统一按多个拟合点（0、500、1000、2000 mN…）
        依次标定，适合批量标定整张传感器。

    示例3 — 清除标定（谨慎）：
        将标定数据恢复到出厂状态。清除后需重新运行
        example_recover_calibration.py 恢复备份数据，否则压力值将不准确。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 port 变量。
    2. 确认 slave_address 与设备拨码地址一致（默认为 1）。
    3. 标定前请在传感器对应压力点上施加精确已知的压力（mN）。
    4. 运行脚本：
           python 02_demo_calibration.py

【注意事项】
    - 标定模式 100 = 单点标定，101 = 全部标定。
    - use_sample=True 表示使用设备实时采样的 AD 值，False 则使用手动设置值。
    - 清除标定操作不可逆，请提前用 06_demo_recover_calibration.py 备份数据。

【依赖】
    pip install -r requirements.txt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactile_sdk import TactilePressureSDK, CommunicationError, CalibrationMode

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1


def main() -> None:
    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("设备连接成功！\n")

        # --- 读取当前标定配置 ---
        print("=" * 40)
        print("当前标定配置")
        print("=" * 40)
        status = sdk.calibration.get_status()
        mode_name = "全部标定" if status.mode == CalibrationMode.ALL_POINTS else "单点标定"
        print(f"标定模式  : {status.mode} ({mode_name})")
        print(f"当前压力点: {status.pressure_point}")
        print(f"当前拟合点: {status.fitting_point}")
        print()

        # ----------------------------------------------------------------
        # 示例1：单点标定
        # 针对指定压力点的指定拟合点单独采样标定
        # ----------------------------------------------------------------
        print("=" * 40)
        print("示例1：单点标定")
        print("=" * 40)
        try:
            sdk.calibration.set_mode(CalibrationMode.SINGLE_POINT)
            print("标定模式 → 单点标定")

            pressure_point = 1
            sdk.calibration.set_pressure_point(pressure_point)
            print(f"选择压力点: {pressure_point}")

            fitting_point = 1
            sdk.calibration.set_fitting_point(fitting_point)
            print(f"设置拟合点: {fitting_point}")

            pressure_value = 1000  # mN
            sdk.calibration.set_fitting_point_pressure(pressure_value)
            print(f"设置压力值: {pressure_value} mN")

            print("执行标定（设备实时采样 AD 值）...")
            sdk.calibration.calibrate(use_sample=True)
            print("标定完成")

            ad_value = sdk.calibration.get_fitting_point_ad()
            print(f"标定后 AD 值: {ad_value}")

        except CommunicationError as exc:
            print(f"标定失败: {exc}")
        print()

        # ----------------------------------------------------------------
        # 示例2：全部标定（多拟合点，对所有压力点统一应用）
        # ----------------------------------------------------------------
        print("=" * 40)
        print("示例2：多拟合点全部标定")
        print("=" * 40)
        try:
            sdk.calibration.set_mode(CalibrationMode.ALL_POINTS)
            print("标定模式 → 全部标定")

            calibration_points = [
                (1,    0),
                (2,  500),
                (3, 1000),
                (4, 2000),
            ]

            for fp_idx, pressure_mn in calibration_points:
                print(f"\n  拟合点 {fp_idx}，施加压力 {pressure_mn} mN")
                sdk.calibration.set_fitting_point(fp_idx)
                sdk.calibration.set_fitting_point_pressure(pressure_mn)
                sdk.calibration.calibrate(use_sample=True)
                ad_value = sdk.calibration.get_fitting_point_ad()
                print(f"  → AD 值: {ad_value}")

            print("\n多拟合点标定完成")

        except CommunicationError as exc:
            print(f"标定失败: {exc}")
        print()

        # ----------------------------------------------------------------
        # 示例3：清除标定（谨慎操作）
        # ----------------------------------------------------------------
        print("=" * 40)
        print("示例3：清除标定（谨慎）")
        print("=" * 40)
        try:
            response = input("是否清除标定信息（恢复出厂标定）？(y/N): ").strip()
        except EOFError:
            response = "n"

        if response.lower() == "y":
            try:
                sdk.calibration.clear()
                print("标定已清除，请运行 06_demo_recover_calibration.py 恢复出厂数据")
            except CommunicationError as exc:
                print(f"清除失败: {exc}")
        else:
            print("已取消")


if __name__ == "__main__":
    main()

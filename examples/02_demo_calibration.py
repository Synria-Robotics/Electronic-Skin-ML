"""
02_demo_calibration — 传感器标定
==========================================

【功能】
    用户手动输入 1–11 个标定点（压力 mN 及对应 AD 值），
    一键写入设备，建立 AD 原始值与实际压力值之间的映射关系。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 确认 SLAVE_ADDRESS 与设备拨码地址一致（默认为 1）。
    3. 运行脚本，按提示依次输入每个标定点的压力（0–1000 mN）和 AD 值。
    4. 输入完所有点后直接回车结束输入，脚本自动写入设备。

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


def input_calibration_points():
    """交互式输入标定点，返回 [(pressure_mn, ad_value), ...] 列表。"""
    print("请依次输入标定点（最多 11 个，压力范围 0–1000 mN）。")
    print("每行格式：  压力(mN) AD值  （用空格分隔）")
    print("输入完毕后直接按回车结束。\n")

    points = []
    for i in range(1, 12):
        while True:
            try:
                line = input(f"  标定点 {i:>2d}: ").strip()
            except EOFError:
                line = ""

            if line == "":
                return points

            parts = line.split()
            if len(parts) != 2:
                print("    格式错误，请输入两个数字，例如：500 1729")
                continue

            try:
                pressure = int(parts[0])
                ad = int(parts[1])
            except ValueError:
                print("    请输入整数。")
                continue

            if not (0 <= pressure <= 1000):
                print("    压力须在 0–1000 mN 范围内。")
                continue

            if not (0 <= ad <= 65535):
                print("    AD 值须在 0–65535 范围内。")
                continue

            points.append((pressure, ad))
            break

    return points


def main() -> None:
    points = input_calibration_points()

    if not points:
        print("未输入任何标定点，已退出。")
        return

    print(f"\n共输入 {len(points)} 个标定点：")
    print(f"  {'编号':>4}  {'压力(mN)':>8}  {'AD值':>6}")
    for idx, (p, a) in enumerate(points, 1):
        print(f"  {idx:>4}  {p:>8}  {a:>6}")

    try:
        confirm = input("\n确认写入设备？(y/N): ").strip()
    except EOFError:
        confirm = "n"

    if confirm.lower() != "y":
        print("已取消。")
        return

    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("\n设备连接成功，开始写入标定数据…\n")
        try:
            sdk.calibration.set_mode(CalibrationMode.ALL_POINTS)
            for idx, (pressure, ad) in enumerate(points, 1):
                sdk.calibration.set_fitting_point(idx)
                sdk.calibration.set_fitting_point_pressure(pressure)
                sdk.calibration.calibrate(ad_value=ad)
                print(f"  拟合点 {idx:>2d} 写入完成：{pressure} mN → AD {ad}")
            print("\n标定写入完成。")
        except CommunicationError as exc:
            print(f"写入失败: {exc}")


if __name__ == "__main__":
    main()

"""
03_demo_configuration — 设备参数配置
======================================

【功能】
    演示如何读取和修改传感器设备的常用配置参数：

    1. 读取当前配置
        显示设备地址、压力值类型（标定值 / AD值）、AD屏蔽值。

    2. 设置压力值类型
        切换设备输出模式：
        - 1 = 标定值（经过标定换算的真实压力，单位 mN）
        - 0 = AD值（传感器原始模拟量，用于调试）

    3. 设置 AD 屏蔽值
        低于该阈值的 AD 采样视为无压力（噪声过滤）。
        示例设为 100，可根据实际噪声水平调整。

    4. 修改设备 Modbus 地址（可选，交互确认）
        通过广播地址将设备地址改为新值（1～247）。
        修改后下次连接必须使用新地址，请记录保存。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 确认 SLAVE_ADDRESS 与设备拨码地址一致（默认为 1）。
    3. 运行脚本：
           python 03_demo_configuration.py

【注意事项】
    - 修改设备地址后，原地址将失效，请谨慎操作。
    - AD 屏蔽值设置过高会导致小压力无法检测，建议从小值开始调整。

【依赖】
    pip install -r requirements.txt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactile_sdk import TactilePressureSDK, CommunicationError, DeviceConnectionError

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1


def main() -> None:
    try:
        sdk = TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS)
        sdk.connect()
    except DeviceConnectionError as exc:
        print(f"连接失败: {exc}")
        return

    print("设备连接成功！\n")

    try:
        # --- 读取当前配置 ---
        print("=" * 40)
        print("当前配置")
        print("=" * 40)
        print(f"设备地址    : {sdk.device.get_address()}")
        print(f"压力值类型  : {'标定值 (mN)' if sdk.config.get_pressure_value_type() == 1 else 'AD 原始值'}")
        print(f"AD 屏蔽值   : {sdk.config.get_ad_mask_value()}")
        print()

        # --- 配置示例 ---
        print("=" * 40)
        print("配置示例")
        print("=" * 40)

        # 1. 设置压力值类型
        print("1. 设置压力值类型 → 标定值 (1)...")
        try:
            sdk.config.set_pressure_value_type(1)
            val = sdk.config.get_pressure_value_type()
            status = "✓" if val == 1 else "✗ 设置失败"
            print(f"   结果: {'标定值' if val == 1 else 'AD 值'} [{status}]")
        except CommunicationError as exc:
            print(f"   设置失败: {exc}")

        # 2. 设置 AD 屏蔽值
        print("2. 设置 AD 屏蔽值 → 100...")
        try:
            sdk.config.set_ad_mask_value(100)
            val = sdk.config.get_ad_mask_value()
            status = "✓" if val == 100 else "✗ 设置失败"
            print(f"   结果: {val} [{status}]")
        except CommunicationError as exc:
            print(f"   设置失败: {exc}")

        print()

        # --- 设备地址修改（可选） ---
        print("=" * 40)
        print("设备 Modbus 地址修改（可选）")
        print("=" * 40)
        print(f"当前设备地址: {sdk.device.get_address()}")
        print("注意：修改后需用新地址重新连接，请谨慎操作。")

        try:
            response = input("\n是否修改设备地址？(y/N): ").strip()
        except EOFError:
            response = "n"

        if response.lower() == "y":
            try:
                new_addr_str = input("请输入新地址 (1-247): ").strip()
                new_addr = int(new_addr_str)
                sdk.device.set_address(new_addr, use_broadcast=True)
                print(f"设备地址已修改为 {new_addr}，下次连接请使用新地址。")
            except (ValueError, EOFError):
                print("输入无效，已取消。")
            except Exception as exc:
                print(f"修改地址失败: {exc}")
        else:
            print("已跳过地址修改。")

        print("\n配置操作完成。")

    except Exception as exc:
        print(f"操作出错: {exc}")
    finally:
        sdk.disconnect()
        print("设备已断开连接。")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

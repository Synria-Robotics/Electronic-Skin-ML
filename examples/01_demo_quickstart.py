"""
01_demo_quickstart — 快速入门：设备连接与基本信息读取
======================================================

【功能】
    演示如何连接触觉压力传感器，并读取设备基本信息和常用配置寄存器。

【适用场景】
    初次使用 SDK，验证设备是否正常连接并能正确通信。

【使用方法】
    1. 将传感器通过 USB 连接到电脑。
    2. 在设备管理器中确认串口号（如 COM6），修改下方 PORT 变量。
    3. 确认 SLAVE_ADDRESS 与设备拨码地址一致（默认为 1）。
    4. 运行脚本：
           python 01_demo_quickstart.py

【输出内容】
    - 设备型号、协议编号/版本、App 版本
    - 设备地址、压力点总数、主动上传频率
    - 压力值类型（标定值 / AD 值）、传感器点面积、AD 屏蔽值

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
PORT = "COM6"       # Windows: "COM6" | Linux/Mac: "/dev/ttyUSB0"
SLAVE_ADDRESS = 1


def main() -> None:
    sdk = TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS)

    try:
        print("正在连接设备...")
        sdk.connect()
        print("设备连接成功！\n")

        # --- 设备信息 ---
        print("=" * 40)
        print("设备信息")
        print("=" * 40)
        info = sdk.device.get_info()
        print(f"设备型号 : {info.device_model}")
        print(f"协议编号 : {info.protocol_number}")
        print(f"协议版本 : {info.protocol_version}")
        print(f"App 版本 : {info.app_version}")
        print()

        # --- 基本配置 ---
        print("=" * 40)
        print("基本配置")
        print("=" * 40)
        print(f"设备地址    : {sdk.device.get_address()}")
        print(f"压力点总数  : {sdk.config.get_pressure_point_count()}")
        print(f"主动上传    : {'开启' if sdk.config.get_auto_upload_flag() else '关闭'}")
        print(f"上传频率    : {sdk.config.get_auto_upload_frequency()} Hz")
        print(f"压力值类型  : {'标定值 (mN)' if sdk.config.get_pressure_value_type() == 1 else 'AD 原始值'}")
        print(f"传感器点面积: {sdk.config.get_sensor_point_area()} mm²")
        print(f"AD 屏蔽值   : {sdk.config.get_ad_mask_value()}")

    except DeviceConnectionError as exc:
        print(f"连接失败: {exc}")
    except CommunicationError as exc:
        print(f"通信错误: {exc}")
    except Exception as exc:
        print(f"未知错误: {exc}")
    finally:
        sdk.disconnect()
        print("\n设备已断开连接")


if __name__ == "__main__":
    main()

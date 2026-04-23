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
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 port 变量。
    2. 确认 slave_address 与设备拨码地址一致（默认为 1）。
    3. 运行脚本：
           python 03_demo_configuration.py

【注意事项】
    - 修改设备地址后，原地址将失效，请谨慎操作。
    - AD 屏蔽值设置过高会导致小压力无法检测，建议从小值开始调整。

【依赖】
    pip install -r requirements.txt
"""

from sdk import TactilePressureSDK
from sdk.modbus_rtu import ModbusRTUError


def main():
    # 配置串口和从设备地址
    port = "COM6"  # 根据实际情况修改
    slave_address = 1

    # 连接设备
    try:
        sdk = TactilePressureSDK(port=port, slave_address=slave_address)
        sdk.connect()
    except Exception as e:
        print(f"连接失败: {e}")
        return

    print("设备连接成功！\n")

    try:
        # 读取当前配置
        print("=== 当前配置 ===")
        print(f"设备地址: {sdk.get_device_address()}")
        print(f"压力值类型: {'标定值' if sdk.get_pressure_value_type() == 1 else 'AD值'}")
        print(f"AD屏蔽值: {sdk.get_ad_mask_value()}")
        print()

        # 配置示例
        print("=== 配置示例 ===")

        # 1. 设置压力值类型
        print("1. 设置压力值类型...")
        try:
            sdk.set_pressure_value_type(1)  # 1=标定值, 0=AD值
            val = sdk.get_pressure_value_type()
            print(f"   压力值类型已设置为: {'标定值' if val == 1 else 'AD值'} ({'✓' if val == 1 else '✗ 设置失败'})")
        except Exception as e:
            print(f"   设置压力值类型失败: {e}")

        # 2. 设置AD屏蔽值
        print("2. 设置AD屏蔽值...")
        try:
            sdk.set_ad_mask_value(100)
            val = sdk.get_ad_mask_value()
            print(f"   AD屏蔽值已设置为: {val} ({'✓' if val == 100 else '✗ 设置失败'})")
        except Exception as e:
            print(f"   设置AD屏蔽值失败: {e}")

        print()

        # 设备地址修改（可选，交互确认）
        print("=== 设备地址修改（可选）===")
        print(f"当前设备地址: {sdk.get_device_address()}")
        print("注意：修改后需用新地址重新连接，请谨慎操作。")

        try:
            response = input("是否修改设备地址？(y/N): ").strip()
        except EOFError:
            response = "n"

        if response.lower() == 'y':
            try:
                new_address_str = input("请输入新地址 (1-247): ").strip()
                new_address = int(new_address_str)
                if 1 <= new_address <= 247:
                    sdk.set_device_address(new_address, use_broadcast=True)
                    print(f"设备地址已修改为 {new_address}，下次连接请使用新地址。")
                else:
                    print("地址超出范围 (1-247)，已取消。")
            except (ValueError, EOFError):
                print("输入无效，已取消。")
            except Exception as e:
                print(f"修改地址失败: {e}")
        else:
            print("已跳过地址修改。")

        print("\n配置完成。")

    except Exception as e:
        print(f"操作出错: {e}")
    finally:
        sdk.disconnect()
        print("设备已断开连接。")


if __name__ == "__main__":
    main()

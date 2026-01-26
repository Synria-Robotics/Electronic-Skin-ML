"""
设备配置示例
"""

from sdk import TactilePressureSDK
from sdk.modbus_rtu import ModbusRTUError


def main():
    # 配置串口和从设备地址
    port = "COM7"  # 根据实际情况修改
    slave_address = 1

    with TactilePressureSDK(port=port, slave_address=slave_address) as sdk:
        print("设备连接成功！\n")
        
        # 读取当前配置
        print("=== 当前配置 ===")
        print(f"设备地址: {sdk.get_device_address()}")
        print(f"压力值类型: {'标定值' if sdk.get_pressure_value_type() == 1 else 'AD值'}")
        print(f"AD屏蔽值: {sdk.get_ad_mask_value()}")
        auto_zero_supported = True
        
        # 配置示例
        print("=== 配置示例 ===")
        
        # 1. 设置压力值类型
        print("1. 设置压力值类型...")
        sdk.set_pressure_value_type(1)  # 设置为标定值
        print("   压力值类型已设置为标定值")
        
        # 2. 设置AD屏蔽值
        print("2. 设置AD屏蔽值...")
        sdk.set_ad_mask_value(100)  # 设置AD屏蔽值为100
        print("   AD屏蔽值已设置为 100")
        
        # 验证配置
        print("=== 验证配置 ===")
        print(f"压力值类型: {sdk.get_pressure_value_type()} (期望: 1)")
        print(f"AD屏蔽值: {sdk.get_ad_mask_value()} (期望: 100)")
        print()
        
        # 设备地址修改示例（使用广播地址）
        print("=== 设备地址修改示例 ===")
        print("注意：修改设备地址需要使用广播地址")
        print("当前设备地址:", sdk.get_device_address())
        
        response = input("是否修改设备地址？(y/N): ")
        if response.lower() == 'y':
            try:
                new_address = int(input("请输入新地址 (1-247): "))
                if 1 <= new_address <= 247:
                    # 使用广播地址修改设备地址
                    sdk.set_device_address(new_address, use_broadcast=True)
                    print(f"设备地址已修改为 {new_address}")
                    print("注意：如果修改成功，下次连接需要使用新地址")
                else:
                    print("地址范围无效")
            except ValueError:
                print("输入无效")
            except Exception as e:
                print(f"修改地址失败: {e}")


if __name__ == "__main__":
    main()

"""
01_demo_quickstart — 快速入门：设备连接与基本信息读取
======================================================

【功能】
    演示如何连接触觉压力传感器，并读取设备基本信息和常用配置寄存器。

【适用场景】
    初次使用 SDK，验证设备是否正常连接并能正确通信。

【使用方法】
    1. 将传感器通过 USB 连接到电脑。
    2. 在设备管理器中确认串口号（如 COM6），修改下方 port 变量。
    3. 确认 slave_address 与设备拨码地址一致（默认为 1）。
    4. 运行脚本：
           python 01_demo_quickstart.py

【输出内容】
    - 设备型号、协议编号/版本、App 版本
    - 设备地址、压力点总数、主动上传频率
    - 压力值类型（标定值 / AD 值）、传感器点面积、AD 屏蔽值

【依赖】
    pip install -r requirements.txt
"""

from sdk import TactilePressureSDK


def main():
    # 配置串口和从设备地址
    port = "COM6"  # Windows系统，Linux/Mac使用 "/dev/ttyUSB0" 或 "/dev/ttyACM0"
    slave_address = 1
    
    # 创建SDK实例
    sdk = TactilePressureSDK(port=port, slave_address=slave_address)
    
    try:
        # 连接设备
        print("正在连接设备...")
        sdk.connect()
        print("设备连接成功！\n")
        
        # 读取设备信息
        print("=== 设备信息 ===")
        device_info = sdk.get_device_info()
        print(f"设备型号: {device_info['device_model']}")
        print(f"协议编号: {device_info['protocol_number']}")
        print(f"协议版本: {device_info['protocol_version']}")
        print(f"App版本: {device_info['app_version']}")
        print()
        
        # 读取基本配置
        print("=== 基本配置 ===")
        print(f"设备地址: {sdk.get_device_address()}")
        print(f"压力点总数: {sdk.get_pressure_point_count()}")
        print(f"主动上传标志: {sdk.get_auto_upload_flag()}")
        print(f"主动上传频率: {sdk.get_auto_upload_frequency()} Hz")
        print(f"压力值类型: {'标定值' if sdk.get_pressure_value_type() == 1 else 'AD值'}")
        print(f"传感器点面积: {sdk.get_sensor_point_area()} 平方毫米")
        print()
        
        # 读取寄存器示例
        print("=== 寄存器读取示例 ===")
        ad_mask = sdk.get_ad_mask_value()
        print(f"AD屏蔽值: {ad_mask}")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 断开连接
        sdk.disconnect()
        print("\n设备已断开连接")


if __name__ == "__main__":
    main()

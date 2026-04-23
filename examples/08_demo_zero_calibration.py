"""
08_demo_zero_calibration — 传感器归零功能
==========================================

【功能】
    演示传感器的三种归零操作，用于消除传感器在无负载状态下的基线偏移：

    演示1 — 上电自动归零
        启用或禁用"每次上电时自动将当前压力值归零"的功能。
        注意：对应寄存器为只写，设置后无法读取确认，需重启设备才能验证效果。

    演示2 — 手动动态归零
        在设备运行中立即触发归零，将当前压力值清零。
        执行前建议确保传感器表面无负载。
        归零前后会自动读取压力值并对比变化。

    演示3 — 重置动态归零
        撤销之前的动态归零操作，恢复到出厂零点状态。
        适用于需要取消之前归零的场景。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 port 变量。
    2. 运行脚本并按照提示操作：
           python 08_demo_zero_calibration.py
    3. 演示2 执行前请确保传感器表面无负载，按回车键触发归零。

【注意事项】
    - 动态归零会立即生效，重置后压力值恢复到原始基线，非物理标定值变化。
    - 上电自动归零仅在下次重启后生效。

【依赖】
    pip install -r requirements.txt
"""

import time
from sdk import TactilePressureSDK
from sdk.modbus_rtu import ModbusRTUError


def main():
    # 配置串口和从设备地址
    port = "COM6"  # 根据实际情况修改
    slave_address = 1

    with TactilePressureSDK(port=port, slave_address=slave_address) as sdk:
        print("设备连接成功！\n")
        
        # 读取设备信息
        info = sdk.get_device_info()
        print(f"设备型号: {info['device_model']}")
        print(f"协议版本: {info['protocol_version']}\n")
        
        # 设置为标定值模式（推荐用于观察归零效果）
        print("设置压力值类型为标定值...")
        sdk.set_pressure_value_type(1)  # 1 = 标定值
        print("✓ 已设置为标定值模式\n")
        
        # ==================== 演示1：上电自动归零功能 ====================
        print("=" * 60)
        print("演示1：上电自动归零功能")
        print("=" * 60)
        print()
        print("上电自动归零功能说明：")
        print("- 启用后，设备每次上电时会自动将当前压力值归零")
        print("- 适用于需要在无压力状态下启动的应用场景")
        print("- ⚠️ 重要：该寄存器(0x0011)为只写寄存器，不支持读取状态")
        print("- 写入后无法验证，需要重启设备才能观察效果\n")
        
        # 设置上电自动归零（启用）
        print("设置上电自动归零：启用")
        sdk.set_pressure_auto_zero_enable(True)
        print("✓ 已发送启用命令（寄存器只写，无法读取确认）")
        print("  说明：设备下次上电时会自动归零\n")
        
        # 提示用户
        print("提示：")
        print("1. 该设置会立即写入设备")
        print("2. 由于寄存器只写，无法读取当前状态")
        print("3. 要验证效果，需要重启设备并观察上电后的压力值")
        print()
        
        # 可以选择禁用
        response = input("是否禁用上电自动归零？(y/N): ")
        if response.lower() == 'y':
            sdk.set_pressure_auto_zero_enable(False)
            print("✓ 已发送禁用命令")
            print("  说明：设备下次上电时不会自动归零\n")
        else:
            print("保持启用状态\n")
        
        # ==================== 演示2：手动动态归零功能 ====================
        print("=" * 60)
        print("演示2：手动动态归零功能")
        print("=" * 60)
        print()
        print("手动动态归零功能说明：")
        print("- 在不重启设备的情况下，立即将当前压力值归零")
        print("- 适用于需要重新设定零点的场景")
        print("- 建议在传感器无负载时执行归零操作\n")
        
        # 读取归零前的压力值
        print("步骤1：读取归零前的压力值...")
        pressure_before = sdk.read_all_pressure_values()
        total_before = sum(pressure_before)
        print(f"归零前总压力: {total_before} (单位: mN)")
        print(f"前10个压力点: {pressure_before[:10]}")
        print()
        
        # 提示用户
        print("请确保传感器表面无负载（或处于需要归零的状态）")
        input("准备好后，按回车键执行动态归零...")
        
        # 触发动态归零
        print("\n步骤2：触发动态归零...")
        sdk.trigger_pressure_dynamic_zero()
        print("✓ 已发送动态归零命令")
        
        # 等待归零完成
        print("等待归零操作完成...", end="", flush=True)
        time.sleep(3.0)  # 设备调零需要静止一段时间
        print(" 完成\n")
        
        # 读取归零后的压力值
        print("步骤3：读取归零后的压力值...")
        pressure_after = sdk.read_all_pressure_values()
        total_after = sum(pressure_after)
        print(f"归零后总压力: {total_after} (单位: mN)")
        print(f"前10个压力点: {pressure_after[:10]}")
        print()
        
        # 显示变化
        print("归零效果：")
        print(f"总压力变化: {total_before} → {total_after} (减少了 {total_before - total_after})")
        if abs(total_after) < abs(total_before):
            print("✓ 归零成功！压力值已接近零点")
        else:
            print("! 归零后压力值未明显变化，可能传感器上有负载")
        print()
        
        # ==================== 演示3：重置动态归零功能 ====================
        print("=" * 60)
        print("演示3：重置动态归零功能")
        print("=" * 60)
        print()
        print("重置动态归零功能说明：")
        print("- 将之前的动态归零调整清除，恢复到出厂归零状态")
        print("- 适用于需要取消之前归零操作的场景")
        print("- 执行后，压力值会回到未归零时的原始状态\n")
        
        # 询问用户是否要演示重置功能
        response = input("是否演示重置动态归零功能？(y/N): ")
        if response.lower() == 'y':
            # 读取重置前的压力值
            print("\n步骤1：读取当前压力值...")
            pressure_before_reset = sdk.read_all_pressure_values()
            total_before_reset = sum(pressure_before_reset)
            print(f"重置前总压力: {total_before_reset} (单位: mN)")
            print(f"前10个压力点: {pressure_before_reset[:10]}")
            print()
            
            # 触发重置
            print("步骤2：触发重置动态归零...")
            sdk.reset_pressure_dynamic_zero()
            print("✓ 已发送重置命令")
            
            # 等待重置完成
            print("等待重置操作完成...", end="", flush=True)
            time.sleep(3.0)
            print(" 完成\n")
            
            # 读取重置后的压力值
            print("步骤3：读取重置后的压力值...")
            pressure_after_reset = sdk.read_all_pressure_values()
            total_after_reset = sum(pressure_after_reset)
            print(f"重置后总压力: {total_after_reset} (单位: mN)")
            print(f"前10个压力点: {pressure_after_reset[:10]}")
            print()
            
            # 显示变化
            print("重置效果：")
            print(f"总压力变化: {total_before_reset} → {total_after_reset} (变化了 {total_after_reset - total_before_reset})")
            if abs(total_after_reset) > abs(total_before_reset):
                print("✓ 重置成功！压力值已恢复到出厂归零状态")
            else:
                print("! 压力值未明显变化")
            print()
        else:
            print("跳过重置演示\n")


if __name__ == "__main__":
    try:
        main()
    except ModbusRTUError as e:
        print(f"\n通信错误: {e}")
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

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
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 运行脚本并按照提示操作：
           python 08_demo_zero_calibration.py
    3. 演示2 执行前请确保传感器表面无负载，按回车键触发归零。

【注意事项】
    - 动态归零会立即生效，重置后压力值恢复到原始基线，非物理标定值变化。
    - 上电自动归零仅在下次重启后生效。

【依赖】
    pip install -r requirements.txt
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactile_sdk import TactilePressureSDK, CommunicationError

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1


def main() -> None:
    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("设备连接成功！\n")

        info = sdk.device.get_info()
        print(f"设备型号: {info.device_model}")
        print(f"协议版本: {info.protocol_version}\n")

        sdk.config.set_pressure_value_type(1)
        print("✓ 已设置为标定值模式\n")

        # ----------------------------------------------------------------
        # 演示1：上电自动归零
        # ----------------------------------------------------------------
        print("=" * 60)
        print("演示1：上电自动归零")
        print("=" * 60)
        print()
        print("说明：启用后，设备每次上电时自动将当前压力值归零。")
        print("⚠️  寄存器 0x0011 为只写，写入后无法读取确认，重启方可验证。\n")

        sdk.config.set_auto_zero_enable(True)
        print("✓ 已发送启用命令（下次上电时自动归零）\n")

        try:
            response = input("是否禁用上电自动归零？(y/N): ").strip()
        except EOFError:
            response = "n"

        if response.lower() == "y":
            sdk.config.set_auto_zero_enable(False)
            print("✓ 已发送禁用命令\n")
        else:
            print("保持启用状态\n")

        # ----------------------------------------------------------------
        # 演示2：手动动态归零
        # ----------------------------------------------------------------
        print("=" * 60)
        print("演示2：手动动态归零")
        print("=" * 60)
        print()
        print("说明：立即触发归零，将当前压力值清零。")
        print("建议在传感器表面无负载时执行。\n")

        frame_before = sdk.pressure.read_all()
        print(f"归零前总压力: {frame_before.total_pressure} mN")
        print(f"前10点: {frame_before.values[:10]}\n")

        try:
            input("准备好后，按回车键执行动态归零…")
        except EOFError:
            pass

        sdk.config.trigger_dynamic_zero()
        print("✓ 已发送动态归零命令")

        print("等待归零完成…", end="", flush=True)
        time.sleep(3.0)
        print(" 完成\n")

        frame_after = sdk.pressure.read_all()
        print(f"归零后总压力: {frame_after.total_pressure} mN")
        print(f"前10点: {frame_after.values[:10]}\n")

        diff = frame_before.total_pressure - frame_after.total_pressure
        print(f"总压力变化: {frame_before.total_pressure} → {frame_after.total_pressure}（减少 {diff}）")
        if frame_after.total_pressure < frame_before.total_pressure:
            print("✓ 归零成功")
        else:
            print("! 压力值未明显变化，请确认传感器无负载")
        print()

        # ----------------------------------------------------------------
        # 演示3：重置动态归零
        # ----------------------------------------------------------------
        print("=" * 60)
        print("演示3：重置动态归零")
        print("=" * 60)
        print()
        print("说明：撤销之前的动态归零，恢复出厂零点状态。\n")

        try:
            response = input("是否演示重置动态归零？(y/N): ").strip()
        except EOFError:
            response = "n"

        if response.lower() == "y":
            before_reset = sdk.pressure.read_all()
            print(f"\n重置前总压力: {before_reset.total_pressure} mN")

            sdk.config.reset_dynamic_zero()
            print("✓ 已发送重置命令")

            print("等待重置完成…", end="", flush=True)
            time.sleep(3.0)
            print(" 完成\n")

            after_reset = sdk.pressure.read_all()
            print(f"重置后总压力: {after_reset.total_pressure} mN")
            diff = after_reset.total_pressure - before_reset.total_pressure
            print(f"总压力变化: {before_reset.total_pressure} → {after_reset.total_pressure}（变化 {diff}）")
            print("✓ 重置完成（压力值已恢复到出厂归零状态）")
        else:
            print("跳过重置演示")


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
        traceback.print_exc()

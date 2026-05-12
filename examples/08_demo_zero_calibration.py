"""
08_demo_zero_calibration — 传感器归零功能
==========================================

【功能】
    演示传感器的三种归零操作，用于消除传感器在无负载状态下的基线偏移：

    演示1 — 上电自动归零
        启用或禁用"每次上电时自动将当前压力值归零"的功能。
        注意：对应寄存器为只写，设置后无法读取确认，需重启设备才能验证效果。

    演示2 — 手动动态归零
        在设备运行中立即触发归零，将触发时刻各点的读取值存为软件基线。
        后续所有压力读取均自动逐点减去该基线，效果等同于重新插拔。
        执行前建议确保传感器表面无负载。

    演示3 — 重置动态归零
        撤销之前的动态归零操作，恢复到出厂零点状态。
        适用于需要取消之前归零的场景。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 运行脚本并按照提示操作：
           python 08_demo_zero_calibration.py
    3. 演示2 执行前请确保传感器表面无负载，按回车键触发归零。

【注意事项】
    - 动态归零会立即生效：将触发时刻的各点读取值存为软件基线，后续所有读取均自动减去该基线。
    - 重置后压力值恢复到上电时的硬件基线状态（原始偏移量）。
    - 上电自动归零仅在下次重启后生效。

【依赖】
    pip install -r requirements.txt
"""

import os
import sys

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
        print("说明：立即触发归零，将触发时各点的当前读取值存为软件基线。")
        print("建议在传感器表面无负载时执行，效果等同于重新插拔。\n")

        frame_before = sdk.pressure.read_all()
        print(f"归零前总压力: {frame_before.total_pressure} mN")
        print(f"前10点: {frame_before.values[:10]}\n")

        try:
            input("准备好后，按回车键执行动态归零…")
        except EOFError:
            pass

        sdk.config.trigger_dynamic_zero()
        # trigger_dynamic_zero() 内部已完成：发送硬件命令 → 等待90ms → 读取并存儲当前60点为软件基线
        print("✓ 归零完成（硬件命令已发送 + 软件基线已记录）\n")

        frame_after = sdk.pressure.read_all()
        print(f"归零后总压力: {frame_after.total_pressure} mN（预期为 0）")
        print(f"前10点: {frame_after.values[:10]}\n")

        cleared = frame_before.total_pressure
        print(f"已清除基线偏移: {cleared} mN")
        print(f"总压力变化: {frame_before.total_pressure} → {frame_after.total_pressure}")
        print("✓ 归零成功（软件层已按基线补偿，后续读取均自动减去该偏移）")
        print()

        # ----------------------------------------------------------------
        # 演示3：重置动态归零
        # ----------------------------------------------------------------
        print("=" * 60)
        print("演示3：重置动态归零")
        print("=" * 60)
        print()
        print("说明：清除软件基线，压力值恢复为上电时硬件基线上的原始偏移量。\n")

        try:
            response = input("是否演示重置动态归零？(y/N): ").strip()
        except EOFError:
            response = "n"

        if response.lower() == "y":
            before_reset = sdk.pressure.read_all()
            print(f"\n重置前总压力: {before_reset.total_pressure} mN")

            sdk.config.reset_dynamic_zero()
            # reset_dynamic_zero() 是瞬时操作：发送硬件命令 + 立即清除软件基线
            print("✓ 已清除软件基线（硬件命令已发送）\n")

            after_reset = sdk.pressure.read_all()
            print(f"重置后总压力: {after_reset.total_pressure} mN（已恢复为上电硬件基线）")
            recovered = after_reset.total_pressure - before_reset.total_pressure
            print(f"总压力变化: {before_reset.total_pressure} → {after_reset.total_pressure}（恢复了 {recovered} mN 的系统偏移）")
            print("✓ 重置完成（压力值已恢复到上电硬件基线）")
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

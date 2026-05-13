"""
08_demo_zero_baseline — 手动动态归零
======================================

【功能】
    在设备运行中立即触发归零，将触发时刻各点的读取值存为软件基线。
    后续所有压力读取均自动逐点减去该基线，效果等同于重新插拔。
    执行前建议确保传感器表面无负载。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 确认传感器表面无负载。
    3. 运行脚本：
           python 08_demo_zero_baseline.py

【注意事项】
    - 动态归零会立即生效：将触发时刻的各点读取值存为软件基线，后续所有读取均自动减去该基线。
    - 如需撤销归零，请运行 09_demo_baseline_initialization.py。

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

        print("=" * 60)
        print("手动动态归零")
        print("=" * 60)
        print()
        print("说明：立即触发归零，将触发时各点的当前读取值存为软件基线。")
        print("建议在传感器表面无负载时执行，效果等同于重新插拔。\n")

        frame_before = sdk.pressure.read_all()
        print(f"归零前总压力: {frame_before.total_pressure} mN")
        print(f"全部60点: {frame_before.values}\n")

        try:
            input("准备好后，按回车键执行动态归零…")
        except EOFError:
            pass

        sdk.config.trigger_dynamic_zero()
        # trigger_dynamic_zero() 内部已完成：发送硬件命令 → 等待90ms → 读取并存储当前60点为软件基线
        print("✓ 归零完成（硬件命令已发送 + 软件基线已记录）\n")

        frame_after = sdk.pressure.read_all()
        print(f"归零后总压力: {frame_after.total_pressure} mN（预期为 0）")
        print(f"全部60点: {frame_after.values}\n")

        cleared = frame_before.total_pressure
        print(f"已清除基线偏移: {cleared} mN")
        print(f"总压力变化: {frame_before.total_pressure} → {frame_after.total_pressure}")
        print("✓ 归零成功（软件层已按基线补偿，后续读取均自动减去该偏移）")


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

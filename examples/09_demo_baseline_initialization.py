"""
09_demo_baseline_initialization — 重置动态归零
===============================================

【功能】
    清除软件基线，压力值恢复为上电时的硬件零点状态。
    撤销之前通过 08_demo_zero_baseline.py 执行的动态归零操作，
    使传感器回到上电时固件自动归零后的硬件基线状态。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 运行脚本：
           python 09_demo_baseline_initialization.py

【注意事项】
    - 重置后压力值恢复到上电时的硬件基线状态（原始偏移量）。
    - 若需重新归零，请运行 08_demo_zero_baseline.py。

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
        print("重置动态归零")
        print("=" * 60)
        print()
        print("说明：清除软件基线，压力值恢复为上电时硬件基线上的原始偏移量。\n")

        before_reset = sdk.pressure.read_all()
        print(f"重置前总压力: {before_reset.total_pressure} mN")

        sdk.config.reset_dynamic_zero()
        # reset_dynamic_zero() 是瞬时操作：发送硬件命令 + 立即清除软件基线
        print("✓ 已清除软件基线（硬件命令已发送）\n")

        after_reset = sdk.pressure.read_all()
        print(f"重置后总压力: {after_reset.total_pressure} mN（已恢复为上电硬件基线）")
        recovered = after_reset.total_pressure - before_reset.total_pressure
        print(f"总压力变化: {before_reset.total_pressure} → {after_reset.total_pressure}（恢复了 {recovered} mN 的系统偏移）")
        print("✓ 重置完成（压力值已恢复到上电硬件基线）")


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

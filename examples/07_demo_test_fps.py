"""
07_demo_test_fps — 测试最大实际采样率（FPS 压测）
==================================================

【功能】
    以全速无限循环调用 pressure.read_fast() 接口，测试当前硬件和串口条件下
    传感器能达到的最大实际采样率（FPS），并每秒统计一次性能数据。

    与 04_demo_read_pressure.py 的区别：
    - 本 demo 不限制采样率，以最快速度持续读取，用于摸底设备极限 FPS
    - 04_demo 以固定目标频率（200Hz）精确采样，用于实际数据采集

【每秒输出内容】
    实际频率: 198.4 Hz | 点数: 60 | 成功: 198 | 失败: 0 | 错误率: 0.00%

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 运行脚本，观察每秒输出的实际频率：
           python 07_demo_test_fps.py
    3. 按 Ctrl+C 停止。

【调参提示】
    - 串口波特率、USB 延迟、CPU 负载均会影响 FPS 上限。
    - 如需限制最大采样率，取消注释末尾的 time.sleep() 并调整间隔。

【依赖】
    pip install -r requirements.txt
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactile_sdk import TactilePressureSDK

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1


def main() -> None:
    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("设备连接成功！")
        print("开始全速读取压力值（按 Ctrl+C 停止）…\n")

        frame_count = 0
        error_count = 0
        last_t = time.perf_counter()
        last_values = None

        try:
            while True:
                values = sdk.pressure.read_fast()

                if values is not None:
                    frame_count += 1
                    last_values = values
                else:
                    error_count += 1

                now = time.perf_counter()
                if now - last_t >= 1.0:
                    elapsed = now - last_t
                    fps = frame_count / elapsed
                    total = frame_count + error_count
                    error_rate = (error_count / total * 100) if total > 0 else 0.0
                    pts = len(last_values) if last_values else 0
                    print(
                        f"实际频率: {fps:.1f} Hz | 点数: {pts} | "
                        f"成功: {frame_count} | 失败: {error_count} | "
                        f"错误率: {error_rate:.2f}%"
                    )
                    frame_count = 0
                    error_count = 0
                    last_t = now

                # 可选：取消注释以限制最大采样率
                # time.sleep(0.001)

        except KeyboardInterrupt:
            print("\n停止读取")


if __name__ == "__main__":
    main()
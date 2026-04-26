"""
04_demo_read_pressure — 高速连续读取压力值
==========================================

【功能】
    以 200Hz 的速率连续读取传感器全部 60 个压力点的实时数据，
    并每秒统计一次实际采样率和错误率。

    - 每帧输出一个长度为 60 的数组，对应 60 个压力点的当前压力值
    - 压力值类型自动设置为标定值（mN），可在代码中改为 0 切换为 AD 原始值
    - 每秒打印一次性能统计：实际采样率 / 成功帧数 / 失败帧数 / 错误率
    - 按 Ctrl+C 停止

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 port 变量。
    2. 确认 slave_address 与设备拨码地址一致（默认为 1）。
    3. 运行脚本：
           python 04_demo_read_pressure.py

【输出格式】
    每行一帧，格式为 Python 列表，例如：
        [0, 0, 128, 0, 256, ...]
    每秒额外输出一行统计信息：
        >>> 统计: 实际采样率=198.3Hz | 成功=198 | 失败=0 | 错误率=0.00%

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
TARGET_HZ = 200


def main() -> None:
    print("=" * 80)
    print(f"压力值高速读取 — {TARGET_HZ} Hz")
    print("=" * 80)
    print()

    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print(f"✓ 设备连接成功 (端口: {PORT}, 地址: {SLAVE_ADDRESS})")
        print()

        # 获取压力点总数
        try:
            point_count = sdk.config.get_pressure_point_count()
            print(f"压力点总数: {point_count}")
        except Exception as exc:
            print(f"获取压力点总数失败: {exc}，默认 60")
            point_count = 60

        # 设置为标定值模式
        try:
            sdk.config.set_pressure_value_type(1)
            print("压力值类型: 标定值 (mN)")
        except Exception as exc:
            print(f"设置压力值类型失败: {exc}")

        print()
        print(f"开始以 {TARGET_HZ} Hz 速率读取压力值（按 Ctrl+C 停止）...")
        print()

        target_interval = 1.0 / TARGET_HZ
        frame_count = 0
        error_count = 0
        last_stats_time = time.perf_counter()

        try:
            next_read_time = time.perf_counter()

            while True:
                current_time = time.perf_counter()

                if current_time < next_read_time:
                    time.sleep(max(0.0, next_read_time - current_time))
                    current_time = time.perf_counter()

                pressure_values = sdk.pressure.read_fast()

                if pressure_values is not None:
                    frame_count += 1
                    print(pressure_values)
                else:
                    error_count += 1

                next_read_time += target_interval
                if next_read_time < current_time:
                    next_read_time = current_time + target_interval

                if current_time - last_stats_time >= 1.0:
                    elapsed = current_time - last_stats_time
                    actual_fps = frame_count / elapsed
                    total = frame_count + error_count
                    error_rate = (error_count / total * 100) if total > 0 else 0.0
                    print(
                        f"\n>>> 统计: 实际采样率={actual_fps:.1f} Hz | "
                        f"成功={frame_count} | 失败={error_count} | "
                        f"错误率={error_rate:.2f}%\n"
                    )
                    frame_count = 0
                    error_count = 0
                    last_stats_time = current_time

        except KeyboardInterrupt:
            print("\n" + "=" * 80)
            print("停止读取")
            print("=" * 80)


if __name__ == "__main__":
    main()

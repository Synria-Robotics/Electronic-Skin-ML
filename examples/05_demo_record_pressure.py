"""
05_demo_record_pressure — 压力数据采集与保存
================================================

【功能】
    交互式配置采样参数，将传感器压力数据连续记录并保存为 CSV 文件：

    1. 采样率选择：10 / 50 / 100 / 200 Hz 或自定义
    2. 记录时长：自定义秒数，或按 Ctrl+C 提前停止
    3. 文件名：可自定义，默认按时间戳自动生成
    4. 记录前显示配置摘要并确认，记录中实时显示进度和当前总压力
    5. 完成后可选择查看数据统计摘要

【CSV 格式】
    标题行： 时间戳, 相对时间(秒), 压力点1, 压力点2, …, 压力点60
    数据行： 时间戳（秒）, 压力点1值, …
    压力单位： mN（标定模式下）

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 确认 SLAVE_ADDRESS 与设备拨码地址一致（默认为 1）。
    3. 运行脚本并按照提示选择参数：
           python 05_demo_record_pressure.py
    4. CSV 文件保存在脚本当前目录下，可用 Excel 或 Python 开放分析。

【依赖】
    pip install -r requirements.txt
"""

import csv
import os
import sys
import time
from datetime import datetime

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
        print(f"协议版本: {info.protocol_version}")

        point_count = sdk.config.get_pressure_point_count()
        print(f"压力点总数: {point_count}\n")

        sdk.config.set_pressure_value_type(1)
        print("✓ 已设置为标定值模式\n")

        # ----------------------------------------------------------------
        # 采样参数交互配置
        # ----------------------------------------------------------------
        print("=" * 60)
        print("配置记录参数")
        print("=" * 60)
        print("[1] 10 Hz   [2] 50 Hz   [3] 100 Hz   [4] 200 Hz   [5] 自定义")
        rate_choice = input("\n选择采样率 [默认2]: ").strip() or "2"
        rate_map = {"1": 10, "2": 50, "3": 100, "4": 200}
        if rate_choice in rate_map:
            sampling_rate = rate_map[rate_choice]
        elif rate_choice == "5":
            sampling_rate = int(input("请输入采样率 (Hz): "))
        else:
            sampling_rate = 50
            print(f"使用默认采样率: {sampling_rate} Hz")

        print(f"✓ 采样率: {sampling_rate} Hz")
        duration = input("\n输入记录时长（秒）[默认10]: ").strip()
        duration = int(duration) if duration else 10

        default_filename = f"pressure_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename = input(f"\n输入CSV文件名 [默认: {default_filename}]: ").strip() or default_filename
        if not filename.endswith(".csv"):
            filename += ".csv"

        print(f"\n{'=' * 60}")
        print(f"采样率: {sampling_rate} Hz | 时长: {duration} s | "
              f"预计 {sampling_rate * duration} 条 | 文件: {filename}")
        print("=" * 60)

        response = input("确认开始记录？(y/N): ")
        if response.lower() != "y":
            print("已取消")
            return

        # ----------------------------------------------------------------
        # 采集主循环
        # ----------------------------------------------------------------
        print("\n开始记录…（按 Ctrl+C 提前停止）\n")
        interval = 1.0 / sampling_rate
        start_time = time.perf_counter()
        next_sample_time = start_time
        sample_count = success_count = failed_count = 0
        elapsed_time = 0.0

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header = ["时间戳", "相对时间(秒)"] + [f"压力点{i + 1}" for i in range(point_count)]
            writer.writerow(header)

            try:
                while True:
                    current_time = time.perf_counter()
                    elapsed_time = current_time - start_time
                    if elapsed_time >= duration:
                        break

                    if current_time < next_sample_time:
                        time.sleep(next_sample_time - current_time)

                    pressure_values = sdk.pressure.read_fast()

                    if pressure_values is not None:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        relative_time = time.perf_counter() - start_time
                        writer.writerow([timestamp, f"{relative_time:.3f}"] + pressure_values)
                        success_count += 1

                        if sample_count % max(1, sampling_rate // 2) == 0:
                            total_p = sum(pressure_values)
                            progress = elapsed_time / duration * 100
                            print(
                                f"进度: {progress:5.1f}% | 已记录: {success_count:4d} | "
                                f"时间: {elapsed_time:6.1f}s | 总压力: {total_p:6d} mN"
                            )
                    else:
                        failed_count += 1

                    sample_count += 1
                    next_sample_time += interval

            except KeyboardInterrupt:
                elapsed_time = time.perf_counter() - start_time
                print("\n\n用户中断记录")

        # ----------------------------------------------------------------
        # 结果摘要
        # ----------------------------------------------------------------
        print(f"\n{'=' * 60}")
        print("记录完成！")
        print(f"{'=' * 60}")
        print(f"文件: {filename}")
        print(f"时长: {elapsed_time:.2f} s | 成功: {success_count} | 失败: {failed_count}")
        if elapsed_time > 0:
            print(f"实际采样率: {success_count / elapsed_time:.1f} Hz")

        response = input("\n是否显示数据统计？(y/N): ")
        if response.lower() == "y":
            import statistics

            with open(filename, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                all_data = [[int(v) for v in row[2:]] for row in reader]

            if all_data:
                print(f"\n{'压力点':<8} {'最小值':<8} {'最大值':<8} {'均值':<8} {'标准差':<8}")
                print("-" * 50)
                for i in range(point_count):
                    vals = [row[i] for row in all_data]
                    std = statistics.stdev(vals) if len(vals) > 1 else 0.0
                    print(f"点 {i + 1:<4d} {min(vals):<8d} {max(vals):<8d} "
                          f"{statistics.mean(vals):<8.1f} {std:<8.1f}")

        print(f"\n数据已保存到: {filename}")


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

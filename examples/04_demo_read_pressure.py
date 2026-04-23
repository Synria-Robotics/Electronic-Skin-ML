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

import time
from sdk import TactilePressureSDK


def main():
    # 配置串口和从设备地址
    port = "COM6"  # 根据实际情况修改
    slave_address = 1
    
    print("=" * 80)
    print("压力值高速读取 - 200Hz")
    print("=" * 80)
    print()
    
    # 使用上下文管理器自动管理连接
    with TactilePressureSDK(port=port, slave_address=slave_address) as sdk:
        print(f"✓ 设备连接成功 (端口: {port}, 地址: {slave_address})")
        print()
        
        # 获取压力点总数
        try:
            point_count = sdk.get_pressure_point_count()
            print(f"压力点总数: {point_count}")
        except Exception as e:
            print(f"获取压力点总数失败: {e}")
            point_count = 60
        
        # 设置压力值类型为标定值
        try:
            sdk.set_pressure_value_type(1)  # 1表示标定值，0表示AD值
            print("压力值类型: 标定值")
        except Exception as e:
            print(f"设置压力值类型失败: {e}")
        
        print()
        print("开始以200Hz速率读取压力值（按Ctrl+C停止）...")
        print()
        
        # 性能统计变量
        frame_count = 0
        error_count = 0
        last_stats_time = time.perf_counter()
        
        # 目标采样间隔：200Hz = 1/200 = 0.005秒 = 5ms
        target_interval = 1.0 / 200.0
        
        try:
            next_read_time = time.perf_counter()
            
            while True:
                current_time = time.perf_counter()
                
                # 等待到下一个采样时间点
                if current_time < next_read_time:
                    # 精确延时
                    time.sleep(max(0, next_read_time - current_time))
                    current_time = time.perf_counter()
                
                # 使用优化的快速读取接口
                pressure_values = sdk.read_pressure_fast()
                
                if pressure_values is not None:
                    frame_count += 1
                    
                    # 打印60个压力点的数组
                    print(pressure_values)
                    
                else:
                    error_count += 1
                
                # 计算下一次读取时间
                next_read_time += target_interval
                
                # 如果已经延迟太多，重新同步
                if next_read_time < current_time:
                    next_read_time = current_time + target_interval
                
                # 每秒统计一次性能（不影响主循环）
                if current_time - last_stats_time >= 1.0:
                    actual_fps = frame_count / (current_time - last_stats_time)
                    total_frames = frame_count + error_count
                    error_rate = (error_count / total_frames * 100) if total_frames > 0 else 0
                    
                    print(f"\n>>> 统计: 实际采样率={actual_fps:.1f}Hz | "
                          f"成功={frame_count} | 失败={error_count} | 错误率={error_rate:.2f}%\n")
                    
                    # 重置计数器
                    frame_count = 0
                    error_count = 0
                    last_stats_time = current_time
            
        except KeyboardInterrupt:
            print()
            print("=" * 80)
            print("停止读取")
            print("=" * 80)


if __name__ == "__main__":
    main()

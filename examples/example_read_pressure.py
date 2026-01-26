"""
压力值读取示例 - 以200Hz速率连续读取并打印60个压力点数据
"""

import time
from sdk import TactilePressureSDK


def main():
    # 配置串口和从设备地址
    port = "COM7"  # 根据实际情况修改
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

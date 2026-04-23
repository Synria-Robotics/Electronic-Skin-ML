"""
07_demo_test_fps — 测试最大实际采样率（FPS 压测）
==================================================

【功能】
    以全速无限循环调用 read_pressure_fast() 接口，测试当前硬件和串口条件下
    传感器能达到的最大实际采样率（FPS），并每秒统计一次性能数据。

    与 04_demo_read_pressure.py 的区别：
    - 本 demo 不限制采样率，以最快速度持续读取，用于摸底设备极限 FPS
    - 04_demo 以固定目标频率（200Hz）精确采样，用于实际数据采集

【每秒输出内容】
    实际频率: 198.4 Hz | 点数: 60 | 成功: 198 | 失败: 0 | 错误率: 0.00%

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 port 变量。
    2. 运行脚本，观察每秒输出的实际频率：
           python 07_demo_test_fps.py
    3. 按 Ctrl+C 停止。

【调参提示】
    - 如需限制最大采样率，取消注释末尾的 time.sleep(0.001) 并调整间隔。
    - 串口波特率、USB 延迟、CPU 负载均会影响 FPS 上限。

【依赖】
    pip install -r requirements.txt
"""
import time
from sdk import TactilePressureSDK


def read_pressure():
    """以高频率读取所有压力值 - 使用优化的快速读取接口"""
    sdk = TactilePressureSDK(port="COM6", slave_address=1)
    sdk.connect()
    
    frame_count = 0
    error_count = 0
    last_t = time.perf_counter()  # 使用高精度计时
    
    try:
        print("开始高速读取压力值（按 Ctrl+C 停止）...")
        print("使用优化的 read_pressure_fast() 接口")
        print()
        
        while True:
            # 使用优化的快速读取接口
            pressures = sdk.read_pressure_fast()
            
            if pressures is not None:
                frame_count += 1
            else:
                error_count += 1
            
            # 每秒统计一次
            now = time.perf_counter()
            if now - last_t >= 1.0:
                fps = frame_count / (now - last_t)
                total_frames = frame_count + error_count
                error_rate = (error_count / total_frames * 100) if total_frames > 0 else 0
                
                print(f"实际频率: {fps:.1f} Hz | 点数: {len(pressures) if pressures else 0} | "
                      f"成功: {frame_count} | 失败: {error_count} | 错误率: {error_rate:.2f}%")
                
                frame_count = 0
                error_count = 0
                last_t = now
            
            # 可选：添加延时控制采样率
            # time.sleep(0.001)  # 取消注释以限制最大采样率
            
    except KeyboardInterrupt:
        print("\n停止读取")
    finally:
        sdk.disconnect()


if __name__ == "__main__":
    read_pressure()
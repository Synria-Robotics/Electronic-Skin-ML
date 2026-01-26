import time
from sdk import TactilePressureSDK


def read_pressure():
    """以高频率读取所有压力值 - 使用优化的快速读取接口"""
    sdk = TactilePressureSDK(port="COM7", slave_address=1)
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
"""
压力数据记录示例

演示如何记录一段时间内的压力数据并保存为CSV文件
CSV文件包含时间戳和60个压力点的数据
"""

import time
import csv
from datetime import datetime
from sdk import TactilePressureSDK
from sdk.modbus_rtu import ModbusRTUError


def main():
    # 配置串口和从设备地址
    port = "COM7"  # 根据实际情况修改
    slave_address = 1

    with TactilePressureSDK(port=port, slave_address=slave_address) as sdk:
        print("设备连接成功！\n")
        
        # 读取设备信息
        info = sdk.get_device_info()
        print(f"设备型号: {info['device_model']}")
        print(f"协议版本: {info['protocol_version']}")
        
        # 获取压力点数量
        point_count = sdk.get_pressure_point_count()
        print(f"压力点总数: {point_count}\n")
        
        # 设置为标定值模式
        print("设置压力值类型为标定值...")
        sdk.set_pressure_value_type(1)  # 1 = 标定值
        print("✓ 已设置为标定值模式\n")
        
        # ==================== 配置记录参数 ====================
        print("=" * 60)
        print("配置记录参数")
        print("=" * 60)
        print()
        
        # 采样率设置
        print("采样率选项：")
        print("[1] 10 Hz  (每秒10次，适合慢速监测)")
        print("[2] 50 Hz  (每秒50次，适合一般监测)")
        print("[3] 100 Hz (每秒100次，适合高速监测)")
        print("[4] 200 Hz (每秒200次，适合超高速监测)")
        print("[5] 自定义")
        
        rate_choice = input("\n选择采样率 [默认2]: ").strip() or "2"
        
        rate_map = {
            "1": 10,
            "2": 50,
            "3": 100,
            "4": 200,
        }
        
        if rate_choice in rate_map:
            sampling_rate = rate_map[rate_choice]
        elif rate_choice == "5":
            sampling_rate = int(input("请输入采样率 (Hz): "))
        else:
            sampling_rate = 50
            print(f"使用默认采样率: {sampling_rate} Hz")
        
        # 记录时长设置
        print(f"\n✓ 采样率: {sampling_rate} Hz")
        duration = input("\n输入记录时长（秒）[默认10]: ").strip()
        duration = int(duration) if duration else 10
        
        # 文件名设置
        default_filename = f"pressure_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename = input(f"\n输入CSV文件名 [默认: {default_filename}]: ").strip()
        filename = filename if filename else default_filename
        
        # 确保文件名以.csv结尾
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # 显示配置摘要
        print("\n" + "=" * 60)
        print("记录配置摘要")
        print("=" * 60)
        print(f"采样率: {sampling_rate} Hz")
        print(f"记录时长: {duration} 秒")
        print(f"预计采样数: {sampling_rate * duration} 条")
        print(f"文件名: {filename}")
        print(f"压力点数: {point_count}")
        print("=" * 60)
        print()
        
        response = input("确认开始记录？(y/N): ")
        if response.lower() != 'y':
            print("已取消记录")
            return
        
        # ==================== 开始记录 ====================
        print("\n" + "=" * 60)
        print("开始记录压力数据")
        print("=" * 60)
        print()
        print("提示：按 Ctrl+C 可提前停止记录\n")
        
        # 创建CSV文件并写入表头
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # 写入表头
            header = ['时间戳', '相对时间(秒)'] + [f'压力点{i+1}' for i in range(point_count)]
            csv_writer.writerow(header)
            
            # 记录参数
            interval = 1.0 / sampling_rate  # 采样间隔
            start_time = time.perf_counter()
            record_start_time = datetime.now()
            next_sample_time = start_time
            
            # 统计信息
            sample_count = 0
            success_count = 0
            failed_count = 0
            
            try:
                while True:
                    current_time = time.perf_counter()
                    elapsed_time = current_time - start_time
                    
                    # 检查是否达到记录时长
                    if elapsed_time >= duration:
                        break
                    
                    # 时间控制：等待到下一个采样时刻
                    if current_time < next_sample_time:
                        sleep_time = next_sample_time - current_time
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                    
                    # 读取压力值
                    pressure_values = sdk.read_pressure_fast()
                    
                    if pressure_values is not None:
                        # 记录时间戳
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        relative_time = time.perf_counter() - start_time
                        
                        # 写入CSV
                        row = [timestamp, f'{relative_time:.3f}'] + pressure_values
                        csv_writer.writerow(row)
                        
                        success_count += 1
                        
                        # 每0.5秒显示一次进度
                        if sample_count % max(1, sampling_rate // 2) == 0:
                            total_pressure = sum(pressure_values)
                            progress = (elapsed_time / duration) * 100
                            print(f"进度: {progress:5.1f}% | "
                                  f"已记录: {success_count:4d} | "
                                  f"时间: {elapsed_time:6.1f}s | "
                                  f"总压力: {total_pressure:6d}mN")
                    else:
                        failed_count += 1
                    
                    sample_count += 1
                    next_sample_time += interval
                    
            except KeyboardInterrupt:
                print("\n\n用户中断记录")
                elapsed_time = time.perf_counter() - start_time
        
        # ==================== 记录完成 ====================
        print("\n" + "=" * 60)
        print("记录完成！")
        print("=" * 60)
        print()
        print(f"文件名: {filename}")
        print(f"记录时长: {elapsed_time:.2f} 秒")
        print(f"成功记录: {success_count} 条")
        print(f"失败次数: {failed_count} 次")
        print(f"实际采样率: {success_count / elapsed_time:.1f} Hz")
        print(f"数据完整率: {success_count / sample_count * 100:.1f}%")
        print()
        
        # ==================== 数据统计 ====================
        response = input("是否显示数据统计信息？(y/N): ")
        if response.lower() == 'y':
            print("\n正在分析数据...")
            
            # 重新读取CSV文件进行统计
            with open(filename, 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                next(csv_reader)  # 跳过表头
                
                all_data = []
                for row in csv_reader:
                    # 提取压力值（跳过时间戳和相对时间）
                    pressure_data = [int(val) for val in row[2:]]
                    all_data.append(pressure_data)
                
                if all_data:
                    import statistics
                    
                    print("\n" + "=" * 60)
                    print("数据统计")
                    print("=" * 60)
                    print()
                    
                    # 计算每个压力点的统计信息
                    print("每个压力点的统计信息：")
                    print(f"{'压力点':<8} {'最小值':<8} {'最大值':<8} {'平均值':<8} {'标准差':<8}")
                    print("-" * 60)
                    
                    for i in range(point_count):
                        point_values = [row[i] for row in all_data]
                        min_val = min(point_values)
                        max_val = max(point_values)
                        avg_val = statistics.mean(point_values)
                        std_val = statistics.stdev(point_values) if len(point_values) > 1 else 0
                        
                        print(f"点 {i+1:<4d} {min_val:<8d} {max_val:<8d} {avg_val:<8.1f} {std_val:<8.1f}")
                    
                    # 总压力统计
                    print("\n总压力统计：")
                    total_pressures = [sum(row) for row in all_data]
                    print(f"  最小总压力: {min(total_pressures)} mN")
                    print(f"  最大总压力: {max(total_pressures)} mN")
                    print(f"  平均总压力: {statistics.mean(total_pressures):.1f} mN")
                    print(f"  标准差: {statistics.stdev(total_pressures):.1f} mN" if len(total_pressures) > 1 else "  标准差: 0.0 mN")
                    print()
        
        print("数据已保存到:", filename)
        print("\n提示：可以使用Excel或其他工具打开CSV文件查看数据")


if __name__ == "__main__":
    try:
        main()
    except ModbusRTUError as e:
        print(f"\n通信错误: {e}")
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

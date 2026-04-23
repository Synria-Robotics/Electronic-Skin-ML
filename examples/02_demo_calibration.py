"""
02_demo_calibration — 传感器标定
==========================================

【功能】
    演示三种标定方式，建立 AD 原始值与实际压力值（mN）之间的映射关系，
    使设备能够输出准确的标定压力值而非原始 AD 值。

    示例1 — 单点标定：
        对指定压力点的指定拟合点单独标定。
        每个压力点最多支持 11 个拟合点，施加已知压力后让设备采样记录 AD 值。

    示例2 — 多拟合点全部标定：
        不指定单个压力点，对所有压力点统一按多个拟合点（0、500、1000、2000 mN…）
        依次标定，适合批量标定整张传感器。

    示例3 — 清除标定（谨慎）：
        将标定数据恢复到出厂状态。清除后需重新运行
        example_recover_calibration.py 恢复备份数据，否则压力值将不准确。

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 port 变量。
    2. 确认 slave_address 与设备拨码地址一致（默认为 1）。
    3. 标定前请在传感器对应压力点上施加精确已知的压力（mN）。
    4. 运行脚本：
           python 02_demo_calibration.py

【注意事项】
    - 标定模式 100 = 单点标定，101 = 全部标定。
    - use_sample=True 表示使用设备实时采样的 AD 值，False 则使用手动设置值。
    - 清除标定操作不可逆，请提前用 example_recover_calibration.py 备份数据。

【依赖】
    pip install -r requirements.txt
"""

from sdk import TactilePressureSDK


def main():
    # 配置串口和从设备地址
    port = "COM6"  # 根据实际情况修改
    slave_address = 1

    with TactilePressureSDK(port=port, slave_address=slave_address) as sdk:
        print("设备连接成功！\n")
        
        # 读取当前标定配置
        print("=== 当前标定配置 ===")
        print(f"标定模式: {sdk.get_calibration_mode()} "
              f"({'全部标定' if sdk.get_calibration_mode() == 101 else '单点标定'})")
        print(f"当前压力点: {sdk.get_pressure_point()}")
        print(f"当前拟合点: {sdk.get_fitting_point()}")
        print()
        
        # 示例1：单点标定
        # 一个拟合点一个压力点,一个ad值,一个设置的压力值(mN)
        print("=== 示例1：单点标定 ===")
        try:
            # 设置标定模式为单点标定
            sdk.set_calibration_mode(100)  # 100表示单点标定
            print("标定模式已设置为单点标定")
            
            # 选择要标定的压力点
            pressure_point = 1
            sdk.set_pressure_point(pressure_point)
            print(f"选择压力点: {pressure_point}")
            
            # 设置拟合点，每个压力点有11个拟合点可选
            fitting_point = 1
            sdk.set_fitting_point(fitting_point)
            print(f"设置拟合点: {fitting_point}")
            
            # 设置压力值（单位：mN，毫牛）
            pressure_value = 1000  # 例如：1000mN
            sdk.set_fitting_point_pressure_value(pressure_value)
            print(f"设置压力值: {pressure_value} mN")
            
            # 执行标定（记录采样值）
            print("执行标定（记录采样值）...")

            sdk.calibrate(use_sample=True)
            print("标定完成")
            
            # 读取标定后的AD值
            ad_value = sdk.get_fitting_point_ad_value()
            print(f"标定后的AD值: {ad_value}")
            print()
            
        except Exception as e:
            print(f"标定失败: {e}\n")
        # 1个压力点需要11个拟合点的数据
        # 示例2：多拟合点标定，相当于多点标定，就是不需要选择压力点了，所有压力点都按照下面的标定方式标定
        # 一个拟合点，一个压力值，一个ad值，ad值可以自己设置数据也可以用采样值，如果是采样值那压力点就是之前设置的压力点
        print("=== 示例2：多拟合点标定 ===")
        try:
            # 设置标定模式为全部标定
            sdk.set_calibration_mode(101)  # 101表示全部标定
            print("标定模式已设置为全部标定")
            
            # 标定多个拟合点
            calibration_points = [
                (1, 0),      # 拟合点1，压力0mN
                (2, 500),    # 拟合点2，压力500mN
                (3, 1000),   # 拟合点3，压力1000mN
                (4, 2000),   # 拟合点4，压力2000mN
            ]
            
            for fitting_point, pressure_value in calibration_points:
                print(f"\n标定拟合点 {fitting_point}，压力值 {pressure_value} mN")
                sdk.set_fitting_point(fitting_point)
                sdk.set_fitting_point_pressure_value(pressure_value)
                
                # 执行标定（记录采样值）
                sdk.calibrate(use_sample=True)  #
                
                # 读取AD值
                ad_value = sdk.get_fitting_point_ad_value()
                print(f"  拟合点 {fitting_point} AD值: {ad_value}")
            
            print("\n多拟合点标定完成")
            
        except Exception as e:
            print(f"标定失败: {e}\n")
        
        # 示例3：清除标定（谨慎使用） 出厂标定并不是可以使用的标定
        print("=== 示例3：清除标定 ===")
        response = input("是否清除标定信息？这将恢复到出厂标定 (y/N): ")
        if response.lower() == 'y':
            try:
                print("正在清除标定信息...")
                sdk.clear_calibration()
                print("标定信息已清除，已恢复到出厂标定,请再重新运行一下example_recover_calibration.py恢复标定数据,否则压力值会不准确")
            except Exception as e:
                print(f"清除标定失败: {e}")
        else:
            print("已取消清除标定操作")


if __name__ == "__main__":
    main()

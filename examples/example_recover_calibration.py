# 如果标定的时候标定错了,运行这个脚本恢复原来的数值
# 恢复出厂标点脚本
# 这个直接写入标定点数据,不需要读取当前标定点数据

from sdk import TactilePressureSDK

points = [
    (1, 0,    10),
    (2, 100, 559),
    (3, 200, 998),
    (4, 300, 1319),
    (5, 400, 1554),
    (6, 500, 1729),
    (7, 600, 1871),
    (8, 700, 1999),
    (9, 800, 2113),
    (10, 900, 2211),
    (11, 1000, 2284),
]

with TactilePressureSDK(port="COM7", slave_address=1) as sdk:
    # 如有多通道，这里先选要标定的压力点（通道），单通道可省略
    sdk.set_calibration_mode(101)  # 101表示全部标定,因为一个压力点需要上面一组标定数据，全部标定就不需要切换压力点了
    for idx, pressure, ad in points:
        print(f"写入拟合点 {idx}: 压力={pressure} mN, AD={ad}")
        sdk.set_fitting_point(idx)                 # 选拟合点编号
        sdk.set_fitting_point_pressure_value(pressure)  # 写压力值
        sdk.calibrate(ad_value=ad)                # 按协议：写入AD值（非65535）
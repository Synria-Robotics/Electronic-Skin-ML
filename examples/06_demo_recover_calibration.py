"""
06_demo_recover_calibration — 恢复出厂标定数据
====================================================

【功能】
    将传感器标定数据恢复为出厂预设值。
    适用于以下场景：
    - 运行 02_demo_calibration.py 后标定内容错误，需要撤销
    - 运行 03_demo_configuration.py 清除了标定后需要恢复
    - 设备压力读数不准，怪疑标定被破坏

【原理】
    直接向设备写入预定义的标定点表（11个拟合点）：
    拟合点编号 | 对应压力（mN） | 对应 AD 值
    采用全部标定模式（mode=101），一次性对所有压力点应用相同标定曲线。

【出厂标定表】
    拟合点  压力(mN)  AD值
    1       0      10
    2       100    559
    3       200    998
    4       300    1319
    5       400    1554
    6       500    1729
    7       600    1871
    8       700    1999
    9       800    2113
    10      900    2211
    11      1000   2284

【使用方法】
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 port 变量。
    2. 直接运行，无需额外操作：
           python 06_demo_recover_calibration.py

【注意事项】
    - 运行后将覆盖当前所有标定数据，不可逆。
    - 如需保留当前自定义标定，请勿运行本脚本。

【依赖】
    pip install -r requirements.txt
"""

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

with TactilePressureSDK(port="COM6", slave_address=1) as sdk:
    # 如有多通道，这里先选要标定的压力点（通道），单通道可省略
    sdk.set_calibration_mode(101)  # 101表示全部标定,因为一个压力点需要上面一组标定数据，全部标定就不需要切换压力点了
    for idx, pressure, ad in points:
        print(f"写入拟合点 {idx}: 压力={pressure} mN, AD={ad}")
        sdk.set_fitting_point(idx)                 # 选拟合点编号
        sdk.set_fitting_point_pressure_value(pressure)  # 写压力值
        sdk.calibrate(ad_value=ad)                # 按协议：写入AD值（非65535）
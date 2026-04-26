"""
06_demo_recover_calibration — 恢复出厂标定数据
====================================================

【功能】
    将传感器标定数据恢复为出厂预设值。
    适用于以下场景：
    - 运行 02_demo_calibration.py 后标定内容错误，需要撤销
    - 运行 03_demo_configuration.py 清除了标定后需要恢复
    - 设备压力读数不准，怀疑标定被破坏

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
    1. 将传感器通过 USB 连接到电脑，确认串口号并修改下方 PORT 变量。
    2. 直接运行，无需额外操作：
           python 06_demo_recover_calibration.py

【注意事项】
    - 运行后将覆盖当前所有标定数据，不可逆。
    - 如需保留当前自定义标定，请勿运行本脚本。

【依赖】
    pip install -r requirements.txt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactile_sdk import TactilePressureSDK, CalibrationMode

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
PORT = "COM6"
SLAVE_ADDRESS = 1

# 出厂标定表：(拟合点编号, 压力 mN, AD 值)
FACTORY_CALIBRATION = [
    (1,    0,   10),
    (2,  100,  559),
    (3,  200,  998),
    (4,  300, 1319),
    (5,  400, 1554),
    (6,  500, 1729),
    (7,  600, 1871),
    (8,  700, 1999),
    (9,  800, 2113),
    (10, 900, 2211),
    (11, 1000, 2284),
]


def main() -> None:
    with TactilePressureSDK(port=PORT, slave_address=SLAVE_ADDRESS) as sdk:
        print("设备连接成功！\n")
        print("正在恢复出厂标定数据…\n")

        # 切换到全部标定模式（对所有压力点统一应用）
        sdk.calibration.set_mode(CalibrationMode.ALL_POINTS)
        print("标定模式 → 全部标定 (101)\n")

        for idx, pressure, ad in FACTORY_CALIBRATION:
            print(f"写入拟合点 {idx:>2d}: 压力={pressure:>5d} mN, AD={ad}")
            sdk.calibration.set_fitting_point(idx)
            sdk.calibration.set_fitting_point_pressure(pressure)
            sdk.calibration.calibrate(ad_value=ad)

        print("\n✓ 出厂标定数据恢复完成")


if __name__ == "__main__":
    main()
"""
常量定义模块
"""

from enum import IntEnum


class FunctionCode(IntEnum):
    """功能码定义"""
    READ_HOLDING_REGISTERS = 0x03  # 读保持寄存器
    WRITE_SINGLE_REGISTER = 0x06   # 写单个保持寄存器
    WRITE_MULTIPLE_REGISTERS = 0x10  # 写多个保持寄存器
    READ_SPECIFIC_INFO = 0x41      # 读取指定信息（扩展）
    READ_ALL_PRESSURE_VALUES = 0x42  # 读取所有压力值（扩展）
    
    # 异常响应码 = 功能码 + 0x80
    EXCEPTION_MASK = 0x80


class ExceptionCode(IntEnum):
    """Modbus异常码"""
    ILLEGAL_FUNCTION = 0x01        # 非法功能码
    ILLEGAL_DATA_ADDRESS = 0x02    # 非法数据地址
    ILLEGAL_DATA_VALUE = 0x03      # 非法数据值


class InfoIndex(IntEnum):
    """信息索引表"""
    DEVICE_MODEL = 1               # 设备型号
    PROTOCOL_NUMBER = 2            # 协议编号
    PROTOCOL_VERSION = 3           # 协议版本
    APP_VERSION = 4                # App版本


class RegisterAddress(IntEnum):
    """保持寄存器地址定义"""
    DEVICE_ADDRESS = 0x0001        # 设备地址
    AUTO_UPLOAD_FLAG = 0x000B      # 主动上传标志
    AUTO_UPLOAD_FREQUENCY = 0x000C  # 主动上传频率
    PRESSURE_VALUE_TYPE = 0x000D   # 压力值类型
    AD_MASK_VALUE = 0x000E         # AD屏蔽值
    PRESSURE_POINT_COUNT = 0x000F  # 压力点总数
    SENSOR_POINT_AREA = 0x0010     # 传感器单个点面积
    PRESSURE_AUTO_ZERO_ENABLE = 0x0011  # 压强值上电自动归零使能标志
    PRESSURE_DYNAMIC_ZERO = 0x0012  # 压强动态归零
    
    # 标定相关
    FITTING_POINT = 0x0064         # 拟合点
    FITTING_POINT_AD_VALUE = 0x0065  # 拟合点对应AD值
    FITTING_POINT_PRESSURE_VALUE = 0x0066  # 拟合点对应压力值
    PRESSURE_POINT = 0x0067        # 压力点
    CALIBRATION_MODE = 0x0068      # 标定模式
    CALIBRATION = 0x0069           # 标定
    CLEAR_CALIBRATION = 0x0070     # 清除标定


class DataEndian:
    """数据字节序定义"""
    BIG_ENDIAN = "big"      # 大端模式（公共功能码使用）
    LITTLE_ENDIAN = "little"  # 小端模式（扩展功能码使用）


# 协议配置
BROADCAST_ADDRESS = 0x00           # 广播地址
MIN_SLAVE_ADDRESS = 1              # 最小从设备地址
MAX_SLAVE_ADDRESS = 247            # 最大从设备地址
DEFAULT_BAUDRATE = 4000000          # 默认波特率
DEFAULT_TIMEOUT = 1.0              # 默认超时时间（秒）

# 主动上传帧
ACTIVE_UPLOAD_FRAME_HEADER = 0xA55A  # 主动上传帧头

# 标定模式
CALIBRATION_MODE_SINGLE_POINT = 100   # 单点标定
CALIBRATION_MODE_ALL_POINTS = 101     # 全部标定

# 标定命令
CALIBRATION_COMMAND_SAMPLE = 65535    # 记录采样值
CLEAR_CALIBRATION_COMMAND = 119       # 清除标定命令

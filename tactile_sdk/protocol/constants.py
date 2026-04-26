"""
协议常量与枚举定义
==================
集中管理 Modbus RTU 功能码、寄存器地址、标定参数等所有协议层常量，
供 protocol 层与 api 层引用，避免魔法数字散落各处。
"""

from enum import IntEnum


# ---------------------------------------------------------------------------
# 功能码
# ---------------------------------------------------------------------------

class FunctionCode(IntEnum):
    """Modbus 功能码。"""

    READ_HOLDING_REGISTERS = 0x03    # 读保持寄存器
    WRITE_SINGLE_REGISTER = 0x06     # 写单个保持寄存器

    READ_SPECIFIC_INFO = 0x41        # 读取指定信息（扩展）
    READ_ALL_PRESSURE_VALUES = 0x42  # 读取所有压力值（扩展）

    # 异常响应掩码：响应功能码 = 请求功能码 | 0x80
    EXCEPTION_MASK = 0x80


# ---------------------------------------------------------------------------
# 异常码
# ---------------------------------------------------------------------------

class ExceptionCode(IntEnum):
    """Modbus 标准异常码。"""

    ILLEGAL_FUNCTION = 0x01       # 非法功能码
    ILLEGAL_DATA_ADDRESS = 0x02   # 非法数据地址
    ILLEGAL_DATA_VALUE = 0x03     # 非法数据值


# ---------------------------------------------------------------------------
# 信息索引（功能码 0x41）
# ---------------------------------------------------------------------------

class InfoIndex(IntEnum):
    """0x41 读取指定信息的索引表。"""

    DEVICE_MODEL = 1       # 设备型号
    PROTOCOL_NUMBER = 2    # 协议编号
    PROTOCOL_VERSION = 3   # 协议版本
    APP_VERSION = 4        # App 固件版本


# ---------------------------------------------------------------------------
# 保持寄存器地址
# ---------------------------------------------------------------------------

class RegisterAddress(IntEnum):
    """保持寄存器地址定义（功能码 0x03 / 0x06 / 0x10）。"""

    # 设备基础配置
    DEVICE_ADDRESS = 0x0001           # 设备 Modbus 地址
    AUTO_UPLOAD_FLAG = 0x000B         # 主动上传使能标志
    AUTO_UPLOAD_FREQUENCY = 0x000C    # 主动上传频率（Hz）
    PRESSURE_VALUE_TYPE = 0x000D      # 压力值类型：0=AD 值，1=标定值
    AD_MASK_VALUE = 0x000E            # AD 屏蔽值（低于此值视为无压力）
    PRESSURE_POINT_COUNT = 0x000F     # 压力点总数（只读）
    SENSOR_POINT_AREA = 0x0010        # 传感器单个点面积（0.1 mm² 为单位）
    PRESSURE_AUTO_ZERO_ENABLE = 0x0011  # 上电自动归零使能（只写）
    PRESSURE_DYNAMIC_ZERO = 0x0012    # 动态归零控制：1=触发归零，2=重置归零

    # 标定相关
    FITTING_POINT = 0x0064                   # 当前拟合点编号（1–11）
    FITTING_POINT_AD_VALUE = 0x0065          # 当前拟合点 AD 值
    FITTING_POINT_PRESSURE_VALUE = 0x0066    # 当前拟合点压力值（mN）
    PRESSURE_POINT = 0x0067                  # 当前压力点编号（单点标定用）
    CALIBRATION_MODE = 0x0068                # 标定模式：100=单点，101=全部
    CALIBRATION = 0x0069                     # 标定控制寄存器
    CLEAR_CALIBRATION = 0x0070               # 清除标定命令寄存器


# ---------------------------------------------------------------------------
# 标定模式常量
# ---------------------------------------------------------------------------

class CalibrationMode(IntEnum):
    """标定模式枚举。"""

    SINGLE_POINT = 100   # 单点标定（需先指定压力点）
    ALL_POINTS = 101     # 全部标定（对所有压力点统一应用）


# ---------------------------------------------------------------------------
# 字节序标识
# ---------------------------------------------------------------------------

class DataEndian:
    """帧字节序标识字符串（供内部帧构建逻辑使用）。"""

    BIG_ENDIAN = "big"       # 公共功能码（0x03/0x06/0x10）使用大端
    LITTLE_ENDIAN = "little"  # 扩展功能码（0x41/0x42）使用小端


# ---------------------------------------------------------------------------
# 协议默认值与边界
# ---------------------------------------------------------------------------

BROADCAST_ADDRESS: int = 0x00    # 广播地址（设备不返回响应）
MIN_SLAVE_ADDRESS: int = 1       # 从设备地址下限
MAX_SLAVE_ADDRESS: int = 247     # 从设备地址上限

DEFAULT_BAUDRATE: int = 4_000_000   # 默认波特率
DEFAULT_TIMEOUT: float = 1.0        # 默认读超时（秒）
DEFAULT_SEND_WAIT_SECS: float = 0.005  # 发送帧后等待响应开始的默认延迟（秒）


# 标定控制命令值
CALIBRATION_COMMAND_SAMPLE: int = 65535   # 触发设备实时采样 AD 值
CLEAR_CALIBRATION_COMMAND: int = 119      # 清除所有标定数据

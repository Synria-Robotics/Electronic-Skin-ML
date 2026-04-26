"""
tactile_sdk — 玄雅 / Synria 科技触觉压力采集模块 Python SDK
=============================================================

快速开始
--------
::

    from tactile_sdk import TactilePressureSDK

    with TactilePressureSDK("COM6") as sdk:
        print(sdk.device.get_info())
        frame = sdk.pressure.read_all()
        print(frame.values)

分层架构
--------
::

    TactilePressureSDK   门面层
    ├── .device          DeviceAPI      设备信息 & Modbus 地址
    ├── .config          ConfigAPI      传感器参数配置
    ├── .pressure        PressureAPI    压力数据读取
    └── .calibration     CalibrationAPI 标定操作
           ↑ 共享 ModbusRTU（协议层）
               ↑ SerialTransport（传输层）
"""

from .client import TactilePressureSDK
from .exceptions import (
    TactileSdkError,
    DeviceConnectionError,
    CommunicationError,
    ProtocolError,
    ValidationError,
    CalibrationError,
)
from .models import DeviceInfo, FittingPoint, PressureFrame, CalibrationStatus
from .protocol.constants import CalibrationMode

__version__ = "2.0.0"
__author__ = "玄雅 / Synria 科技"

__all__ = [
    # 主入口
    "TactilePressureSDK",
    # 异常
    "TactileSdkError",
    "DeviceConnectionError",
    "CommunicationError",
    "ProtocolError",
    "ValidationError",
    "CalibrationError",
    # 模型
    "DeviceInfo",
    "FittingPoint",
    "PressureFrame",
    "CalibrationStatus",
    # 用户层常量
    "CalibrationMode",
]

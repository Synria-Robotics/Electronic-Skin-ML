"""
tactile_sdk 异常层
==================
定义 SDK 全局异常类型，所有模块统一使用此处的异常，
避免将底层依赖（如 serial.SerialException）暴露给调用方。

继承关系
--------
TactileSdkError (基类)
├── DeviceConnectionError 串口连接失败或连接断开
├── CommunicationError    通信错误（超时、CRC 失败、响应不完整）
├── ProtocolError         协议层错误（非法功能码、帧结构异常）
├── ValidationError       参数校验失败（地址越界、值超范围）
└── CalibrationError      标定操作失败
"""


class TactileSdkError(Exception):
    """SDK 基础异常，所有自定义异常均继承自此类。"""


class DeviceConnectionError(TactileSdkError):
    """串口连接失败或连接意外断开时抛出。"""


class CommunicationError(TactileSdkError):
    """通信错误：超时未收到响应、CRC 校验失败、帧长度不足等。"""


class ProtocolError(TactileSdkError):
    """协议层错误：功能码不匹配、Modbus 异常响应码、索引不一致等。"""


class ValidationError(TactileSdkError):
    """参数值不符合协议规范（地址越界、频率超范围、数量不符等）。"""


class CalibrationError(TactileSdkError):
    """标定操作失败，通常由底层 CommunicationError 或 ProtocolError 包装而来。"""

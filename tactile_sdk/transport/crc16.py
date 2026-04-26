"""
CRC16 转发模块
================
CRC16 实现已移至 ``tactile_sdk.protocol.crc16``，
此文件仅做转发，保持向后兼容。
"""
from ..protocol.crc16 import calculate_crc16, verify_crc16  # noqa: F401

__all__ = ["calculate_crc16", "verify_crc16"]



def calculate_crc16(data: bytes) -> bytes:
    """
    计算 Modbus CRC16 校验码。

    Args:
        data: 待校验的数据（不含 CRC 本身）。

    Returns:
        2 字节 CRC，小端序（低字节在前，高字节在后）。
    """
    crc = 0xFFFF
    polynomial = 0xA001  # Modbus CRC16 多项式

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ polynomial
            else:
                crc >>= 1

    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def verify_crc16(data: bytes, crc: bytes) -> bool:
    """
    验证 CRC16 校验码是否匹配。

    Args:
        data: 数据部分（不含 CRC）。
        crc:  接收到的 2 字节 CRC。

    Returns:
        True 表示校验通过，False 表示不匹配。
    """
    return calculate_crc16(data) == crc

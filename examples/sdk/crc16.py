"""
CRC16校验模块
使用Modbus CRC16算法（生成多项式为A001）
"""


def calculate_crc16(data: bytes) -> bytes:
    """
    计算CRC16校验码（Modbus标准，生成多项式A001）
    
    Args:
        data: 需要计算CRC的数据（不包括CRC本身）
        
    Returns:
        CRC16校验码（2字节，小端模式）
    """
    crc = 0xFFFF
    polynomial = 0xA001  # Modbus CRC16多项式
    
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ polynomial
            else:
                crc >>= 1
    
    # 返回小端模式的CRC（低字节在前，高字节在后）
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def verify_crc16(data: bytes, crc: bytes) -> bool:
    """
    验证CRC16校验码
    
    Args:
        data: 数据部分
        crc: 接收到的CRC校验码（2字节）
        
    Returns:
        True表示校验通过，False表示校验失败
    """
    calculated_crc = calculate_crc16(data)
    return calculated_crc == crc

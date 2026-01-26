"""
Modbus RTU通信基础模块
"""

import serial
import time
import struct
from typing import Optional, List
from .constants import FunctionCode, ExceptionCode, DataEndian, BROADCAST_ADDRESS
from .crc16 import calculate_crc16, verify_crc16


class ModbusRTUError(Exception):
    """Modbus RTU通信异常"""
    pass


class ModbusRTU:
    """
    Modbus RTU通信基础类
    负责底层的串口通信和帧的构建与解析
    """
    
    def __init__(self, port: str, baudrate: int = 921600, timeout: float = 1.0):
        """
        初始化Modbus RTU通信对象
        
        Args:
            port: 串口名称（如 'COM3' 或 '/dev/ttyUSB0'）
            baudrate: 波特率，默认921600
            timeout: 超时时间（秒），默认1.0
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        
    def connect(self) -> None:
        """
        打开串口连接
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
        except serial.SerialException as e:
            raise ModbusRTUError(f"无法打开串口 {self.port}: {e}")
    
    def disconnect(self) -> None:
        """
        关闭串口连接
        """
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.serial_conn = None
    
    def is_connected(self) -> bool:
        """
        检查串口是否已连接
        
        Returns:
            True表示已连接，False表示未连接
        """
        return self.serial_conn is not None and self.serial_conn.is_open
    
    def _build_frame(self, slave_address: int, function_code: int, 
                    data: bytes, endian: str = DataEndian.BIG_ENDIAN) -> bytes:
        """
        构建Modbus RTU帧
        
        Args:
            slave_address: 从设备地址
            function_code: 功能码
            data: 数据域内容
            endian: 字节序（大端或小端）
            
        Returns:
            完整的Modbus RTU帧（包括地址、功能码、数据、CRC）
        """
        frame = bytes([slave_address, function_code]) + data
        crc = calculate_crc16(frame)
        return frame + crc
    
    def _parse_response(self, response: bytes, expected_function_code: int,
                       endian: str = DataEndian.BIG_ENDIAN) -> bytes:
        """
        解析Modbus RTU响应帧
        
        Args:
            response: 接收到的响应数据
            expected_function_code: 期望的功能码
            endian: 字节序
            
        Returns:
            数据域内容（不包括地址、功能码、CRC）
            
        Raises:
            ModbusRTUError: 如果响应格式错误或包含异常码
        """
        if len(response) < 4:  # 最小帧长度：地址(1) + 功能码(1) + CRC(2)
            raise ModbusRTUError("响应帧长度不足")
        
        # 检查CRC
        frame_data = response[:-2]
        crc_received = response[-2:]
        if not verify_crc16(frame_data, crc_received):
            raise ModbusRTUError("CRC校验失败")
        
        function_code = response[1]
        
        # 检查是否为异常响应
        if function_code & FunctionCode.EXCEPTION_MASK:
            exception_code = response[2]
            exception_name = ExceptionCode(exception_code).name if exception_code in [e.value for e in ExceptionCode] else f"未知异常({exception_code})"
            raise ModbusRTUError(f"Modbus异常响应: {exception_name} (异常码: 0x{exception_code:02X})")
        
        # 检查功能码是否匹配
        if function_code != expected_function_code:
            raise ModbusRTUError(f"功能码不匹配: 期望0x{expected_function_code:02X}, 收到0x{function_code:02X}")
        
        # 返回数据域（不包括地址、功能码、CRC）
        return response[2:-2]
    
    def send_request(self, slave_address: int, function_code: int, 
                    data: bytes, endian: str = DataEndian.BIG_ENDIAN,
                    expect_response: bool = True) -> Optional[bytes]:
        """
        发送Modbus请求并接收响应
        
        Args:
            slave_address: 从设备地址
            function_code: 功能码
            data: 数据域内容
            endian: 字节序
            expect_response: 是否期望响应（广播地址不返回响应）
            
        Returns:
            响应数据域内容，如果expect_response=False则返回None
            
        Raises:
            ModbusRTUError: 如果通信失败
        """
        if not self.is_connected():
            raise ModbusRTUError("串口未连接")
        
        # 构建请求帧
        request_frame = self._build_frame(slave_address, function_code, data, endian)
        
        # 清空接收缓冲区
        self.serial_conn.reset_input_buffer()
        
        # 发送请求
        self.serial_conn.write(request_frame)
        self.serial_conn.flush()
        
        # 如果是广播地址，不等待响应
        if slave_address == BROADCAST_ADDRESS or not expect_response:
            return None
        
        # 等待并接收响应
        # 对于高速读取，减少固定延迟，改为动态等待
        if function_code == FunctionCode.READ_ALL_PRESSURE_VALUES:
            # 0x42功能码响应较快，减少延迟
            time.sleep(0.001)  # 仅等待1ms，让数据开始到达
        else:
            time.sleep(0.01)  # 其他功能码保持原延迟
        
        # 读取响应（需要根据实际帧长度动态读取）
        response = self._read_response()
        
        if response is None:
            raise ModbusRTUError("未收到响应或响应超时")
        # hex_str = response.hex(' ').upper()  # 空格分隔，大写显示（推荐，符合协议文档风格）
        # print("接收数据（16进制）：", hex_str)
        # 解析响应
        return self._parse_response(response, function_code, endian)
    
    def _read_response(self) -> Optional[bytes]:
        """
        读取Modbus响应帧
        
        Returns:
            响应数据，如果超时则返回None
        """
        start_time = time.perf_counter()  # 使用更高精度的计时
        buffer = bytes()
        
        # 等待至少4个字节（最小帧长度）
        while len(buffer) < 4:
            if time.perf_counter() - start_time > self.timeout:
                return None
            if self.serial_conn.in_waiting > 0:
                buffer += self.serial_conn.read(self.serial_conn.in_waiting)
            else:
                # 只有在没有数据时才sleep，减少延迟
                time.sleep(0.0001)  # 减少sleep时间到0.1ms
        
        # 根据功能码确定帧长度
        if len(buffer) >= 2:
            function_code = buffer[1]
            
            # 异常响应：地址(1) + 功能码(1) + 异常码(1) + CRC(2) = 5字节
            if function_code & FunctionCode.EXCEPTION_MASK:
                expected_length = 5
            # 0x03读保持寄存器：地址(1) + 功能码(1) + 字节数(1) + 数据(N*2) + CRC(2)
            elif function_code == FunctionCode.READ_HOLDING_REGISTERS:
                if len(buffer) >= 3:
                    byte_count = buffer[2]
                    expected_length = 3 + byte_count + 2
                else:
                    expected_length = 3 + 2
            # 0x06写单个寄存器：地址(1) + 功能码(1) + 地址(2) + 值(2) + CRC(2) = 8字节
            elif function_code == FunctionCode.WRITE_SINGLE_REGISTER:
                expected_length = 8
            # 0x10写多个寄存器：地址(1) + 功能码(1) + 起始地址(2) + 数量(2) + CRC(2) = 8字节
            elif function_code == FunctionCode.WRITE_MULTIPLE_REGISTERS:
                expected_length = 8
            # 0x41读取指定信息：地址(1) + 功能码(1) + 索引(1) + 长度(1) + 内容(N) + CRC(2)
            elif function_code == FunctionCode.READ_SPECIFIC_INFO:
                if len(buffer) >= 4:
                    content_length = buffer[3]
                    expected_length = 4 + content_length + 2
                else:
                    expected_length = 4 + 2
            # 0x42读取所有压力值：地址(1) + 功能码(1) + 数据长度(2) + 数据(N*2) + CRC(2)
            elif function_code == FunctionCode.READ_ALL_PRESSURE_VALUES:
                if len(buffer) >= 4:
                    data_length = int.from_bytes(buffer[2:4], byteorder='little')
                    expected_length = 4 + data_length + 2
                else:
                    expected_length = 4 + 2
            else:
                # 未知功能码，尝试读取更多数据
                expected_length = 256  # 最大帧长度
            
            # 等待完整帧
            while len(buffer) < expected_length:
                if time.perf_counter() - start_time > self.timeout:
                    break
                if self.serial_conn.in_waiting > 0:
                    buffer += self.serial_conn.read(self.serial_conn.in_waiting)
                else:
                    # 只有在没有数据时才sleep
                    time.sleep(0.0001)  # 减少sleep时间到0.1ms
        
        return buffer if len(buffer) >= 4 else None
    
    def read_holding_registers(self, slave_address: int, start_address: int, 
                              count: int) -> List[int]:
        """
        读保持寄存器（功能码0x03）
        
        Args:
            slave_address: 从设备地址
            start_address: 起始寄存器地址
            count: 寄存器数量（1-125）
            
        Returns:
            寄存器值列表
            
        Raises:
            ModbusRTUError: 如果通信失败
        """
        if count < 1 or count > 125:
            raise ValueError("寄存器数量必须在1-125之间")
        
        # 构建数据域（大端模式）
        data = start_address.to_bytes(2, byteorder='big') + count.to_bytes(2, byteorder='big')
        
        # 发送请求
        response_data = self.send_request(slave_address, FunctionCode.READ_HOLDING_REGISTERS, data)
        
        if response_data is None or len(response_data) < 1:
            raise ModbusRTUError("响应数据无效")
        
        byte_count = response_data[0]
        if byte_count != count * 2:
            raise ModbusRTUError(f"响应数据长度不匹配: 期望{count*2}字节, 收到{byte_count}字节")
        
        # 解析寄存器值（大端模式）
        values = []
        for i in range(count):
            value_bytes = response_data[1 + i*2:1 + (i+1)*2]
            value = int.from_bytes(value_bytes, byteorder='big')
            values.append(value)
        
        return values
    
    def write_single_register(self, slave_address: int, address: int, value: int) -> None:
        """
        写单个保持寄存器（功能码0x06）
        
        Args:
            slave_address: 从设备地址
            address: 寄存器地址
            value: 寄存器值（0-65535）
            
        Raises:
            ModbusRTUError: 如果通信失败
        """
        if value < 0 or value > 65535:
            raise ValueError("寄存器值必须在0-65535之间")
        
        # 构建数据域（大端模式）
        data = address.to_bytes(2, byteorder='big') + value.to_bytes(2, byteorder='big')
        
        # 广播地址不返回响应，跳过回显校验
        expect_response = slave_address != BROADCAST_ADDRESS
        response_data = self.send_request(
            slave_address,
            FunctionCode.WRITE_SINGLE_REGISTER,
            data,
            expect_response=expect_response,
        )
        
        if not expect_response:
            return
        
        # 验证响应（响应应该回显请求的数据）
        if response_data is None or len(response_data) != 4:
            raise ModbusRTUError("响应数据无效")
        
        resp_address = int.from_bytes(response_data[0:2], byteorder='big')
        resp_value = int.from_bytes(response_data[2:4], byteorder='big')
        
        if resp_address != address or resp_value != value:
            raise ModbusRTUError("响应数据与请求不匹配")
    
    def write_multiple_registers(self, slave_address: int, start_address: int, 
                                 values: List[int]) -> None:
        """
        写多个保持寄存器（功能码0x10）
        
        Args:
            slave_address: 从设备地址
            start_address: 起始寄存器地址
            values: 寄存器值列表（每个值0-65535，最多123个）
            
        Raises:
            ModbusRTUError: 如果通信失败
        """
        if len(values) < 1 or len(values) > 123:
            raise ValueError("寄存器数量必须在1-123之间")
        
        # 构建数据域（大端模式）
        count = len(values)
        data = start_address.to_bytes(2, byteorder='big')
        data += count.to_bytes(2, byteorder='big')
        data += bytes([count * 2])  # 字节数
        
        for value in values:
            if value < 0 or value > 65535:
                raise ValueError(f"寄存器值必须在0-65535之间: {value}")
            data += value.to_bytes(2, byteorder='big')
        
        # 广播地址不返回响应，跳过回显校验
        expect_response = slave_address != BROADCAST_ADDRESS
        response_data = self.send_request(
            slave_address,
            FunctionCode.WRITE_MULTIPLE_REGISTERS,
            data,
            expect_response=expect_response,
        )
        
        if not expect_response:
            return
        
        # 验证响应
        if response_data is None or len(response_data) != 4:
            raise ModbusRTUError("响应数据无效")
        
        resp_address = int.from_bytes(response_data[0:2], byteorder='big')
        resp_count = int.from_bytes(response_data[2:4], byteorder='big')
        
        if resp_address != start_address or resp_count != count:
            raise ModbusRTUError("响应数据与请求不匹配")
    
    def read_specific_info(self, slave_address: int, info_index: int) -> str:
        """
        读取指定信息（功能码0x41，扩展）
        
        Args:
            slave_address: 从设备地址
            info_index: 信息索引（见InfoIndex枚举）
            
        Returns:
            信息内容（ASCII字符串）
            
        Raises:
            ModbusRTUError: 如果通信失败
        """
        # 构建数据域（小端模式）
        data = bytes([info_index])
        
        # 发送请求
        response_data = self.send_request(
            slave_address, 
            FunctionCode.READ_SPECIFIC_INFO, 
            data, 
            endian=DataEndian.LITTLE_ENDIAN
        )
        
        if response_data is None or len(response_data) < 2:
            raise ModbusRTUError("响应数据无效")
        
        resp_index = response_data[0]
        if resp_index != info_index:
            raise ModbusRTUError(f"信息索引不匹配: 期望{info_index}, 收到{resp_index}")
        
        # 解析信息内容（ASCII字符串）
        content_length = response_data[1]
        if len(response_data) < 2 + content_length:
            raise ModbusRTUError("响应数据长度不足")
        
        content = response_data[2:2+content_length].decode('ascii', errors='ignore')
        return content
    
    def _read_response_fast_0x42(self, slave_address: int) -> Optional[bytes]:
        """
        快速读取0x42功能码的响应帧（专门优化版本）
        
        Args:
            slave_address: 期望的从设备地址
            
        Returns:
            完整的响应帧（包括地址、功能码、数据、CRC），如果超时则返回None
        """
        start_time = time.perf_counter()
        buffer = bytes()
        in_waiting = self.serial_conn.in_waiting
        
        # 等待至少4个字节（地址+功能码+数据长度低字节+数据长度高字节）
        while len(buffer) < 4:
            if time.perf_counter() - start_time > self.timeout:
                return None
            in_waiting = self.serial_conn.in_waiting
            if in_waiting > 0:
                buffer += self.serial_conn.read(in_waiting)
            # 完全移除sleep，使用非阻塞模式
        
        # 检查地址和功能码
        if buffer[0] != slave_address or buffer[1] != FunctionCode.READ_ALL_PRESSURE_VALUES:
            # 地址或功能码不匹配，返回None
            return None
        
        # 检查异常响应
        if buffer[1] & FunctionCode.EXCEPTION_MASK:
            return buffer[:5] if len(buffer) >= 5 else None
        
        # 读取数据长度（小端模式，2字节）
        data_length = struct.unpack('<H', buffer[2:4])[0]  # 使用struct更快
        expected_length = 4 + data_length + 2  # 地址+功能码+数据长度+数据+CRC
        
        # 等待完整帧
        while len(buffer) < expected_length:
            if time.perf_counter() - start_time > self.timeout:
                return None
            in_waiting = self.serial_conn.in_waiting
            if in_waiting > 0:
                buffer += self.serial_conn.read(in_waiting)
            # 完全移除sleep，使用非阻塞模式
        
        return buffer if len(buffer) >= expected_length else None
    
    def read_all_pressure_values(self, slave_address: int) -> List[int]:
        """
        读取所有压力值（功能码0x42，扩展）- 高度优化版本
        
        Args:
            slave_address: 从设备地址
            
        Returns:
            压力值列表（每个压力点一个值）
            
        Raises:
            ModbusRTUError: 如果通信失败
        """
        if not self.is_connected():
            raise ModbusRTUError("串口未连接")
        
        # 构建请求帧（功能码0x42无需数据域）
        request_frame = self._build_frame(slave_address, FunctionCode.READ_ALL_PRESSURE_VALUES, bytes(), DataEndian.LITTLE_ENDIAN)
        
        # 清空接收缓冲区并发送请求（合并操作）
        self.serial_conn.reset_input_buffer()
        self.serial_conn.write(request_frame)
        self.serial_conn.flush()
        
        # 使用快速响应读取函数（无延时，直接读取）
        response = self._read_response_fast_0x42(slave_address)
        
        if response is None:
            raise ModbusRTUError("未收到响应或响应超时")
        
        # 快速CRC校验
        if not verify_crc16(response[:-2], response[-2:]):
            raise ModbusRTUError("CRC校验失败")
        
        # 检查异常响应
        if response[1] & FunctionCode.EXCEPTION_MASK:
            exception_code = response[2]
            raise ModbusRTUError(f"Modbus异常响应 (异常码: 0x{exception_code:02X})")
        
        # 快速解析：直接从响应中提取压力数据并解析
        # 跳过: 地址(1) + 功能码(1) + 数据长度(2)，取到倒数第3个字节（CRC前）
        data_length = struct.unpack('<H', response[2:4])[0]
        
        # 使用struct一次性解析所有uint16值（小端）
        # 数据从第5个字节开始（索引4），长度为data_length
        pressure_values = struct.unpack(f'<{data_length//2}H', response[4:4+data_length])
        
        return list(pressure_values)
    
    def read_all_pressure_values_fast(self, slave_address: int) -> Optional[List[int]]:
        """
        读取所有压力值（功能码0x42）- 超高速版本（无异常抛出，适合高频循环）
        
        Args:
            slave_address: 从设备地址
            
        Returns:
            压力值列表，如果读取失败返回None
            
        Note:
            此版本专为高频读取优化，不抛出异常，失败时返回None
            建议在确认设备正常工作后使用此函数进行高速数据采集
        """
        if not self.is_connected():
            return None
        
        try:
            # 构建并发送请求
            request_frame = self._build_frame(slave_address, FunctionCode.READ_ALL_PRESSURE_VALUES, bytes(), DataEndian.LITTLE_ENDIAN)
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(request_frame)
            self.serial_conn.flush()
            
            # 快速读取响应
            response = self._read_response_fast_0x42(slave_address)
            if response is None or len(response) < 6:
                return None
            
            # 快速CRC校验（可选，为了速度可以跳过）
            if not verify_crc16(response[:-2], response[-2:]):
                return None
            
            # 检查异常
            if response[1] & FunctionCode.EXCEPTION_MASK:
                return None
            
            # 快速解析数据
            data_length = struct.unpack('<H', response[2:4])[0]
            if len(response) < 4 + data_length + 2:
                return None
            
            return list(struct.unpack(f'<{data_length//2}H', response[4:4+data_length]))
            
        except Exception:
            return None
    
    def read_active_upload_frame(self, pressure_point_count: Optional[int] = None) -> Optional[List[int]]:
        """
        读取主动上传帧（非标准Modbus帧）
        
        Args:
            pressure_point_count: 压力点总数，如果为None则尝试自动检测
        
        Returns:
            压力值列表，如果没有数据则返回None
            
        Note:
            根据协议文档，主动上传帧格式为：帧头(0xA55A) + 数据(N个uint16) + CRC16
            如果没有提供pressure_point_count，将尝试读取可用数据并通过CRC验证
        """
        if not self.is_connected():
            return None
        
        if self.serial_conn.in_waiting < 4:  # 至少需要帧头(2) + 最小数据(2)
            return None
        
        # 检查帧头
        header = self.serial_conn.read(2)
        if len(header) != 2:
            return None
        
        frame_header = int.from_bytes(header, byteorder='little')
        if frame_header != 0xA55A:
            # 不是主动上传帧，将数据放回缓冲区
            self.serial_conn.reset_input_buffer()
            return None
        
        # 根据压力点总数确定数据长度
        if pressure_point_count is not None:
            data_length = pressure_point_count * 2  # 每个压力点2字节
        else:
            # 如果没有指定，尝试读取所有可用数据（最大256字节，减去帧头和CRC）
            # 但需要确保数据长度是2的倍数
            available = self.serial_conn.in_waiting
            # 保留2字节给CRC
            max_data_length = min(available - 2, 250)  # 最大250字节数据
            # 确保是2的倍数
            data_length = (max_data_length // 2) * 2
        
        if data_length < 2:
            return None
        
        # 等待足够的数据
        if self.serial_conn.in_waiting < data_length + 2:  # +2 for CRC
            return None
        
        # 读取数据和CRC
        data = self.serial_conn.read(data_length)
        crc_received = self.serial_conn.read(2)
        
        if len(data) != data_length or len(crc_received) != 2:
            return None
        
        # 验证CRC
        frame_data = header + data
        if not verify_crc16(frame_data, crc_received):
            return None
        
        # 解析压力值（小端模式，每个值2字节）
        pressure_values = []
        for i in range(0, data_length, 2):
            if i + 2 <= data_length:
                value = int.from_bytes(data[i:i+2], byteorder='little')
                pressure_values.append(value)
        
        return pressure_values

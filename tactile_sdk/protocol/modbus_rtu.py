"""
Modbus RTU 协议层
=================
负责将 API 层的高级操作翻译为 Modbus RTU 帧，并通过 ``SerialTransport``
完成帧的发送与接收解析。

本层只关心：
- 帧的构建（地址 + 功能码 + 数据域 + CRC）
- 帧的发送与响应接收
- 响应帧的合法性验证（CRC、功能码、异常码）
- 具体功能码的请求/响应编解码

不关心：业务含义（由 API 层处理）、串口参数（由 Transport 层管理）。
"""

from __future__ import annotations

import struct
import time
from typing import List, Optional

from ..exceptions import CommunicationError, ProtocolError
from .crc16 import calculate_crc16, verify_crc16
from ..transport.serial_transport import SerialTransport
from .constants import (
    BROADCAST_ADDRESS,
    DataEndian,
    ExceptionCode,
    FunctionCode,
)


class ModbusRTU:
    """
    Modbus RTU 协议处理器。

    接受一个已初始化的 ``SerialTransport`` 实例，不自行管理连接生命周期。
    调用任何请求方法前，必须保证 ``transport.is_open == True``。
    """

    # 发送帧后等待设备开始返回第一个字节的最短时间（秒）
    # 适用于标准 Modbus 命令（非高频 0x42 路径）
    _SEND_WAIT_SECS: float = 0.005

    def __init__(
        self,
        transport: SerialTransport,
        send_wait_secs: float = 0.005,
    ) -> None:
        """
        Args:
            transport:      已配置好的串口传输实例（不需要已打开）。
            send_wait_secs: 发送请求帧后等待设备开始响应的时间（秒），
                            默认 0.005。低延迟设备或高波特率可适当减小。
        """
        self._transport = transport
        self._send_wait_secs = send_wait_secs

    # ------------------------------------------------------------------
    # 内部：帧构建
    # ------------------------------------------------------------------

    @staticmethod
    def _build_frame(
        slave_address: int,
        function_code: int,
        data: bytes,
    ) -> bytes:
        """构建完整 Modbus RTU 帧（含 CRC）。"""
        frame = bytes([slave_address, function_code]) + data
        return frame + calculate_crc16(frame)

    # ------------------------------------------------------------------
    # 内部：响应接收
    # ------------------------------------------------------------------

    def _read_response(self) -> Optional[bytes]:
        """
        动态读取一帧完整 Modbus 响应。

        根据已接收到的功能码自动推断期望帧长度，待数据到齐或超时后返回。

        Returns:
            完整响应帧字节序列，超时则返回 ``None``。
        """
        start = time.perf_counter()
        buf = b""

        # --- 等待至少 4 字节（地址 + 功能码 + 至少 2 字节有效载荷）---
        while len(buf) < 4:
            if time.perf_counter() - start > self._transport.timeout:
                return None
            waiting = self._transport.in_waiting
            if waiting > 0:
                buf += self._transport.read(waiting)
            else:
                time.sleep(0.0001)

        func = buf[1]
        # 异常响应：5 字节固定长度
        if func & FunctionCode.EXCEPTION_MASK:
            expected = 5
        elif func == FunctionCode.READ_HOLDING_REGISTERS:
            expected = (3 + buf[2] + 2) if len(buf) >= 3 else 5
        elif func == FunctionCode.WRITE_SINGLE_REGISTER:
            expected = 8
        elif func == FunctionCode.READ_SPECIFIC_INFO:
            expected = (4 + buf[3] + 2) if len(buf) >= 4 else 6
        elif func == FunctionCode.READ_ALL_PRESSURE_VALUES:
            if len(buf) >= 4:
                data_len = int.from_bytes(buf[2:4], "little")
                expected = 4 + data_len + 2
            else:
                expected = 6
        else:
            expected = 256  # 未知功能码，尽量多读

        while len(buf) < expected:
            if time.perf_counter() - start > self._transport.timeout:
                break
            waiting = self._transport.in_waiting
            if waiting > 0:
                buf += self._transport.read(waiting)
            else:
                time.sleep(0.0001)

        return buf if len(buf) >= 4 else None

    def _read_response_fast_0x42(self, slave_address: int) -> Optional[bytes]:
        """
        专为 0x42 功能码优化的响应读取（无 sleep，轮询模式）。

        Args:
            slave_address: 期望的从设备地址（用于基本校验）。

        Returns:
            完整响应帧，超时返回 ``None``。
        """
        start = time.perf_counter()
        buf = b""

        while len(buf) < 4:
            if time.perf_counter() - start > self._transport.timeout:
                return None
            waiting = self._transport.in_waiting
            if waiting > 0:
                buf += self._transport.read(waiting)

        if buf[0] != slave_address or buf[1] != FunctionCode.READ_ALL_PRESSURE_VALUES:
            return None

        if buf[1] & FunctionCode.EXCEPTION_MASK:
            return buf[:5] if len(buf) >= 5 else None

        data_len = struct.unpack("<H", buf[2:4])[0]
        expected = 4 + data_len + 2

        while len(buf) < expected:
            if time.perf_counter() - start > self._transport.timeout:
                return None
            waiting = self._transport.in_waiting
            if waiting > 0:
                buf += self._transport.read(waiting)

        return buf if len(buf) >= expected else None

    # ------------------------------------------------------------------
    # 内部：响应解析
    # ------------------------------------------------------------------

    def _parse_response(
        self,
        response: bytes,
        expected_function_code: int,
    ) -> bytes:
        """
        验证响应帧并提取数据域。

        Args:
            response:               完整响应帧（含地址、功能码、CRC）。
            expected_function_code: 期望的功能码。

        Returns:
            数据域字节（不含地址、功能码、CRC）。

        Raises:
            CommunicationError: 帧太短或 CRC 不匹配。
            ProtocolError:      包含 Modbus 异常码或功能码不一致。
        """
        if len(response) < 4:
            raise CommunicationError(f"响应帧长度不足（{len(response)} 字节）")

        if not verify_crc16(response[:-2], response[-2:]):
            raise CommunicationError("CRC16 校验失败")

        func = response[1]

        if func & FunctionCode.EXCEPTION_MASK:
            exc_code = response[2]
            try:
                exc_name = ExceptionCode(exc_code).name
            except ValueError:
                exc_name = f"UNKNOWN(0x{exc_code:02X})"
            raise ProtocolError(
                f"Modbus 异常响应: {exc_name} (异常码 0x{exc_code:02X})"
            )

        if func != expected_function_code:
            raise ProtocolError(
                f"功能码不匹配：期望 0x{expected_function_code:02X}，"
                f"收到 0x{func:02X}"
            )

        return response[2:-2]

    # ------------------------------------------------------------------
    # 内部：发送请求
    # ------------------------------------------------------------------

    def _send_and_receive(
        self,
        slave_address: int,
        function_code: int,
        data: bytes,
        expect_response: bool = True,
        fast_0x42: bool = False,
    ) -> Optional[bytes]:
        """
        发送 Modbus 请求帧并等待接收响应。

        Args:
            slave_address:    从设备地址。
            function_code:    功能码。
            data:             数据域。
            expect_response:  是否期待响应（广播地址无需响应）。
            fast_0x42:        是否使用 0x42 专用快速读取路径。

        Returns:
            响应数据域；若 ``expect_response=False`` 则返回 ``None``。

        Raises:
            CommunicationError: 串口未连接或未收到响应。
        """
        if not self._transport.is_open:
            raise CommunicationError("串口未连接，请先调用 connect()")

        frame = self._build_frame(slave_address, function_code, data)
        self._transport.reset_input_buffer()
        self._transport.write(frame)

        if slave_address == BROADCAST_ADDRESS or not expect_response:
            return None

        if fast_0x42:
            response = self._read_response_fast_0x42(slave_address)
        else:
            # 非 0x42 功能码加少量等待，保证数据开始到达
            time.sleep(self._send_wait_secs)
            response = self._read_response()

        if response is None:
            raise CommunicationError("未收到响应或响应超时")

        return self._parse_response(response, function_code)

    # ------------------------------------------------------------------
    # 公共：标准 Modbus 命令
    # ------------------------------------------------------------------

    def read_holding_registers(
        self,
        slave_address: int,
        start_address: int,
        count: int,
    ) -> List[int]:
        """
        读保持寄存器（功能码 0x03）。

        Args:
            slave_address: 从设备地址。
            start_address: 起始寄存器地址。
            count:         读取数量（1–125）。

        Returns:
            寄存器值列表（大端，无符号 16 位）。
        """
        data = (
            start_address.to_bytes(2, "big")
            + count.to_bytes(2, "big")
        )
        resp = self._send_and_receive(slave_address, FunctionCode.READ_HOLDING_REGISTERS, data)

        if resp is None or len(resp) < 1:
            raise CommunicationError("读保持寄存器：响应数据无效")

        byte_count = resp[0]
        if byte_count != count * 2:
            raise CommunicationError(
                f"读保持寄存器：字节数不匹配（期望 {count * 2}，收到 {byte_count}）"
            )

        return [
            int.from_bytes(resp[1 + i * 2: 1 + (i + 1) * 2], "big")
            for i in range(count)
        ]

    def write_single_register(
        self,
        slave_address: int,
        address: int,
        value: int,
    ) -> None:
        """
        写单个保持寄存器（功能码 0x06）。

        Args:
            slave_address: 从设备地址（0 = 广播，不等待响应）。
            address:       寄存器地址。
            value:         写入值（0–65535）。
        """
        data = address.to_bytes(2, "big") + value.to_bytes(2, "big")
        expect = slave_address != BROADCAST_ADDRESS
        resp = self._send_and_receive(
            slave_address, FunctionCode.WRITE_SINGLE_REGISTER, data,
            expect_response=expect,
        )

        if not expect:
            return

        if resp is None or len(resp) != 4:
            raise CommunicationError("写单个寄存器：响应数据无效")

        resp_addr = int.from_bytes(resp[0:2], "big")
        resp_val = int.from_bytes(resp[2:4], "big")
        if resp_addr != address or resp_val != value:
            raise ProtocolError("写单个寄存器：响应回显与请求不一致")

    # ------------------------------------------------------------------
    # 公共：扩展功能码 0x41
    # ------------------------------------------------------------------

    def read_specific_info(self, slave_address: int, info_index: int) -> str:
        """
        读取指定信息字符串（功能码 0x41，扩展，小端）。

        Args:
            slave_address: 从设备地址。
            info_index:    信息索引（见 ``InfoIndex`` 枚举）。

        Returns:
            ASCII 字符串内容。
        """
        resp = self._send_and_receive(
            slave_address,
            FunctionCode.READ_SPECIFIC_INFO,
            bytes([info_index]),
        )

        if resp is None or len(resp) < 2:
            raise CommunicationError("读取指定信息：响应数据无效")

        if resp[0] != info_index:
            raise ProtocolError(
                f"读取指定信息：索引不一致（期望 {info_index}，收到 {resp[0]}）"
            )

        content_len = resp[1]
        if len(resp) < 2 + content_len:
            raise CommunicationError("读取指定信息：响应数据长度不足")

        return resp[2: 2 + content_len].decode("ascii", errors="ignore")

    # ------------------------------------------------------------------
    # 公共：扩展功能码 0x42
    # ------------------------------------------------------------------

    def read_all_pressure_values(self, slave_address: int) -> List[int]:
        """
        读取所有压力值（功能码 0x42，扩展，小端）。

        Returns:
            各压力点值列表（uint16，小端解析）。

        Raises:
            CommunicationError: 通信失败。
        """
        resp = self._send_and_receive(
            slave_address,
            FunctionCode.READ_ALL_PRESSURE_VALUES,
            b"",
            fast_0x42=True,
        )

        if resp is None or len(resp) < 2:
            raise CommunicationError("读取压力值：响应数据无效")

        data_len = int.from_bytes(resp[0:2], "little")
        if len(resp) < 2 + data_len:
            raise CommunicationError("读取压力值：数据长度不足")

        return list(struct.unpack(f"<{data_len // 2}H", resp[2: 2 + data_len]))

    def read_all_pressure_values_fast(
        self, slave_address: int
    ) -> Optional[List[int]]:
        """
        读取所有压力值——高频采集专用版（不抛出异常，失败返回 ``None``）。

        适合在确认设备正常工作后，以 100 Hz+ 速率的热循环中使用。
        """
        if not self._transport.is_open:
            return None
        try:
            frame = self._build_frame(
                slave_address, FunctionCode.READ_ALL_PRESSURE_VALUES, b""
            )
            self._transport.reset_input_buffer()
            self._transport.write(frame)

            response = self._read_response_fast_0x42(slave_address)
            if response is None or len(response) < 6:
                return None
            if not verify_crc16(response[:-2], response[-2:]):
                return None
            if response[1] & FunctionCode.EXCEPTION_MASK:
                return None

            data_len = struct.unpack("<H", response[2:4])[0]
            if len(response) < 4 + data_len + 2:
                return None

            return list(struct.unpack(f"<{data_len // 2}H", response[4: 4 + data_len]))
        except Exception:
            return None

"""
串口传输层
==========
对 pyserial 的 ``serial.Serial`` 进行轻量封装，只暴露 SDK 内部所需的最小接口。

职责
----
- 管理串口的生命周期（open / close）
- 提供原子级 I/O 操作（write / read / flush）
- 将 pyserial 的硬件异常转换为 SDK 内部的 ``DeviceConnectionError``

此层不了解任何 Modbus 协议细节。
"""

from __future__ import annotations

from typing import Optional

import serial

from ..exceptions import CommunicationError, DeviceConnectionError


class SerialTransport:
    """
    串口物理传输层。

    只负责字节级的发送与接收，不包含任何协议逻辑。
    """

    def __init__(self, port: str, baudrate: int = 4_000_000, timeout: float = 1.0) -> None:
        """
        Args:
            port:     串口名称，例如 ``"COM6"`` 或 ``"/dev/ttyUSB0"``。
            baudrate: 波特率，默认 4 000 000。
            timeout:  读操作超时（秒），默认 1.0。
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    def open(self) -> None:
        """打开串口。已打开时调用为空操作。

        Raises:
            DeviceConnectionError: 无法打开目标串口时抛出。
        """
        if self.is_open:
            return
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
        except serial.SerialException as exc:
            raise DeviceConnectionError(f"无法打开串口 {self.port!r}: {exc}") from exc

    def close(self) -> None:
        """关闭串口。未打开时调用为空操作。"""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    @property
    def is_open(self) -> bool:
        """串口是否处于已连接状态。"""
        return self._serial is not None and self._serial.is_open

    # ------------------------------------------------------------------
    # I/O 操作
    # ------------------------------------------------------------------

    def _require_open(self) -> None:
        """内部辅助：确保串口已打开，否则抛出 CommunicationError。"""
        if not self.is_open:
            raise CommunicationError("串口未连接，请先调用 connect()")

    def write(self, data: bytes) -> None:
        """
        发送字节数据，发送后立即 flush。

        Args:
            data: 待发送的字节序列。
        """
        self._require_open()
        self._serial.write(data)
        self._serial.flush()

    def read(self, size: int) -> bytes:
        """
        从接收缓冲区读取最多 *size* 个字节。

        Args:
            size: 期望读取的字节数。

        Returns:
            实际读取到的字节（可能少于 *size*）。
        """
        self._require_open()
        return self._serial.read(size)

    def reset_input_buffer(self) -> None:
        """清空接收缓冲区，丢弃尚未读取的数据。"""
        self._require_open()
        self._serial.reset_input_buffer()

    @property
    def in_waiting(self) -> int:
        """接收缓冲区中当前可读取的字节数。"""
        if not self.is_open:
            return 0
        return self._serial.in_waiting

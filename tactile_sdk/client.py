"""
TactilePressureSDK — 主客户端
==============================
顶层门面（Facade）类，将四个领域 API 组合为统一入口。

使用方式
--------
上下文管理器（推荐）::

    from tactile_sdk import TactilePressureSDK

    with TactilePressureSDK("COM6") as sdk:
        info = sdk.device.get_info()
        pressures = sdk.pressure.read_all()

手动管理连接::

    sdk = TactilePressureSDK("COM6", slave_address=2)
    sdk.connect()
    try:
        sdk.config.set_pressure_value_type(1)
        values = sdk.pressure.read_fast()
    finally:
        sdk.disconnect()

分层结构
--------
::

    TactilePressureSDK          ← 门面层（本文件）
    ├── sdk.device              DeviceAPI   设备信息 & 地址
    ├── sdk.config              ConfigAPI   传感器参数配置
    ├── sdk.pressure            PressureAPI 压力数据读取
    └── sdk.calibration         CalibrationAPI 标定操作
            ↑（共享同一 ModbusRTU 实例）
        ModbusRTU               协议层  帧构建 & 解析
            ↑
        SerialTransport         传输层  串口 I/O
"""

from __future__ import annotations

from .api.calibration_api import CalibrationAPI
from .api.config_api import ConfigAPI
from .api.device_api import DeviceAPI
from .api.pressure_api import PressureAPI
from .exceptions import ValidationError
from .protocol.constants import (
    DEFAULT_BAUDRATE,
    DEFAULT_SEND_WAIT_SECS,
    DEFAULT_TIMEOUT,
    MIN_SLAVE_ADDRESS,
    MAX_SLAVE_ADDRESS,
)
from .protocol.modbus_rtu import ModbusRTU
from .transport.serial_transport import SerialTransport


class TactilePressureSDK:
    """
    玄雅 / Synria 科技触觉压力采集模块 Python SDK。

    Parameters
    ----------
    port:
        串口名称，例如 ``"COM6"`` 或 ``"/dev/ttyUSB0"``。
    slave_address:
        从设备 Modbus 地址（1–247），默认 ``1``。
    baudrate:
        串口波特率，默认 ``4_000_000``。
    timeout:
        读操作超时秒数，默认 ``1.0``。
    """

    def __init__(
        self,
        port: str,
        slave_address: int = 1,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        send_wait_secs: float = DEFAULT_SEND_WAIT_SECS,
    ) -> None:
        if not (MIN_SLAVE_ADDRESS <= slave_address <= MAX_SLAVE_ADDRESS):
            raise ValidationError(
                f"从设备地址须在 {MIN_SLAVE_ADDRESS}–{MAX_SLAVE_ADDRESS} 之间，"
                f"当前值：{slave_address}"
            )

        # --- 传输层 ---
        self._transport = SerialTransport(port, baudrate, timeout)

        # --- 协议层 ---
        self._modbus = ModbusRTU(self._transport, send_wait_secs=send_wait_secs)

        # 共享地址容器：四个 API 实例共享同一个 list，
        # 保证 device.set_address() 后所有子域地址同步更新。
        self._addr_ref: list = [slave_address]

        # 共享软件层零点偏移容器：ConfigAPI 写入，PressureAPI 读取并应用。
        # 空列表 = 无偏移；非空时长度等于压力点数，逐点相减。
        self._zero_offsets: list = []

        # --- API 层（四个子域） ---
        self.device = DeviceAPI(self._modbus, self._addr_ref)
        """设备身份信息与地址管理，见 :class:`~tactile_sdk.api.device_api.DeviceAPI`。"""

        self.config = ConfigAPI(self._modbus, self._addr_ref, self._zero_offsets)
        """传感器参数配置，见 :class:`~tactile_sdk.api.config_api.ConfigAPI`。"""

        self.pressure = PressureAPI(self._modbus, self._addr_ref, self._zero_offsets)
        """压力数据读取，见 :class:`~tactile_sdk.api.pressure_api.PressureAPI`。"""

        self.calibration = CalibrationAPI(self._modbus, self._addr_ref)
        """标定操作，见 :class:`~tactile_sdk.api.calibration_api.CalibrationAPI`。"""

    # ------------------------------------------------------------------
    # 连接生命周期
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """打开串口连接。

        Raises:
            DeviceConnectionError: 无法打开串口时抛出。
        """
        self._transport.open()

    def disconnect(self) -> None:
        """关闭串口连接。未连接时调用为空操作。"""
        self._transport.close()

    @property
    def is_connected(self) -> bool:
        """当前串口是否处于已连接状态。"""
        return self._transport.is_open

    # ------------------------------------------------------------------
    # 上下文管理器
    # ------------------------------------------------------------------

    def __enter__(self) -> "TactilePressureSDK":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        return (
            f"TactilePressureSDK("
            f"port={self._transport.port!r}, "
            f"slave={self._addr_ref[0]}, "
            f"status={status})"
        )

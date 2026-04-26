"""
API 层基类
==========
所有领域 API 类（DeviceAPI、ConfigAPI 等）均继承自 ``BaseAPI``，
共享同一个 ``ModbusRTU`` 传输实例和从设备地址。
"""

from __future__ import annotations

from typing import List

from ..protocol.modbus_rtu import ModbusRTU


class BaseAPI:
    """API 层公共基类，持有 Modbus 传输实例与从设备地址。"""

    def __init__(self, modbus: ModbusRTU, addr_ref: List[int]) -> None:
        """
        Args:
            modbus:   已初始化的 Modbus RTU 协议实例。
            addr_ref: 共享从设备地址容器（单元素列表），由 TactilePressureSDK
                      统一创建并传入所有 API 子类，确保 set_address() 后全局同步。
        """
        self._modbus = modbus
        self._addr_ref = addr_ref

    @property
    def _slave_address(self) -> int:
        """当前目标从设备地址（读写均通过共享容器，始终与其他 API 实例同步）。"""
        return self._addr_ref[0]

    @_slave_address.setter
    def _slave_address(self, value: int) -> None:
        self._addr_ref[0] = value

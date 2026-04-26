"""
设备信息 API
============
提供读取设备型号、协议版本、固件版本以及设备 Modbus 地址等只读/配置接口。
"""

from __future__ import annotations

from ..exceptions import ValidationError
from ..models import DeviceInfo
from ..protocol.constants import (
    InfoIndex,
    MIN_SLAVE_ADDRESS,
    MAX_SLAVE_ADDRESS,
    RegisterAddress,
)
from .base import BaseAPI


class DeviceAPI(BaseAPI):
    """设备身份信息与地址管理 API。"""

    # ------------------------------------------------------------------
    # 设备信息读取
    # ------------------------------------------------------------------

    def get_model(self) -> str:
        """获取设备型号，例如 ``"ST-00-01"``。"""
        return self._modbus.read_specific_info(self._slave_address, InfoIndex.DEVICE_MODEL)

    def get_protocol_number(self) -> str:
        """获取协议编号，例如 ``"YF-e0-000001"``。"""
        return self._modbus.read_specific_info(self._slave_address, InfoIndex.PROTOCOL_NUMBER)

    def get_protocol_version(self) -> str:
        """获取协议版本，例如 ``"v1.2"``。"""
        return self._modbus.read_specific_info(self._slave_address, InfoIndex.PROTOCOL_VERSION)

    def get_app_version(self) -> str:
        """获取固件 App 版本，例如 ``"v1.0.1"``。"""
        return self._modbus.read_specific_info(self._slave_address, InfoIndex.APP_VERSION)

    def get_info(self) -> DeviceInfo:
        """
        一次性获取所有设备身份信息。

        Returns:
            ``DeviceInfo`` 数据对象。
        """
        return DeviceInfo(
            device_model=self.get_model(),
            protocol_number=self.get_protocol_number(),
            protocol_version=self.get_protocol_version(),
            app_version=self.get_app_version(),
        )

    # ------------------------------------------------------------------
    # 设备地址管理
    # ------------------------------------------------------------------

    def get_address(self) -> int:
        """
        读取当前设备 Modbus 地址（寄存器 0x0001）。

        Returns:
            设备地址（1–247）。
        """
        values = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.DEVICE_ADDRESS, 1
        )
        return values[0]

    def set_address(self, new_address: int, *, use_broadcast: bool = True) -> None:
        """
        修改设备 Modbus 地址。

        Args:
            new_address:   新地址（1–247）。
            use_broadcast: 使用广播地址发送（设备不返回响应）；默认 ``True``。

        Note:
            若 ``use_broadcast=True``，SDK 内部 ``_slave_address`` 会同步更新。
        """
        if not (MIN_SLAVE_ADDRESS <= new_address <= MAX_SLAVE_ADDRESS):
            raise ValidationError(
                f"设备地址必须在 {MIN_SLAVE_ADDRESS}–{MAX_SLAVE_ADDRESS} 之间，"
                f"当前值：{new_address}"
            )
        target = 0 if use_broadcast else self._slave_address
        self._modbus.write_single_register(target, RegisterAddress.DEVICE_ADDRESS, new_address)
        if use_broadcast:
            self._slave_address = new_address

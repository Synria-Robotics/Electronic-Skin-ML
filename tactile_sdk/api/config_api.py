"""
设备配置 API
============
负责所有可读写的传感器工作参数：上传模式、采样频率、压力值类型、
AD 屏蔽值、单点面积及归零控制。
"""

from __future__ import annotations

import time
from typing import List, Optional

from ..exceptions import CommunicationError, ProtocolError, ValidationError
from ..protocol.constants import RegisterAddress
from ..protocol.modbus_rtu import ModbusRTU
from .base import BaseAPI


class ConfigAPI(BaseAPI):
    """传感器设备参数配置 API。"""

    def __init__(
        self,
        modbus: ModbusRTU,
        addr_ref: List[int],
        zero_offsets_ref: List[int],
    ) -> None:
        """
        Args:
            modbus:           Modbus RTU 协议实例。
            addr_ref:         共享从设备地址容器。
            zero_offsets_ref: 共享软件层零点偏移容器（与 PressureAPI 共享同一个 list）。
        """
        super().__init__(modbus, addr_ref)
        self._zero_offsets_ref = zero_offsets_ref

    # ------------------------------------------------------------------
    # 主动上传
    # ------------------------------------------------------------------

    def get_auto_upload_flag(self) -> bool:
        """读取主动上传使能标志。"""
        values = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.AUTO_UPLOAD_FLAG, 1
        )
        return values[0] == 1

    def set_auto_upload_flag(self, enable: bool) -> None:
        """
        设置主动上传使能。

        Args:
            enable: ``True`` 开启，``False`` 关闭。
        """
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.AUTO_UPLOAD_FLAG, 1 if enable else 0
        )

    def get_auto_upload_frequency(self) -> int:
        """
        读取主动上传频率。

        Returns:
            频率值（50–200 Hz）。
        """
        values = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.AUTO_UPLOAD_FREQUENCY, 1
        )
        return values[0]

    def set_auto_upload_frequency(self, frequency: int) -> None:
        """
        设置主动上传频率。

        Args:
            frequency: 50–200 Hz。
        """
        if not (50 <= frequency <= 200):
            raise ValidationError(f"上传频率须在 50–200 Hz 范围内，当前值：{frequency}")
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.AUTO_UPLOAD_FREQUENCY, frequency
        )

    # ------------------------------------------------------------------
    # 压力值类型
    # ------------------------------------------------------------------

    def get_pressure_value_type(self) -> int:
        """
        读取压力值输出类型。

        Returns:
            ``0`` = AD 原始值，``1`` = 标定压力值（mN）。
        """
        values = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.PRESSURE_VALUE_TYPE, 1
        )
        return values[0]

    def set_pressure_value_type(self, value_type: int) -> None:
        """
        设置压力值输出类型。

        Args:
            value_type: ``0`` = AD 值，``1`` = 标定值。
        """
        if value_type not in (0, 1):
            raise ValidationError("压力值类型须为 0（AD 值）或 1（标定值）")
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.PRESSURE_VALUE_TYPE, value_type
        )

    # ------------------------------------------------------------------
    # AD 屏蔽值
    # ------------------------------------------------------------------

    def get_ad_mask_value(self) -> int:
        """读取 AD 屏蔽值（低于此值视为无压力）。"""
        values = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.AD_MASK_VALUE, 1
        )
        return values[0]

    def set_ad_mask_value(self, mask_value: int) -> None:
        """
        设置 AD 屏蔽值。

        Args:
            mask_value: 0–65535（12 位 ADC 最大 4095，16 位最大 65535）。
        """
        if mask_value < 0:
            raise ValidationError(f"AD 屏蔽值不能为负数，当前值：{mask_value}")
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.AD_MASK_VALUE, mask_value
        )

    # ------------------------------------------------------------------
    # 压力点总数 / 传感器点面积
    # ------------------------------------------------------------------

    def get_pressure_point_count(self) -> int:
        """读取传感器压力点总数（只读寄存器）。"""
        values = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.PRESSURE_POINT_COUNT, 1
        )
        return values[0]

    def get_sensor_point_area(self) -> float:
        """
        读取传感器单个点面积。

        Returns:
            面积值（单位：平方毫米，精度 0.1 mm²）。
        """
        values = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.SENSOR_POINT_AREA, 1
        )
        return values[0] * 0.1

    def set_sensor_point_area(self, area_mm2: float) -> None:
        """
        设置传感器单个点面积。

        Args:
            area_mm2: 面积（mm²，精度 0.1 mm²，范围 0–6553.5）。
        """
        raw = int(area_mm2 / 0.1)
        if not (0 <= raw <= 65535):
            raise ValidationError(f"面积值超出有效范围（0–6553.5 mm²），当前值：{area_mm2}")
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.SENSOR_POINT_AREA, raw
        )

    # ------------------------------------------------------------------
    # 归零控制
    # ------------------------------------------------------------------

    def get_auto_zero_enable(self) -> Optional[bool]:
        """
        尝试读取上电自动归零使能标志。

        Note:
            该寄存器在部分固件版本中为**只写**，读取时将返回 ``None``
            而非抛出异常，调用方据此判断设备是否支持读取。

        Returns:
            ``True`` = 已启用，``False`` = 已禁用，``None`` = 不支持读取。
        """
        try:
            values = self._modbus.read_holding_registers(
                self._slave_address, RegisterAddress.PRESSURE_AUTO_ZERO_ENABLE, 1
            )
            return values[0] == 1
        except ProtocolError as exc:
            if "ILLEGAL_DATA_ADDRESS" in str(exc):
                return None
            raise

    def set_auto_zero_enable(self, enable: bool) -> None:
        """
        设置上电自动归零使能（写寄存器 0x0011）。

        Note:
            该寄存器为只写；写入后需重启设备才能验证效果。

        Args:
            enable: ``True`` = 启用，``False`` = 禁用。
        """
        self._modbus.write_single_register(
            self._slave_address,
            RegisterAddress.PRESSURE_AUTO_ZERO_ENABLE,
            1 if enable else 0,
        )

    def trigger_dynamic_zero(self) -> None:
        """
        立即触发动态归零，效果等同于重新插拔设备。

        执行流程：
        1. 向寄存器 0x0012 写入 1，尝试触发硬件归零。
        2. 等待硬件处理（100 ms）。
        3. 读取当前各点压力值作为软件层基线，存入共享零点容器。

        后续所有 ``pressure.read_all()`` / ``pressure.read_fast()`` 均会逐点
        减去此基线并截断至 0，无论硬件命令是否实际生效，软件层均可保证归零效果。

        建议在传感器表面无负载时调用。
        """
        # 1. 硬件归零命令（兼容固件；若固件支持则硬件层同步归零）
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.PRESSURE_DYNAMIC_ZERO, 1
        )
        # 2. 给硬件留出处理时间
        time.sleep(0.1)
        # 3. 读取当前值作为软件基线（无论硬件是否生效，此步保证归零效果）
        baseline = self._modbus.read_all_pressure_values(self._slave_address)
        self._zero_offsets_ref.clear()
        self._zero_offsets_ref.extend(baseline)

    def reset_dynamic_zero(self) -> None:
        """
        重置动态归零，恢复出厂零点状态（撤销之前的 :meth:`trigger_dynamic_zero`）。

        同时清除软件层基线，使压力读取恢复为原始值。
        """
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.PRESSURE_DYNAMIC_ZERO, 2
        )
        self._zero_offsets_ref.clear()

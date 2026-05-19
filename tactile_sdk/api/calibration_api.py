"""
标定 API
========
提供传感器标定工作流，包括：
- 拟合点选择与单点写入
- 单点 / 全部标定模式切换与执行
- 标定数据清除
"""

from __future__ import annotations

from typing import Optional

from ..exceptions import ValidationError
from ..models import CalibrationStatus
from ..protocol.constants import (
    CALIBRATION_COMMAND_SAMPLE,
    CLEAR_CALIBRATION_COMMAND,
    CalibrationMode,
    RegisterAddress,
)
from .base import BaseAPI


class CalibrationAPI(BaseAPI):
    """传感器标定操作 API。"""

    # ------------------------------------------------------------------
    # 拟合点编号 / 压力点选择
    # ------------------------------------------------------------------

    def get_fitting_point(self) -> int:
        """读取当前选定的拟合点编号（1–11）。"""
        return self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.FITTING_POINT, 1
        )[0]

    def set_fitting_point(self, point: int) -> None:
        """
        选择拟合点。

        Args:
            point: 1–11。
        """
        if not (1 <= point <= 11):
            raise ValidationError(f"拟合点编号须在 1–11 范围内，当前值：{point}")
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.FITTING_POINT, point
        )

    def get_pressure_point(self) -> int:
        """读取当前选定的压力点编号（单点标定模式用）。"""
        return self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.PRESSURE_POINT, 1
        )[0]

    def set_pressure_point(self, point: int) -> None:
        """
        选择要标定的压力点（单点标定模式下必须先调用此方法）。

        Args:
            point: 压力点编号。
        """
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.PRESSURE_POINT, point
        )

    # ------------------------------------------------------------------
    # 拟合点 AD 值 / 压力值
    # ------------------------------------------------------------------

    def get_fitting_point_ad(self) -> int:
        """读取当前拟合点记录的 ADC 原始值。"""
        return self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.FITTING_POINT_AD_VALUE, 1
        )[0]

    def get_fitting_point_pressure(self) -> int:
        """读取当前拟合点记录的压力值（mN）。"""
        return self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.FITTING_POINT_PRESSURE_VALUE, 1
        )[0]

    def set_fitting_point_pressure(self, pressure_mn: int) -> None:
        """
        设置当前拟合点的压力值。

        Args:
            pressure_mn: 压力值（毫牛，0–65535）。
        """
        if not (0 <= pressure_mn <= 65535):
            raise ValidationError(f"压力值须在 0–65535 mN 范围内，当前值：{pressure_mn}")
        self._modbus.write_single_register(
            self._slave_address,
            RegisterAddress.FITTING_POINT_PRESSURE_VALUE,
            pressure_mn,
        )

    # ------------------------------------------------------------------
    # 标定模式
    # ------------------------------------------------------------------

    def get_mode(self) -> CalibrationMode:
        """
        读取当前标定模式。

        Returns:
            ``CalibrationMode.SINGLE_POINT`` 或 ``CalibrationMode.ALL_POINTS``。
        """
        raw = self._modbus.read_holding_registers(
            self._slave_address, RegisterAddress.CALIBRATION_MODE, 1
        )[0]
        return CalibrationMode(raw)

    def set_mode(self, mode: CalibrationMode) -> None:
        """
        切换标定模式。

        Args:
            mode: ``CalibrationMode.SINGLE_POINT``（100）或
                  ``CalibrationMode.ALL_POINTS``（101）。
        """
        if mode not in (CalibrationMode.SINGLE_POINT, CalibrationMode.ALL_POINTS):
            raise ValidationError(
                f"无效的标定模式：{mode}，须为 SINGLE_POINT(100) 或 ALL_POINTS(101)"
            )
        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.CALIBRATION_MODE, int(mode)
        )

    # ------------------------------------------------------------------
    # 执行标定 / 清除标定
    # ------------------------------------------------------------------

    def calibrate(
        self,
        *,
        use_sample: bool = True,
        ad_value: Optional[int] = None,
    ) -> None:
        """
        执行当前拟合点的标定操作。

        Args:
            use_sample: ``True``（默认）= 写入 65535，设备实时采样并记录 AD 值；
                        ``False`` = 写入 0，使用寄存器中已有的 AD 值。
            ad_value:   若不为 ``None``，直接将此值写入标定控制寄存器，
                        可精确指定拟合点 AD 值（0–65535，65535 等同于 ``use_sample=True``）。

        Example::

            sdk.calibration.calibrate()               # 采样
            sdk.calibration.calibrate(ad_value=1500)  # 手动指定 AD
        """
        if ad_value is not None:
            raw = int(ad_value)
            if not (0 <= raw <= 65535):
                raise ValidationError(f"ad_value 须在 0–65535 范围内，当前值：{raw}")
            value = raw
        else:
            value = CALIBRATION_COMMAND_SAMPLE if use_sample else 0

        self._modbus.write_single_register(
            self._slave_address, RegisterAddress.CALIBRATION, value
        )

    def clear(self) -> None:
        """
        清除所有标定数据，恢复出厂标定。

        Warning:
            此操作不可逆，执行前请确认已备份标定数据。
        """
        self._modbus.write_single_register(
            self._slave_address,
            RegisterAddress.CLEAR_CALIBRATION,
            CLEAR_CALIBRATION_COMMAND,
        )

    # ------------------------------------------------------------------
    # 快照
    # ------------------------------------------------------------------

    def get_status(self) -> CalibrationStatus:
        """
        读取当前标定配置快照（模式、压力点、拟合点编号）。

        Returns:
            ``CalibrationStatus`` 对象（不含拟合点详情，需单独调用
            :meth:`get_all_fitting_points`）。
        """
        return CalibrationStatus(
            mode=self.get_mode(),
            pressure_point=self.get_pressure_point(),
            fitting_point=self.get_fitting_point(),
        )

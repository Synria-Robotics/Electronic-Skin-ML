"""
压力读取 API
============
提供标准读取和高频快速读取两种模式，返回统一的 ``PressureFrame`` 模型
对象或原始列表（高频路径，减少对象分配开销）。
"""

from __future__ import annotations

import time
from typing import List, Optional

from ..models import PressureFrame
from ..protocol.modbus_rtu import ModbusRTU
from .base import BaseAPI


class PressureAPI(BaseAPI):
    """压力数据读取 API。"""

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
            zero_offsets_ref: 共享软件层零点偏移容器（与 ConfigAPI 共享同一个 list）。
        """
        super().__init__(modbus, addr_ref)
        self._zero_offsets_ref = zero_offsets_ref

    @staticmethod
    def _apply_offsets(values: List[int], offsets: List[int]) -> List[int]:
        """将压力值逻点减去将零点偏移，结果截断至 0（不得为负）。"""
        return [max(0, v - o) for v, o in zip(values, offsets)]

    # ------------------------------------------------------------------
    # 标准读取（含完整错误处理）
    # ------------------------------------------------------------------

    def read_all(self) -> PressureFrame:
        """
        读取所有压力点当前值（功能码 0x42）。

        Returns:
            ``PressureFrame``，含各压力点值和采样时间戳。
            若已调用 :meth:`~tactile_sdk.api.config_api.ConfigAPI.trigger_dynamic_zero`，
            返回值为归零后的相对压力。

        Raises:
            CommunicationError: 通信失败。
        """
        ts = time.perf_counter()
        values = self._modbus.read_all_pressure_values(self._slave_address)
        if self._zero_offsets_ref:
            values = self._apply_offsets(values, self._zero_offsets_ref)
        return PressureFrame(values=values, timestamp=ts)

    # ------------------------------------------------------------------
    # 高频快速读取（不抛出异常，适合热循环）
    # ------------------------------------------------------------------

    def read_fast(self) -> Optional[List[int]]:
        """
        高频采集专用快速读取接口。

        - 不抛出异常；失败时返回 ``None``。
        - 适合在确认设备正常工作后，以 100 Hz+ 速率的循环中使用。
        - 返回原始列表以减少对象分配开销，调用方可自行包装为
          ``PressureFrame(values=result)``。
        - 若已调用 :meth:`~tactile_sdk.api.config_api.ConfigAPI.trigger_dynamic_zero`，
          返回值为归零后的相对压力。

        Returns:
            压力值列表；通信失败时返回 ``None``。
        """
        raw = self._modbus.read_all_pressure_values_fast(self._slave_address)
        if raw is None:
            return None
        if self._zero_offsets_ref:
            return self._apply_offsets(raw, self._zero_offsets_ref)
        return raw

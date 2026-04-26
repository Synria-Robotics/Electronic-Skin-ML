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
from .base import BaseAPI


class PressureAPI(BaseAPI):
    """压力数据读取 API。"""

    # ------------------------------------------------------------------
    # 标准读取（含完整错误处理）
    # ------------------------------------------------------------------

    def read_all(self) -> PressureFrame:
        """
        读取所有压力点当前值（功能码 0x42）。

        Returns:
            ``PressureFrame``，含各压力点值和采样时间戳。

        Raises:
            CommunicationError: 通信失败。
        """
        ts = time.perf_counter()
        values = self._modbus.read_all_pressure_values(self._slave_address)
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

        Returns:
            压力值列表；通信失败时返回 ``None``。
        """
        return self._modbus.read_all_pressure_values_fast(self._slave_address)

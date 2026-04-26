"""
tactile_sdk 领域模型层
======================
定义 SDK 对外暴露的数据结构（dataclass），解耦底层字节格式与业务含义，
使调用方得到类型清晰、可直接使用的对象，而非裸字典或元组。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

# CalibrationMode 仅用于类型注解，运行时不需要（from __future__ import annotations
# 使所有注解均为惰性字符串），因此使用 TYPE_CHECKING 避免模型层向下依赖协议层。
if TYPE_CHECKING:
    from .protocol.constants import CalibrationMode


@dataclass
class DeviceInfo:
    """设备身份信息快照。"""

    device_model: str
    """设备型号，例如 "ST-00-01"。"""

    protocol_number: str
    """协议编号，例如 "YF-e0-000001"。"""

    protocol_version: str
    """协议版本，例如 "v1.2"。"""

    app_version: str
    """固件 App 版本，例如 "v1.0.1"。"""

    def __str__(self) -> str:
        return (
            f"DeviceInfo("
            f"model={self.device_model!r}, "
            f"protocol={self.protocol_number} {self.protocol_version}, "
            f"app={self.app_version})"
        )


@dataclass
class FittingPoint:
    """标定拟合点，描述一个 AD 值与对应压力值（mN）的映射关系。"""

    index: int
    """拟合点编号，范围 1–11。"""

    pressure_mn: int
    """该拟合点施加的已知压力，单位：毫牛（mN）。"""

    ad_value: int
    """该拟合点记录的 ADC 原始采样值（0–65535）。"""

    def __str__(self) -> str:
        return f"FittingPoint(idx={self.index}, pressure={self.pressure_mn} mN, ad={self.ad_value})"


@dataclass
class PressureFrame:
    """一帧压力采样结果。"""

    values: List[int]
    """各压力点的压力值列表，长度等于设备压力点总数。"""

    timestamp: Optional[float] = None
    """采样时间戳（`time.perf_counter()` 值），None 表示未记录。"""

    @property
    def point_count(self) -> int:
        """压力点总数。"""
        return len(self.values)

    @property
    def total_pressure(self) -> int:
        """所有压力点之和。"""
        return sum(self.values)

    def __str__(self) -> str:
        ts = f", t={self.timestamp:.3f}s" if self.timestamp is not None else ""
        return f"PressureFrame(points={self.point_count}, total={self.total_pressure} mN{ts})"


@dataclass
class CalibrationStatus:
    """当前标定配置快照。"""

    mode: "CalibrationMode"
    """标定模式：100 = 单点标定，101 = 全部标定。"""

    pressure_point: int
    """当前选定的压力点编号。"""

    fitting_point: int
    """当前选定的拟合点编号（1–11）。"""

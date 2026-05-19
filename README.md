# 玄雅 / Synria 科技 触觉压力采集模块 Python SDK

> 内部开发文档 · 面向 SDK 维护者与集成开发者

基于 Modbus RTU 协议的高性能 Python SDK，支持 60 点触觉压力传感器实时数据采集（实测最高 ~1480 Hz）。

---

## 目录

- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [架构详解](#架构详解)
  - [门面层 client.py](#门面层--clientpy)
  - [API 层 api/](#api-层--api)
  - [协议层 protocol/](#协议层--protocol)
  - [传输层 transport/](#传输层--transport)
  - [横切层 models / exceptions](#横切层--models--exceptions)
- [数据流全链路](#数据流全链路)
- [完整 API 参考](#完整-api-参考)
  - [连接管理](#连接管理)
  - [sdk.device — 设备信息](#sdkdevice--设备信息)
  - [sdk.config — 参数配置](#sdkconfig--参数配置)
  - [sdk.pressure — 压力读取](#sdkpressure--压力读取)
  - [sdk.calibration — 标定操作](#sdkcalibration--标定操作)
- [数据模型](#数据模型)
- [异常体系](#异常体系)
- [协议常量参考](#协议常量参考)
- [示例脚本说明](#示例脚本说明)
- [硬件通信参数](#硬件通信参数)
- [常见问题](#常见问题)

---

## 快速开始

```bash
pip install -r requirements.txt
```

```python
from tactile_sdk import TactilePressureSDK

with TactilePressureSDK("COM6", slave_address=1) as sdk:
    # 读取设备信息
    info = sdk.device.get_info()
    print(info)  # DeviceInfo(model='ST-00-01', ...)

    # 读取一帧压力数据（标准路径，含完整错误处理）
    sdk.config.set_pressure_value_type(1)   # 1=标定值(mN), 0=AD原始值
    frame = sdk.pressure.read_all()
    print(frame.values)         # List[int], 长度=60
    print(frame.total_pressure) # 所有点之和

    # 高频采集路径（不抛异常，失败返回 None）
    values = sdk.pressure.read_fast()
```

---

## 项目结构

```
Electronic-Skin-ML-main/
├── tactile_sdk/                  ← SDK 主包
│   ├── __init__.py               ← 公开接口出口（用户 import 的总入口）
│   ├── client.py                 ← 门面层：TactilePressureSDK
│   ├── exceptions.py             ← 横切层：统一异常类型
│   ├── models.py                 ← 横切层：业务数据模型 (dataclass)
│   │
│   ├── api/                      ← API 层：按业务领域拆分
│   │   ├── __init__.py
│   │   ├── base.py               ← BaseAPI：持有 modbus + 共享地址
│   │   ├── device_api.py         ← DeviceAPI：设备信息读写、地址管理
│   │   ├── config_api.py         ← ConfigAPI：传感器工作参数配置
│   │   ├── pressure_api.py       ← PressureAPI：压力数据读取
│   │   └── calibration_api.py    ← CalibrationAPI：标定工作流
│   │
│   ├── protocol/                 ← 协议层：Modbus RTU 帧构建与解析
│   │   ├── __init__.py
│   │   ├── constants.py          ← 功能码、寄存器地址、枚举常量
│   │   ├── crc16.py              ← CRC16 算法（Modbus 协议规范的一部分）
│   │   └── modbus_rtu.py         ← 帧构建/发送/接收/CRC校验/解析
│   │
│   └── transport/                ← 传输层：串口物理 I/O
│       ├── __init__.py
│       ├── serial_transport.py   ← pyserial 封装，字节级 I/O
│       └── crc16.py              ← 转发模块（向后兼容，实现在 protocol/）
│
├── examples/                     ← 10 个完整示例脚本
├── pyproject.toml                ← 包元数据与构建配置
├── requirements.txt              ← 依赖（仅 pyserial）
└── actual.moduluscali.moduluscali.csv  ← 出厂标定数据备份
```

---

## 架构详解

本 SDK 采用**严格四层架构**，每一层只与相邻层通信，职责单一、互不越界。

```
用户代码
    │
    ▼
┌─────────────────────────────────────┐
│   门面层   TactilePressureSDK       │  client.py
│   sdk.device / .config / .pressure  │
│   / .calibration                    │
└────────────────┬────────────────────┘
                 │ 调用
                 ▼
┌─────────────────────────────────────┐
│   API 层   DeviceAPI / ConfigAPI    │  api/
│            PressureAPI / Calibration│
│            API（继承自 BaseAPI）    │
└────────────────┬────────────────────┘
                 │ 调用
                 ▼
┌─────────────────────────────────────┐
│   协议层   ModbusRTU                │  protocol/
│   帧构建 · 发送接收 · CRC · 解析   │
└────────────────┬────────────────────┘
                 │ 调用
                 ▼
┌─────────────────────────────────────┐
│   传输层   SerialTransport          │  transport/
│   字节级 write / read / flush       │
└─────────────────────────────────────┘

横切层（各层均可引用）：
  exceptions.py  ←  统一异常体系，屏蔽底层 pyserial 异常
  models.py      ←  业务数据结构，解耦字节格式与业务含义
```

---

### 门面层 — `client.py`

**唯一对外入口**，使用 **Facade 模式**把四个领域 API 组合为一个 `TactilePressureSDK` 对象。

`__init__` 中按依赖顺序创建各层实例：

```
SerialTransport(port, baudrate, timeout)
    └─→ ModbusRTU(transport, send_wait_secs)
            ├─→ DeviceAPI(modbus, addr_ref)
            ├─→ ConfigAPI(modbus, addr_ref)
            ├─→ PressureAPI(modbus, addr_ref)
            └─→ CalibrationAPI(modbus, addr_ref)
```

**共享地址容器 `addr_ref`**：四个 API 实例共享同一个单元素列表 `[slave_address]`，`BaseAPI._slave_address` 是操作该列表的 property。因此调用 `sdk.device.set_address(new_addr)` 后，其余三个 API 会**立即同步**，不存在地址不一致问题。

```python
# client.py 内部
self._addr_ref: list = [slave_address]
self.device      = DeviceAPI(self._modbus, self._addr_ref)
self.config      = ConfigAPI(self._modbus, self._addr_ref)
self.pressure    = PressureAPI(self._modbus, self._addr_ref)
self.calibration = CalibrationAPI(self._modbus, self._addr_ref)
```

```python
# base.py 内部
@property
def _slave_address(self) -> int:
    return self._addr_ref[0]   # 读共享容器

@_slave_address.setter
def _slave_address(self, value: int) -> None:
    self._addr_ref[0] = value  # 写共享容器，全局同步
```

---

### API 层 — `api/`

按业务领域分为 4 个类，**只调用 `self._modbus` 的高层方法**，不关心 Modbus 帧结构。

| 类 | 文件 | 核心职责 |
|---|---|---|
| `DeviceAPI` | device_api.py | 读取设备型号/协议版本/固件版本；读写 Modbus 地址 |
| `ConfigAPI` | config_api.py | 压力值类型、采样频率、AD 屏蔽值、点面积、归零控制 |
| `PressureAPI` | pressure_api.py | 标准读取（返回 `PressureFrame`）和高频快速读取 |
| `CalibrationAPI` | calibration_api.py | 拟合点写入、标定模式切换、执行标定、清除标定 |

所有子类继承 `BaseAPI`，共享：
- `self._modbus` — `ModbusRTU` 实例，负责实际通信
- `self._slave_address` — 当前目标从设备地址（通过共享容器保持同步）

---

### 协议层 — `protocol/`

**知道 Modbus RTU 协议格式，不知道业务含义，不知道串口参数。**

#### `modbus_rtu.py` — 核心流程

```
API 层调用高层方法
    │
    ▼
_build_frame(slave, func, data)   → bytes（地址+功能码+数据+CRC）
    │
    ▼
transport.reset_input_buffer()    → 清空接收缓冲区
transport.write(frame)            → 发送帧
    │
    ▼
_read_response() 或 _read_response_fast_0x42()  → 读取响应字节
    │
    ▼
_parse_response(bytes, expected_func)
  ├─ len(response) < 4?         → CommunicationError
  ├─ CRC 不匹配?                → CommunicationError
  ├─ 功能码带 0x80 异常掩码?    → ProtocolError
  └─ 功能码不一致?              → ProtocolError
    │
    ▼
返回数据域 bytes（去掉地址、功能码、CRC）
```

#### 两条读取路径

| 路径 | 方法 | 适用功能码 | 特点 |
|---|---|---|---|
| 标准路径 | `_read_response()` | 0x03 / 0x06 / 0x41 | 发送后等待 `send_wait_secs`（默认 5ms），动态推断帧长 |
| 快速路径 | `_read_response_fast_0x42()` | 0x42（压力读取） | 纯轮询无 sleep，最大化吞吐，实测 ~1480 Hz |

#### `constants.py` — 协议常量

集中管理所有魔法数字，禁止在其他层散落：

- `FunctionCode`：`READ_HOLDING_REGISTERS(0x03)` / `WRITE_SINGLE_REGISTER(0x06)` / `READ_SPECIFIC_INFO(0x41)` / `READ_ALL_PRESSURE_VALUES(0x42)`
- `RegisterAddress`：所有寄存器地址枚举（0x0001–0x0070）
- `CalibrationMode`：`SINGLE_POINT(100)` / `ALL_POINTS(101)`
- `InfoIndex`：0x41 信息索引
- `ExceptionCode`：Modbus 标准异常码
- 边界常量：`MIN_SLAVE_ADDRESS(1)` / `MAX_SLAVE_ADDRESS(247)` / `BROADCAST_ADDRESS(0)` / `DEFAULT_BAUDRATE(4_000_000)` / `DEFAULT_TIMEOUT(1.0)` / `DEFAULT_SEND_WAIT_SECS(0.005)`

#### `crc16.py` — CRC16 算法

CRC16 是 Modbus 协议规范的一部分，因此放在 `protocol/` 而非 `transport/`。

```python
calculate_crc16(data: bytes) -> bytes   # 返回 2 字节小端 CRC
verify_crc16(data: bytes, crc: bytes) -> bool
```

> `transport/crc16.py` 是向后兼容的转发模块，直接 re-export `protocol/crc16`。

---

### 传输层 — `transport/`

**只管字节进出，完全不知道 Modbus 协议。**

`SerialTransport` 是对 pyserial `serial.Serial` 的轻量封装：

| 方法/属性 | 说明 |
|---|---|
| `open()` | 打开串口（已打开时为空操作） |
| `close()` | 关闭串口 |
| `is_open` | 属性，bool |
| `write(data: bytes)` | 发送字节，立即 flush |
| `read(size: int)` | 从缓冲区读取最多 size 字节 |
| `reset_input_buffer()` | 清空接收缓冲区 |
| `in_waiting` | 属性，当前缓冲区可读字节数 |

所有 pyserial 的 `SerialException` 都被转换为 `DeviceConnectionError` 或 `CommunicationError`，不向上层暴露底层依赖。

---

### 横切层 — `models` / `exceptions`

#### `models.py` — 业务数据模型

4 个 `dataclass`，是 API 层与用户代码之间的**数据契约**，使用户拿到类型清晰的对象而非裸字节或裸字典。

> `models.py` 不在运行时依赖任何其他模块（`CalibrationMode` 的导入受 `TYPE_CHECKING` 保护），保持模型层独立。

#### `exceptions.py` — 统一异常体系

```
TactileSdkError（基类）
├── DeviceConnectionError   串口打不开 / 连接意外断开
├── CommunicationError      超时 / CRC 失败 / 帧不完整
├── ProtocolError           功能码异常 / Modbus 异常响应码
├── ValidationError         参数越界（地址/频率/压力值等）
└── CalibrationError        标定操作失败（通常包装上述两种）
```

捕获建议：
- 日常使用：捕获 `TactileSdkError`（一网打尽）
- 精细处理：按子类分别处理（例如区分连接失败和通信失败）
- 高频采集：使用 `read_fast()` — 内部吞掉所有异常，失败返回 `None`

---

## 数据流全链路

以 `sdk.pressure.read_all()` 为例，完整追踪一次调用：

```
1. 用户调用
   sdk.pressure.read_all()

2. PressureAPI（api/pressure_api.py）
   ts = time.perf_counter()
   values = self._modbus.read_all_pressure_values(self._slave_address)
   return PressureFrame(values=values, timestamp=ts)

3. ModbusRTU（protocol/modbus_rtu.py）
   frame = _build_frame(addr, 0x42, b"")    # [addr, 0x42, CRC_lo, CRC_hi]
   transport.reset_input_buffer()
   transport.write(frame)                   # 发送 4 字节请求帧
   response = _read_response_fast_0x42()    # 轮询接收响应
   data_bytes = _parse_response(response, 0x42)
                                            # 验证 CRC + 功能码
   return struct.unpack("<60H", data_bytes[2:])   # 小端解析 60 个 uint16

4. SerialTransport（transport/serial_transport.py）
   serial.Serial.write(frame)
   serial.Serial.flush()
   ...（硬件串口通信）...
   serial.Serial.read(n) → bytes

5. 设备响应帧结构（0x42）
   [addr][0x42][len_lo][len_hi][value0_lo][value0_hi]...[value59_hi][CRC_lo][CRC_hi]
    1B     1B    2B（小端）        60×2=120 字节数据                   2B CRC

6. 返回给用户
   PressureFrame(values=[0,0,512,...], timestamp=12345.678)
```

---

## 完整 API 参考

### 连接管理

```python
sdk = TactilePressureSDK(
    port="COM6",            # 串口名：Windows "COM6"，Linux "/dev/ttyUSB0"
    slave_address=1,        # Modbus 从设备地址（1–247），默认 1
    baudrate=4_000_000,     # 波特率，默认 4,000,000
    timeout=1.0,            # 读超时秒数，默认 1.0
    send_wait_secs=0.005,   # 发送后等待响应开始的延迟，默认 0.005
                            # 低延迟设备可适当减小，提高标准命令速度
)

sdk.connect()           # 打开串口（已打开时为空操作）
sdk.disconnect()        # 关闭串口
sdk.is_connected        # 属性 bool，当前串口是否已打开

# 推荐用上下文管理器（自动 connect / disconnect）
with TactilePressureSDK("COM6") as sdk:
    ...
```

---

### `sdk.device` — 设备信息

#### 读取设备身份信息

```python
info: DeviceInfo = sdk.device.get_info()
# 一次调用读取全部（内部发送 4 次 0x41 请求）
# info.device_model       → "ST-00-01"
# info.protocol_number    → "YF-e0-000001"
# info.protocol_version   → "v1.2"
# info.app_version        → "v1.0.1"

# 也可单独读取
sdk.device.get_model()            # → str
sdk.device.get_protocol_number()  # → str
sdk.device.get_protocol_version() # → str
sdk.device.get_app_version()      # → str
```

#### Modbus 地址管理

```python
sdk.device.get_address() → int
# 从寄存器 0x0001 读取当前 Modbus 地址（1–247）

sdk.device.set_address(new_address: int, *, use_broadcast: bool = True)
# 修改设备 Modbus 地址
# use_broadcast=True（默认）：通过广播地址发送（设备不返回响应）
#     → SDK 内所有 API 实例的地址同步更新
# use_broadcast=False：通过当前地址发送（有响应确认，但修改后设备立即失效）
```

> **注意**：修改地址后设备立即使用新地址，代码中 `slave_address` 同步更新，无需重新创建 SDK 实例。

---

### `sdk.config` — 参数配置

#### 压力值类型

```python
sdk.config.get_pressure_value_type() → int
sdk.config.set_pressure_value_type(value_type: int)
# 0 = ADC 原始值（0–65535）
# 1 = 标定后压力值（mN，需先完成标定）
```

#### AD 屏蔽值

```python
sdk.config.get_ad_mask_value() → int
sdk.config.set_ad_mask_value(mask_value: int)
# 低于此 AD 值的压力点输出 0（视为无压力）
# 用于过滤传感器底噪，范围 0–65535
```

#### 主动上传

```python
sdk.config.get_auto_upload_flag() → bool
sdk.config.set_auto_upload_flag(enable: bool)
# 设备主动周期性上报数据（无需主动轮询）
# 与主动采集（read_fast）二选一使用

sdk.config.get_auto_upload_frequency() → int    # 50–200 Hz
sdk.config.set_auto_upload_frequency(frequency: int)
# 有效范围 50–200 Hz，超出抛 ValidationError
```

#### 压力点信息

```python
sdk.config.get_pressure_point_count() → int   # 只读，典型值 60
sdk.config.get_sensor_point_area()    → float  # 单位 mm²，精度 0.1
sdk.config.set_sensor_point_area(area_mm2: float)
# 范围 0–6553.5 mm²，精度 0.1 mm²
```

#### 归零控制

```python
sdk.config.get_auto_zero_enable() → Optional[bool]
# True=已启用，False=已禁用，None=固件不支持读取该寄存器
sdk.config.set_auto_zero_enable(enable: bool)
# 上电自动归零使能（只写寄存器），重启后生效

sdk.config.trigger_dynamic_zero()
# 立即将当前压力输出归零（建议无负载时调用）

sdk.config.reset_dynamic_zero()
# 撤销动态归零，恢复出厂零点
```

---

### `sdk.pressure` — 压力读取

SDK 提供两条读取路径，根据使用场景选择：

#### 标准路径（含完整错误处理）

```python
frame: PressureFrame = sdk.pressure.read_all()
# 功能码 0x42，快速路径读取，包装为 PressureFrame
# frame.values        → List[int]，长度 = 压力点总数
# frame.timestamp     → float，time.perf_counter() 值
# frame.point_count   → int，压力点数量
# frame.total_pressure→ int，所有点之和（mN）

# 失败时抛出 CommunicationError
```

适用场景：单次读取、调试、需要时间戳、需要明确错误原因。

#### 高频快速路径（热循环专用）

```python
values: Optional[List[int]] = sdk.pressure.read_fast()
# 成功：返回 List[int]
# 失败：返回 None（内部吞掉所有异常，不打断循环）
```

适用场景：100 Hz+ 连续采集循环，实测最高 ~1480 Hz。

```python
# 典型高频采集模式
import time

TARGET_HZ = 200
interval = 1.0 / TARGET_HZ
next_t = time.perf_counter()

with TactilePressureSDK("COM6") as sdk:
    sdk.config.set_pressure_value_type(1)
    while True:
        now = time.perf_counter()
        if now < next_t:
            time.sleep(next_t - now)
        values = sdk.pressure.read_fast()
        if values is not None:
            process(values)   # 你的处理逻辑
        next_t += interval
```

---

### `sdk.calibration` — 标定操作

标定建立 **ADC 原始值 → 实际压力（mN）** 的映射关系，每个压力点支持最多 **11 个拟合点**（分段线性插值）。

#### 标定模式

| `CalibrationMode` | 值 | 说明 |
|---|---|---|
| `SINGLE_POINT` | 100 | 仅标定当前选中的一个压力点 |
| `ALL_POINTS` | 101 | 对所有压力点统一应用同一组拟合曲线 |

```python
from tactile_sdk import CalibrationMode

sdk.calibration.get_mode() → CalibrationMode
sdk.calibration.set_mode(CalibrationMode.ALL_POINTS)
```

#### 拟合点与压力点选择

```python
sdk.calibration.get_fitting_point() → int      # 当前选中的拟合点编号（1–11）
sdk.calibration.set_fitting_point(point: int)  # 选择拟合点，范围 1–11

sdk.calibration.get_pressure_point() → int           # 当前选中的压力点（单点模式用）
sdk.calibration.set_pressure_point(point: int)        # 选择要标定的压力点编号
```

#### 执行标定

```python
sdk.calibration.get_fitting_point_ad() → int         # 读取当前拟合点已记录的 AD 值
sdk.calibration.set_fitting_point_pressure(pressure_mn: int)
# 设置当前拟合点对应的已知压力值（mN），范围 0–65535

sdk.calibration.calibrate(*, use_sample: bool = True, ad_value: Optional[int] = None)
# use_sample=True（默认）：写入 65535，设备实时采样 ADC 并记录
# use_sample=False：        写入 0，使用寄存器中已有的 AD 值
# ad_value=1500：           直接指定具体 AD 值（精确控制，0–65535）
```

#### 查看当前状态

```python
status: CalibrationStatus = sdk.calibration.get_status()
# status.mode            → CalibrationMode
# status.pressure_point  → int
# status.fitting_point   → int
```

#### 清除标定（不可逆）

```python
sdk.calibration.clear()
# 清除所有标定数据，恢复出厂状态
# ⚠️ 清除后如需恢复，运行 06_demo_recover_calibration.py 可由固件还原出厂标定
```

#### 标准标定流程示例

```python
from tactile_sdk import TactilePressureSDK, CalibrationMode

with TactilePressureSDK("COM6") as sdk:

    # —— 全部标定（推荐：对所有 60 个点统一建曲线）——
    sdk.calibration.set_mode(CalibrationMode.ALL_POINTS)

    fitting_plan = [
        (1, 0),     # 拟合点1：施加 0 mN（空载）
        (2, 200),   # 拟合点2：施加 200 mN
        (3, 500),
        (4, 1000),
    ]
    for fitting_point, pressure_mn in fitting_plan:
        sdk.calibration.set_fitting_point(fitting_point)
        sdk.calibration.set_fitting_point_pressure(pressure_mn)
        input(f"请施加 {pressure_mn} mN 后按 Enter 采样...")
        sdk.calibration.calibrate(use_sample=True)
        ad = sdk.calibration.get_fitting_point_ad()
        print(f"拟合点{fitting_point}: {pressure_mn} mN → AD={ad}")

    # —— 单点标定（仅标定压力点 #5）——
    sdk.calibration.set_mode(CalibrationMode.SINGLE_POINT)
    sdk.calibration.set_pressure_point(5)       # 选定压力点 5
    sdk.calibration.set_fitting_point(1)        # 选定拟合点 1
    sdk.calibration.set_fitting_point_pressure(0)
    sdk.calibration.calibrate()                 # 采样

    # —— 手动指定 AD 值（离线/回放标定）——
    sdk.calibration.set_fitting_point(2)
    sdk.calibration.set_fitting_point_pressure(1000)
    sdk.calibration.calibrate(ad_value=2284)    # 直接写入历史 AD 值
```

#### 出厂标定参考数据

存储于 `actual.moduluscali.moduluscali.csv`。出厂标定参数因设备批次/型号而异，如需恢复请运行 `06_demo_recover_calibration.py`，由固件自动还原匹配本设备的出厂参数。

---

## 数据模型

### `DeviceInfo`

```python
@dataclass
class DeviceInfo:
    device_model: str       # 设备型号，如 "ST-00-01"
    protocol_number: str    # 协议编号，如 "YF-e0-000001"
    protocol_version: str   # 协议版本，如 "v1.2"
    app_version: str        # 固件 App 版本，如 "v1.0.1"
```

### `PressureFrame`

```python
@dataclass
class PressureFrame:
    values: List[int]              # 各点压力值，长度 = 压力点总数
    timestamp: Optional[float]     # 采样时刻（time.perf_counter()），可为 None

    # 计算属性
    point_count: int               # len(values)
    total_pressure: int            # sum(values)
```

### `FittingPoint`

```python
@dataclass
class FittingPoint:
    index: int          # 拟合点编号（1–11）
    pressure_mn: int    # 已知压力值（mN）
    ad_value: int       # ADC 原始采样值（0–65535）
```

### `CalibrationStatus`

```python
@dataclass
class CalibrationStatus:
    mode: CalibrationMode   # SINGLE_POINT 或 ALL_POINTS
    pressure_point: int     # 当前选定的压力点编号
    fitting_point: int      # 当前选定的拟合点编号（1–11）
```

---

## 异常体系

```python
from tactile_sdk import (
    TactileSdkError,        # 基类，捕获所有 SDK 异常
    DeviceConnectionError,  # 串口打不开 / 意外断开
    CommunicationError,     # 超时 / CRC 失败 / 帧不完整
    ProtocolError,          # 功能码异常 / Modbus 异常响应码
    ValidationError,        # 参数越界（地址/频率/压力值等）
    CalibrationError,       # 标定操作失败（通常包装上述异常）
)
```

```python
# 推荐的异常处理模式
try:
    sdk.connect()
    frame = sdk.pressure.read_all()
except DeviceConnectionError as e:
    print(f"串口连接失败: {e}")      # 检查串口号、驱动
except CommunicationError as e:
    print(f"通信失败: {e}")          # 检查线缆、地址、波特率
except ProtocolError as e:
    print(f"协议错误: {e}")          # 通常是固件版本不匹配
except ValidationError as e:
    print(f"参数错误: {e}")          # 检查传入参数范围
except TactileSdkError as e:
    print(f"SDK 其他错误: {e}")
finally:
    sdk.disconnect()
```

---

## 协议常量参考

```python
from tactile_sdk.protocol.constants import (
    FunctionCode,
    RegisterAddress,
    CalibrationMode,
    InfoIndex,
    ExceptionCode,
    BROADCAST_ADDRESS,      # 0x00，广播地址，写后设备不回复
    MIN_SLAVE_ADDRESS,      # 1
    MAX_SLAVE_ADDRESS,      # 247
    DEFAULT_BAUDRATE,       # 4_000_000
    DEFAULT_TIMEOUT,        # 1.0 秒
    DEFAULT_SEND_WAIT_SECS, # 0.005 秒
    CALIBRATION_COMMAND_SAMPLE,  # 65535，触发采样
    CLEAR_CALIBRATION_COMMAND,   # 119，清除标定
)
```

### 保持寄存器地址速查

| 寄存器地址 | 枚举名 | 读/写 | 说明 |
|---|---|---|---|
| 0x0001 | `DEVICE_ADDRESS` | 读/写 | Modbus 从设备地址（1–247） |
| 0x000B | `AUTO_UPLOAD_FLAG` | 读/写 | 主动上传使能（0/1） |
| 0x000C | `AUTO_UPLOAD_FREQUENCY` | 读/写 | 主动上传频率（50–200 Hz） |
| 0x000D | `PRESSURE_VALUE_TYPE` | 读/写 | 输出类型（0=AD，1=mN） |
| 0x000E | `AD_MASK_VALUE` | 读/写 | AD 屏蔽阈值 |
| 0x000F | `PRESSURE_POINT_COUNT` | 只读 | 压力点总数（60） |
| 0x0010 | `SENSOR_POINT_AREA` | 读/写 | 单点面积（×0.1 mm²） |
| 0x0011 | `PRESSURE_AUTO_ZERO_ENABLE` | 只写 | 上电自动归零使能 |
| 0x0012 | `PRESSURE_DYNAMIC_ZERO` | 只写 | 1=触发归零，2=重置归零 |
| 0x0064 | `FITTING_POINT` | 读/写 | 当前拟合点编号（1–11） |
| 0x0065 | `FITTING_POINT_AD_VALUE` | 只读 | 当前拟合点 AD 值 |
| 0x0066 | `FITTING_POINT_PRESSURE_VALUE` | 读/写 | 当前拟合点压力值（mN） |
| 0x0067 | `PRESSURE_POINT` | 读/写 | 当前压力点编号（单点标定） |
| 0x0068 | `CALIBRATION_MODE` | 读/写 | 标定模式（100/101） |
| 0x0069 | `CALIBRATION` | 只写 | 标定控制（65535=采样，0=使用已有AD，其他=指定AD） |
| 0x0070 | `CLEAR_CALIBRATION` | 只写 | 写入 119 清除所有标定 |

---

## 示例脚本说明

所有示例位于 `examples/`，**串口号统一设为 `COM6`**，运行前请根据实际情况修改顶部的 `PORT` 变量。  
`SLAVE_ADDRESS` 须与设备拨码开关一致（出厂默认为 `1`）。

```bash
cd examples
python 01_demo_quickstart.py
```

---

### 01_demo_quickstart.py — 快速入门

**适用场景**：初次使用 SDK，验证设备是否正常连接。

**运行方式**：运行后自动打印信息并退出。

```bash
python 01_demo_quickstart.py
```

**输出内容**：
- 设备型号、协议编号/版本、App 固件版本
- 设备 Modbus 地址、压力点总数、主动上传频率
- 压力值类型（标定值 / AD 原始值）、传感器点面积、AD 屏蔽值

---

### 02_demo_calibration.py — 手动输入标定数据

**适用场景**：已通过实验/仪器获得各压力点对应的 AD 值，手动写入设备标定表。

**运行方式**：交互式输入，确认后写入设备。

```bash
python 02_demo_calibration.py
```

**操作流程**：
1. 脚本提示逐行输入标定点，格式为 `压力(mN) AD值`，例如：
   ```
     标定点  1: 0 10
     标定点  2: 100 559
     标定点  3: 500 1729
     标定点  4:          ← 直接回车结束输入
   ```
2. 支持 1–11 个标定点，压力范围 0–1000 mN，AD 值范围 0–65535。
3. 输入完毕后显示汇总表并确认（`y`），脚本以**全部标定模式**写入所有压力点。

**注意**：写入后会覆盖当前标定数据。如需恢复出厂标定，运行 `06_demo_recover_calibration.py`。

---

### 03_demo_configuration.py — 设备参数配置

**适用场景**：调整设备工作参数，或修改 Modbus 地址。

**运行方式**：自动执行读写示例，设备地址修改步骤含交互确认。

```bash
python 03_demo_configuration.py
```

**操作内容**：
1. **读取当前配置**：设备地址、压力值类型、AD 屏蔽值。
2. **设置压力值类型**：`1` = 标定值（mN），`0` = AD 原始值（调试用）。
3. **设置 AD 屏蔽值**：低于此阈值的 AD 采样视为无压力（噪声过滤），示例设为 100。
4. **修改 Modbus 地址**（可选，需手动输入 `y` 确认）：将设备地址改为 1–247 之间的新值，修改后须用新地址重新连接。

---

### 04_demo_read_pressure.py — 高速连续读取

**适用场景**：实时监测压力分布，以固定目标频率持续采样。

**运行方式**：Ctrl+C 停止。

```bash
python 04_demo_read_pressure.py
```

**行为说明**：
- 目标采样率 200 Hz（可修改 `TARGET_HZ`），通过 sleep 精确控制帧间隔。
- 每帧打印长度为 60 的压力值列表。
- 每秒额外输出一行性能统计：
  ```
  >>> 统计: 实际采样率=198.3Hz | 成功=198 | 失败=0 | 错误率=0.00%
  ```

---

### 05_demo_record_pressure.py — 数据记录到 CSV

**适用场景**：采集一段时间的压力数据用于后续分析。

**运行方式**：交互式配置后开始记录，Ctrl+C 可提前停止。

```bash
python 05_demo_record_pressure.py
```

**操作流程**：
1. 选择采样率：10 / 50 / 100 / 200 Hz 或自定义。
2. 输入记录时长（秒），或留空后按 Ctrl+C 手动停止。
3. 输入文件名（默认按时间戳自动生成，如 `pressure_data_20260426_214712.csv`）。
4. 确认配置摘要后开始记录，实时显示已采集帧数和当前总压力。

**CSV 格式**：
```
时间戳, 相对时间(秒), 压力点1, 压力点2, ..., 压力点60
1746000000.123, 0.000, 0, 128, 256, ...
```

---

### 06_demo_recover_calibration.py — 恢复出厂标定

**适用场景**：标定数据被破坏或自定义标定有误，需恢复出厂基线。

**运行方式**：含安全确认提示，确认后执行。

```bash
python 06_demo_recover_calibration.py
```

**行为说明**：
1. 读取恢复**前**各拟合点的 AD 值，供对比。
2. 显示 ⚠️ 警告并等待用户输入 `y` 确认。
3. 向固件发送恢复命令（寄存器 `0x0070` ← 119），由固件自动将 ADC–mN 对应关系还原为出厂烧录参数。
4. 读取恢复**后**各拟合点的 AD 值，显示变更数量。

**优势**：恢复逻辑在固件内完成，Python 无需知道具体参数值，对任何批次/型号的设备均有效。

**注意**：此操作不可逆，运行后将覆盖当前所有自定义标定数据。

---

### 07_demo_test_fps.py — 最大采样率压测

**适用场景**：摸底当前硬件条件（串口芯片、USB 延迟、CPU 负载）下的 FPS 上限。

**运行方式**：Ctrl+C 停止。

```bash
python 07_demo_test_fps.py
```

**行为说明**：
- 以全速无限循环调用 `pressure.read_fast()`，不做任何限速。
- 每秒打印一次性能统计：
  ```
  实际频率: 1480.2 Hz | 点数: 60 | 成功: 1480 | 失败: 0 | 错误率: 0.00%
  ```
- 与 `04_demo_read_pressure.py` 的区别：本脚本不限速（测极限），04 脚本固定目标频率（实际采集用）。

---

### 08_demo_zero_baseline.py — 手动动态归零

**适用场景**：在设备运行中消除当前基线偏移，效果等同于重新插拔。执行前建议确保传感器表面无负载。

**运行方式**：含交互提示。

```bash
python 08_demo_zero_baseline.py
```

**流程**：
1. 打印归零前全部 60 点压力值及总压力
2. 按回车触发 `trigger_dynamic_zero()`：发送硬件命令 → 等待 90ms → 读取 60 点存为软件基线
3. 打印归零后全部 60 点压力值（预期全为 0）
4. 后续所有读取自动逐点减去该基线（`output[i] = max(0, raw[i] - baseline[i])`）

**注意**：软件基线仅在当次 SDK 连接生命周期内有效，断开重连后自动清除。如需撤销归零，运行 `09_demo_baseline_initialization.py`。

---

### 09_demo_baseline_initialization.py — 重置动态归零

**适用场景**：撤销之前的动态归零，将压力值恢复为上电时的硬件零点状态（原始偏移量）。

**运行方式**：直接运行，无交互提示。

```bash
python 09_demo_baseline_initialization.py
```

**流程**：
1. 打印重置前总压力（当前归零后状态）
2. 调用 `reset_dynamic_zero()`：发送硬件命令 + 立即清除 Python 软件基线
3. 打印重置后总压力（已恢复为上电硬件基线的原始偏移量）

**注意**：重置后压力值会恢复到上电时固件自动归零后的硬件基线状态，而非完全原始的 AD 零点。

---

### 10_demo_read_calibration.py — 读取当前标定参数

**适用场景**：查看设备当前存储的 11 个拟合点标定参数，用于验证标定是否正确写入或被意外覆盖。

**运行方式**：直接运行，无交互提示。

```bash
python 10_demo_read_calibration.py
```

**输出内容**：
- `pressure_value_type`：当前输出模式（0 = AD 原始值，1 = 标定值 mN）
- 11 个拟合点各自的 AD 值与对应压力值（mN）

**示例输出**：
```
pressure_value_type = 1  (0=AD 值, 1=标定值 mN)

    点位      AD 值   pressure (mN)
------------------------------------
point  1:  AD =     10,   pressure =      0 mN
point  2:  AD =    559,   pressure =    100 mN
...
point 11:  AD =   2284,   pressure =   1000 mN
```

**注意**：读取的是设备可读写存储区（Flash/EEPROM）里的当前值。运行 `06_demo_recover_calibration.py` 或固件 `clear()` 命令会覆盖这些值；真实出厂标定数据备份在 `actual.moduluscali.moduluscali.csv`。

---

> `examples/sdk/` 目录是旧版单文件 SDK（历史遗留），已被本包替代，**仅保留作参考，不应在新代码中使用**。

---

## 硬件通信参数

| 参数 | 值 |
|------|---|
| 通信协议 | Modbus RTU |
| 波特率 | 4,000,000 bps |
| 数据位 | 8 |
| 校验位 | 无 (None) |
| 停止位 | 1 |
| 从设备地址范围 | 1–247 |
| 广播地址 | 0（写地址时使用，设备不返回响应） |
| 压力点数量 | 60 |
| 压力数据格式 | uint16 × 60，小端序（每帧 120 字节数据域） |
| ADC 分辨率 | 12 位（0–4095）/ 16 位（0–65535）视固件 |
| 实测最大采样率 | ~1480 Hz（read_fast 全速无限制） |
| 推荐采样率 | 100–200 Hz |

---

## 常见问题

**Q：串口拒绝访问（PermissionError / Access Denied）？**
> 其他程序（串口调试助手、另一个 Python 进程）已占用该串口。关闭后重试。

**Q：压力值全为 0？**
> 1. 确认输出类型：`sdk.config.set_pressure_value_type(1)` 切换为标定值模式。
> 2. 检查 AD 屏蔽值：`sdk.config.get_ad_mask_value()` 若过高会过滤小信号。
> 3. 运行 `06_demo_recover_calibration.py` 恢复出厂标定后再测试。

**Q：实际采样率达不到目标？**
> 1. 使用 `sdk.pressure.read_fast()` 而非 `read_all()`。
> 2. 减少循环内的打印、写文件等 I/O 操作（用环形缓冲后处理）。
> 3. 确认波特率为 4,000,000。
> 4. 使用 FTDI 芯片的 USB 转串口适配器（避免 CH340 的延迟问题）。
> 5. 如响应延迟较低，可减小 `send_wait_secs`：`TactilePressureSDK("COM6", send_wait_secs=0.002)`。

**Q：修改设备地址后连不上？**
> `set_address()` 会同步更新 SDK 内部所有 API 实例的地址，无需重新创建实例。若已断开连接，重新连接时传入新地址即可。

**Q：标定后压力仍不准？**
> 先运行 `06_demo_recover_calibration.py` 恢复出厂标定，确认基线准确后再执行自定义标定。

**Q：`get_auto_zero_enable()` 返回 `None`？**
> 该寄存器（0x0011）在部分固件版本中为只写，读取时设备返回 `ILLEGAL_DATA_ADDRESS` 异常码，SDK 捕获后返回 `None`。这是正常行为，不影响 `set_auto_zero_enable()` 的写入功能。

**Q：如何向协议层添加新功能码？**
> 1. 在 `protocol/constants.py` 的 `FunctionCode` 和 `RegisterAddress` 中添加常量。
> 2. 在 `protocol/modbus_rtu.py` 中添加对应的公共方法（参照 `read_holding_registers` 的模式）。
> 3. 在对应的 `api/*.py` 中添加高层业务方法调用协议层新方法。
> 4. 如需对外暴露新数据结构，在 `models.py` 添加 dataclass，并在 `__init__.py` 的 `__all__` 中导出。


---

## 目录

- [主要特性](#主要特性)
- [系统要求](#系统要求)
- [安装](#安装)
- [快速开始](#快速开始)
- [示例脚本](#示例脚本)
- [API 文档](#api-文档)
- [设备与通信参数](#设备与通信参数)
- [常见问题](#常见问题)

---

## 主要特性

- **高速采集**：`read_pressure_fast()` 实测最高 ~1480 Hz，200 Hz 精确控制零失帧
- **完整功能**：设备信息读取、参数配置、传感器标定、归零、数据记录
- **易用接口**：支持上下文管理器（`with` 语句）自动管理连接
- **可靠通信**：Modbus RTU 协议 + CRC16 校验，确保数据完整性
- **跨平台**：支持 Windows、Linux、macOS

---

## 系统要求

- Python 3.7+
- pyserial

---

## 安装

```bash
pip install -r requirements.txt
```

---

## 快速开始

### 1. 确认串口号

| 操作系统 | 串口名称示例 |
|---------|------------|
| Windows | `COM3`、`COM6` 等（设备管理器查看） |
| Linux   | `/dev/ttyUSB0`、`/dev/ttyACM0` |
| macOS   | `/dev/tty.usbserial-*` |

### 2. 连接设备并读取信息

```python
from sdk import TactilePressureSDK

with TactilePressureSDK(port="COM6", slave_address=1) as sdk:
    info = sdk.get_device_info()
    print(f"设备型号: {info['device_model']}")
    print(f"压力点数: {sdk.get_pressure_point_count()}")  # 60
```

### 3. 读取一帧压力数据

```python
with TactilePressureSDK(port="COM6", slave_address=1) as sdk:
    sdk.set_pressure_value_type(1)          # 1=标定值(mN)，0=AD 原始值
    values = sdk.read_pressure_fast()       # 返回长度为 60 的列表，失败返回 None
    print(values)
```

### 4. 以 200 Hz 精确采集

```python
import time
from sdk import TactilePressureSDK

with TactilePressureSDK(port="COM6", slave_address=1) as sdk:
    sdk.set_pressure_value_type(1)
    interval = 1.0 / 200.0
    next_t = time.perf_counter()

    while True:
        now = time.perf_counter()
        if now < next_t:
            time.sleep(next_t - now)
        data = sdk.read_pressure_fast()
        if data is not None:
            print(data)          # 60 个压力点（mN）
        next_t += interval
```

---

## 示例脚本

所有示例位于 `examples/` 目录，**串口号已统一设置为 `COM6`**，请根据实际情况修改。

| 文件名 | 功能简介 |
|--------|--------|
| 01_demo_quickstart.py | 连接设备，读取设备信息和基本配置寄存器 |
| 02_demo_calibration.py | 传感器标定：单点标定、多拟合点全部标定、清除标定 |
| 03_demo_configuration.py | 读取并修改设备配置：压力值类型、AD 屏蔽值、设备地址 |
| 04_demo_read_pressure.py | 以 200 Hz 精确采样，连续打印 60 点压力数组，每秒统计采样率 |
| 05_demo_record_pressure.py | 交互式配置采样率和时长，将压力数据保存为 CSV 文件 |
| 06_demo_recover_calibration.py | 向固件发送恢复命令，由设备自动还原出厂标定参数（兼容任意批次/型号） |
| 07_demo_test_fps.py | 全速压测，测试当前硬件条件下的最大实际采样率（实测 ~1480 Hz） |
| 08_demo_zero_baseline.py | 手动动态归零：触发后将当前 60 点存为软件基线，后续读取自动补偿 |
| 09_demo_baseline_initialization.py | 重置动态归零：清除软件基线，压力值恢复为上电时的硬件零点状态 |

### 运行方式

```bash
cd examples
python 01_demo_quickstart.py
```

> **注意**：04、07 为持续运行脚本，按 `Ctrl+C` 停止；05、08 包含交互式提示。

---

## API 文档

### 连接管理

```python
sdk = TactilePressureSDK(port, slave_address, baudrate=4000000, timeout=1.0)
sdk.connect()       # 连接设备
sdk.disconnect()    # 断开连接
sdk.is_connected()  # 返回 bool
```

### 设备信息

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_device_info()` | dict | 包含型号、协议编号/版本、App 版本 |
| `get_device_model()` | str | 设备型号 |
| `get_protocol_number()` | str | 协议编号 |
| `get_protocol_version()` | str | 协议版本 |
| `get_app_version()` | str | App 版本 |

### 压力值读取

#### `read_pressure_fast()` 推荐

```python
values = sdk.read_pressure_fast()
# 成功：返回 List[int]，长度 = 压力点总数（60）
# 失败：返回 None，不抛异常
```

适用于生产环境和高频采集。

#### `read_all_pressure_values()`

```python
values = sdk.read_all_pressure_values()
# 成功：返回 List[int]
# 失败：抛出 ModbusRTUError
```

适用于开发调试，需要详细错误信息时使用。

### 设备配置

| 方法 | 说明 | 参数 |
|------|------|------|
| `get/set_pressure_value_type(type)` | 压力值输出类型 | 0=AD 原始值，1=标定值（mN） |
| `get/set_ad_mask_value(value)` | AD 屏蔽阈值，低于此值视为无压力 | 0~4095 |
| `get/set_auto_upload_flag(enable)` | 主动上传开关 | True / False |
| `get/set_auto_upload_frequency(freq)` | 主动上传频率 | 50~200 Hz |
| `get/set_sensor_point_area(area)` | 传感器点面积 | 单位：mm² |
| `get_pressure_point_count()` | 压力点总数（只读） | 如 60 |
| `get/set_device_address(addr)` | Modbus 从设备地址 | 1~247（修改需广播） |

### 标定功能

每个压力点支持最多 **11 个拟合点**（索引 1~11）。

#### 标定模式

| 模式值 | 含义 |
|--------|------|
| 100 | 单点标定：只标定当前选中的压力点 |
| 101 | 全部标定：所有压力点应用同一组拟合曲线 |

#### 标定流程示例

```python
# 单点标定：对压力点1的拟合点1标定 1000 mN
sdk.set_calibration_mode(100)
sdk.set_pressure_point(1)
sdk.set_fitting_point(1)
sdk.set_fitting_point_pressure_value(1000)   # 施加已知压力后执行
sdk.calibrate(use_sample=True)               # 采样当前 AD 值并写入
ad = sdk.get_fitting_point_ad_value()        # 读回确认
```

```python
# 全部标定：对所有压力点写入多个拟合点
sdk.set_calibration_mode(101)
for fitting_point, pressure_mN in [(1,0),(2,500),(3,1000),(4,2000)]:
    sdk.set_fitting_point(fitting_point)
    sdk.set_fitting_point_pressure_value(pressure_mN)
    sdk.calibrate(use_sample=True)
```

#### 标定相关方法

| 方法 | 说明 |
|------|------|
| `get/set_calibration_mode(mode)` | 标定模式（100 单点 / 101 全部） |
| `get/set_pressure_point(point)` | 当前操作的压力点编号 |
| `get/set_fitting_point(point)` | 当前操作的拟合点编号（1~11） |
| `set_fitting_point_pressure_value(mN)` | 设置该拟合点对应的压力值 |
| `get_fitting_point_ad_value()` | 读取该拟合点的 AD 值 |
| `calibrate(use_sample, ad_value)` | 执行标定；use_sample=True 使用采样值 |
| `clear_calibration()` | 清除所有标定，恢复出厂状态（不可逆） |

#### 出厂标定参考数据

存储于 `actual.moduluscali.moduluscali.csv`。出厂标定参数因设备批次/型号而异，如需恢复请运行 `06_demo_recover_calibration.py`，由固件自动还原匹配本设备的出厂参数。

### 归零功能

| 方法 | 说明 | 注意 |
|------|------|------|
| `config.trigger_dynamic_zero()` | 触发动态归零；采集 60 点软件基线，后续读取均自动逐点扣减 | 建议无负载时执行；通过 Python 层实现，效果等同重新插拔 |
| `config.reset_dynamic_zero()` | 清除软件基线，恢复为上电硬件零点状态 | 即时生效 |

> 上电自动归零为固件强制行为，每次上电自动执行，无对应 SDK 控制方法。

---

## 设备与通信参数

| 参数 | 值 |
|------|---|
| 通信协议 | Modbus RTU |
| 波特率 | 4,000,000 bps |
| 数据位 | 8 |
| 校验位 | 无 |
| 停止位 | 1 |
| 从设备地址范围 | 1~247 |
| 广播地址 | 0（用于修改设备地址） |
| 压力点数量 | 60 |
| 压力数据类型 | uint16（2字节/点） |
| AD 分辨率 | 12位（0~4095） |
| 实测最大采样率 | ~1480 Hz（全速无限制） |
| 推荐采样率 | 100~200 Hz |

---

## 常见问题

**Q：串口拒绝访问（PermissionError）？**
> 其他程序已占用该串口。关闭串口调试工具或其他 Python 脚本后重试。

**Q：压力值全为 0？**
> 1. 确认压力值类型：`set_pressure_value_type(1)` 切换为标定值模式。
> 2. 检查 AD 屏蔽值 `get_ad_mask_value()`，过高会过滤小压力信号。
> 3. 运行 `06_demo_recover_calibration.py` 恢复出厂标定后重试。

**Q：实际采样率达不到目标？**
> 1. 使用 `read_pressure_fast()` 而非 `read_all_pressure_values()`。
> 2. 减少循环内的打印、写文件等耗时操作。
> 3. 确认波特率为 4,000,000。
> 4. 使用高性能 USB 转串口适配器（推荐 FTDI 芯片）。

**Q：修改设备地址后连不上？**
> 将代码中 `slave_address` 改为新地址后重新连接，原地址立即失效。

**Q：标定后压力仍不准？**
> 先运行 `06_demo_recover_calibration.py` 恢复出厂标定，再重新执行自定义标定流程。
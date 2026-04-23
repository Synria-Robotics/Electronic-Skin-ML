# 玄雅/Synria科技 触觉压力采集模块 Python SDK

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

基于 Modbus RTU 协议的高性能 Python SDK，支持 60 点触觉压力传感器的实时数据采集（实测最高 ~1480 Hz）。

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
| 06_demo_recover_calibration.py | 一键写入出厂标定数据，恢复标定到初始状态 |
| 07_demo_test_fps.py | 全速压测，测试当前硬件条件下的最大实际采样率（实测 ~1480 Hz） |
| 08_demo_zero_calibration.py | 上电自动归零、手动动态归零、重置归零三种归零演示 |

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

存储于 `actual.moduluscali.moduluscali.csv` 及 `examples/06_demo_recover_calibration.py`。

| 拟合点 | 压力 (mN) | AD 值 |
|--------|----------|-------|
| 1 | 0 | 10 |
| 2 | 100 | 559 |
| 3 | 200 | 998 |
| 4 | 300 | 1319 |
| 5 | 400 | 1554 |
| 6 | 500 | 1729 |
| 7 | 600 | 1871 |
| 8 | 700 | 1999 |
| 9 | 800 | 2113 |
| 10 | 900 | 2211 |
| 11 | 1000 | 2284 |

### 归零功能

| 方法 | 说明 | 注意 |
|------|------|------|
| `set_pressure_auto_zero_enable(True/False)` | 上电自动归零开关 | 只写寄存器，重启后生效 |
| `trigger_pressure_dynamic_zero()` | 立即将当前压力值归零 | 只写，建议无负载时执行 |
| `reset_pressure_dynamic_zero()` | 撤销动态归零，恢复出厂零点 | 只写 |

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
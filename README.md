# 玄雅/Synria科技触觉压力采集模块 Python SDK

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

基于Modbus RTU协议的高性能Python SDK，支持高速数据采集（100-200Hz+）。

## 主要特性

- ✅ **高速数据采集**：支持100-200Hz+的压力数据读取
- ✅ **易用接口**：简洁的API设计，支持上下文管理器
- ✅ **完整功能**：设备配置、标定、压力读取等全功能支持
- ✅ **性能优化**：专门优化的快速读取接口，减少延迟
- ✅ **可靠通信**：基于Modbus RTU协议，CRC校验确保数据完整性
- ✅ **跨平台**：支持Windows、Linux、macOS

## 系统要求

- Python 3.7 或更高版本
- pyserial 库

## 安装

### 安装依赖

```bash
pip install pyserial
```

或使用requirements.txt：

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 基本使用

```python
from sdk import TactilePressureSDK

# 创建SDK实例并连接设备
sdk = TactilePressureSDK(port="COM3", slave_address=1)
sdk.connect()

try:
    # 读取设备信息
    info = sdk.get_device_info()
    print(f"设备型号: {info['device_model']}")
    print(f"协议版本: {info['protocol_version']}")
    
    # 读取所有压力值
    pressure_values = sdk.read_all_pressure_values()
    print(f"压力值: {pressure_values}")
    print(f"总压力: {sum(pressure_values)}")
    
finally:
    # 断开连接
    sdk.disconnect()
```

### 2. 使用上下文管理器（推荐）

```python
from sdk import TactilePressureSDK

with TactilePressureSDK(port="COM3", slave_address=1) as sdk:
    # 获取设备信息
    info = sdk.get_device_info()
    print(info)
    
    # 读取压力值
    pressure_values = sdk.read_all_pressure_values()
    print(f"读取到 {len(pressure_values)} 个压力点")
```

### 3. 高速数据采集（100Hz+）

```python
import time
from sdk import TactilePressureSDK

with TactilePressureSDK(port="COM3", slave_address=1) as sdk:
    # 设置为标定值模式
    sdk.set_pressure_value_type(1)
    
    frame_count = 0
    last_time = time.perf_counter()
    
    while True:
        # 使用优化的快速读取接口
        pressure_values = sdk.read_pressure_fast()
        
        if pressure_values is not None:
            frame_count += 1
            # 处理压力数据...
        
        # 每秒统计一次采样率
        current_time = time.perf_counter()
        if current_time - last_time >= 1.0:
            fps = frame_count / (current_time - last_time)
            print(f"采样率: {fps:.1f} Hz, 数据点: {len(pressure_values)}")
            frame_count = 0
            last_time = current_time
```

### 4. 200Hz高速采集并打印数据

```python
import time
from sdk import TactilePressureSDK

with TactilePressureSDK(port="COM3", slave_address=1) as sdk:
    sdk.set_pressure_value_type(1)  # 设置为标定值
    
    # 200Hz = 5ms间隔
    target_interval = 1.0 / 200.0
    next_read_time = time.perf_counter()
    
    while True:
        # 精确时间控制
        current_time = time.perf_counter()
        if current_time < next_read_time:
            time.sleep(next_read_time - current_time)
        
        # 快速读取压力值
        pressure_values = sdk.read_pressure_fast()
        if pressure_values is not None:
            print(pressure_values)  # 打印60个压力点的数组
        
        next_read_time += target_interval
```

### 5. 压力数据记录并保存为CSV

```python
import time
import csv
from datetime import datetime
from sdk import TactilePressureSDK

with TactilePressureSDK(port="COM3", slave_address=1) as sdk:
    sdk.set_pressure_value_type(1)  # 设置为标定值
    
    # 配置参数
    sampling_rate = 50  # 采样率 50Hz
    duration = 10  # 记录10秒
    filename = f"pressure_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 创建CSV文件
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # 写入表头
        point_count = sdk.get_pressure_point_count()
        header = ['时间戳', '相对时间(秒)'] + [f'压力点{i+1}' for i in range(point_count)]
        csv_writer.writerow(header)
        
        # 开始记录
        start_time = time.perf_counter()
        interval = 1.0 / sampling_rate
        next_sample_time = start_time
        
        while time.perf_counter() - start_time < duration:
            # 时间控制
            current_time = time.perf_counter()
            if current_time < next_sample_time:
                time.sleep(next_sample_time - current_time)
            
            # 读取并保存数据
            pressure_values = sdk.read_pressure_fast()
            if pressure_values:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                relative_time = time.perf_counter() - start_time
                row = [timestamp, f'{relative_time:.3f}'] + pressure_values
                csv_writer.writerow(row)
            
            next_sample_time += interval
    
    print(f"数据已保存到: {filename}")
```

## 示例代码

SDK提供了多个完整的示例脚本，位于 `examples/` 目录：

| 示例文件 | 说明 | 适用场景 |
|---------|------|----------|
| **example_basic.py** | 基础操作示例 | 设备连接和信息读取 |
| **example_read_pressure.py** | **200Hz高速读取示例** | **高频数据采集（推荐）** |
| **example_record_pressure.py** | 压力数据记录示例 | 数据记录和CSV导出 |
| **example_configuration.py** | 设备配置示例 | 修改设备参数 |
| **example_zero_calibration.py** | 归零功能示例 | 压力归零和零点设定 |
| **example_calibration.py** | 标定功能示例 | 传感器标定（谨慎使用） |
| **example_recover_calibration.py** | 恢复标定数据 | 恢复出厂或备份标定 |
| **example_test_fps.py** | 测试脚本 | 性能测试和调试 |

### 运行示例

```bash
# 基础操作
python examples/example_basic.py

# 200Hz高速读取（推荐）
python examples/example_read_pressure.py

# 压力数据记录（保存为CSV）
python examples/example_record_pressure.py

# 设备配置
python examples/example_configuration.py

# 归零功能
python examples/example_zero_calibration.py
```

## API文档

### 连接管理

```python
sdk = TactilePressureSDK(port, slave_address, baudrate=4000000, timeout=1.0)
sdk.connect()        # 连接设备
sdk.disconnect()     # 断开连接
sdk.is_connected()   # 检查连接状态
```

### 设备信息读取

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `get_device_model()` | str | 设备型号（如"ST-00-01"） |
| `get_protocol_number()` | str | 协议编号（如"YF-e0-000001"） |
| `get_protocol_version()` | str | 协议版本（如"v1.0"） |
| `get_app_version()` | str | App版本（如"v1.0.1"） |
| `get_device_info()` | dict | 获取所有设备信息的字典 |

### 压力值读取（核心功能）

#### 方法1：普通读取（带异常处理）

```python
pressure_values = sdk.read_all_pressure_values()
```

- 返回：`List[int]` - 压力值列表
- 异常：通信失败时抛出 `ModbusRTUError`
- 适用：开发调试阶段，需要完整错误提示

#### 方法2：快速读取（推荐用于高频采集）⚡

```python
pressure_values = sdk.read_pressure_fast()
```

- 返回：`Optional[List[int]]` - 成功返回压力值列表，失败返回None
- 异常：不抛出异常
- 性能：可达100-200Hz+
- 适用：**生产环境、高频数据采集（推荐）**



### 设备配置

#### 基本配置

| 方法 | 说明 | 参数范围 |
|------|------|----------|
| `get_device_address()` / `set_device_address(addr)` | 设备地址 | 1-247 |
| `get_pressure_value_type()` / `set_pressure_value_type(type)` | 压力值类型 | 0=AD值, 1=标定值(mN) |
| `get_pressure_point_count()` | 压力点总数 | 只读，如60 |
| `get_sensor_point_area()` / `set_sensor_point_area(area)` | 传感器点面积 | 单位：平方毫米 |

#### 高级配置

| 方法 | 说明 | 参数范围 |
|------|------|----------|
| `get_auto_upload_flag()` / `set_auto_upload_flag(enable)` | 主动上传开关 | True/False |
| `get_auto_upload_frequency()` / `set_auto_upload_frequency(freq)` | 主动上传频率 | 50-200 Hz |
| `get_ad_mask_value()` / `set_ad_mask_value(value)` | AD屏蔽值 | 0-4095 |
| `set_pressure_auto_zero_enable(enable)` | 上电自动归零 | True/False（⚠️ 只写） |
| `trigger_pressure_dynamic_zero()` | 触发动态归零 | 无参数（⚠️ 只写） |
| `reset_pressure_dynamic_zero()` | 重置动态归零 | 无参数（⚠️ 只写） |

### 标定功能

#### 标定流程

```python
# 1. 选择拟合点（1-11）
sdk.set_fitting_point(1)

# 2. 设置该点的压力值（单位：mN，毫牛）
sdk.set_fitting_point_pressure_value(1000)  # 1000mN

# 3. 执行标定（采样当前AD值）
sdk.calibrate(use_sample=True)

# 4. 重复步骤1-3，设置其他拟合点...
```

#### 标定相关方法

| 方法 | 说明 |
|------|------|
| `get_fitting_point()` / `set_fitting_point(point)` | 当前拟合点（1-11） |
| `get_fitting_point_ad_value()` | 读取拟合点AD值（原始ADC采样值） |
| `get_fitting_point_pressure_value()` / `set_fitting_point_pressure_value(pressure)` | 拟合点压力值（单位：mN，毫牛） |
| `get_calibration_mode()` / `set_calibration_mode(mode)` | 标定模式（100=单点，101=全部） |
| `calibrate(use_sample=True, ad_value=None)` | 执行标定 |
| `clear_calibration()` | ⚠️ 清除标定（恢复出厂设置） |

#### 批量操作标定点

```python
# 读取所有7个拟合点
points = sdk.get_all_fitting_points()
# 返回格式: [{"index": 1, "pressure": 0, "ad": 10}, ...]

# 写入所有7个拟合点
points = [
    {"pressure": 0, "ad": 10},
    {"pressure": 1000, "ad": 559},
    {"pressure": 2000, "ad": 998},
    # ... 共7个点
]
sdk.set_all_fitting_points(points)
```

### 归零功能

#### 上电自动归零

```python
# 启用上电自动归零（设备每次上电时自动归零）
sdk.set_pressure_auto_zero_enable(True)

# 禁用上电自动归零
sdk.set_pressure_auto_zero_enable(False)
```

**⚠️ 注意**：该寄存器(0x0011)为只写寄存器，设备不支持读取当前状态。设置后需要重启设备才能观察效果。

#### 手动动态归零

```python
# 触发一次动态归零（立即将当前压力值归零）
sdk.trigger_pressure_dynamic_zero()

# 重置动态归零（恢复到出厂归零状态）
sdk.reset_pressure_dynamic_zero()

# 完整示例：归零前后对比
pressure_before = sdk.read_all_pressure_values()
print(f"归零前总压力: {sum(pressure_before)} mN")

sdk.trigger_pressure_dynamic_zero()
time.sleep(0.5)  # 等待归零完成

pressure_after = sdk.read_all_pressure_values()
print(f"归零后总压力: {sum(pressure_after)} mN")
```

## 设备信息

### 通信协议参数

| 参数 | 值 | 说明 |
|------|---|------|
| **通信协议** | Modbus RTU | 标准工业协议 |
| **波特率** | 4000000 bps | 默认值，可修改 |
| **数据位** | 8 | 固定 |
| **校验位** | None | 无校验 |
| **停止位** | 1 | 固定 |
| **从设备地址** | 1-247 | 可配置 |
| **广播地址** | 0 | 用于批量配置 |

### 玄雅/Synria科技电子皮肤传感器布局

**60个压力点分布**（从上到下，从左到右）：

```
行布局：
- 1: 2列 × 2行 = 4个点
- 2：4列 × 6行 = 24个点
- 3：6列 × 2行 = 12个点
- 4：8列 × 2行 = 16个点
- 底部：左右各2个 = 4个点

总计：60个压力点
```

**数据格式**：
- 每个压力点：2字节（uint16）
- 数据类型：
  - **AD值（type=0）**：原始ADC采样值（0-4095，12位ADC）
  - **标定值（type=1）**：经过标定后的压力值（单位：mN，毫牛）
- 数组索引：0-59

### 串口名称格式

| 操作系统 | 串口名称示例 |
|---------|-------------|
| **Windows** | `COM3`, `COM4`, `COM7` 等 |
| **Linux** | `/dev/ttyUSB0`, `/dev/ttyACM0` 等 |
| **macOS** | `/dev/tty.usbserial-*`, `/dev/tty.usbmodem*` |

## 注意事项与最佳实践

### ⚠️ 重要注意事项

1. **修改设备地址**：必须使用广播地址（0）发送命令
2. **清除标定**：会恢复出厂设置，请备份标定数据后谨慎操作
3. **只写寄存器限制**：
   - **压强上电归零寄存器（0x0011）**：只写不读，无法查询当前状态
   - **压强动态归零寄存器（0x0012）**：只写不读，写入即触发归零

### 💡 最佳实践

1. **高频采集**：使用 `read_pressure_fast()` 方法
2. **错误处理**：生产环境检查返回值是否为None
3. **连接管理**：使用 `with` 语句自动管理连接
4. **性能优化**：
   - 设置合适的串口超时时间
   - 避免频繁配置寄存器
   - 高频读取时不要每次都查询设备信息
5. **数据采集**：
   - 开发调试：使用 `read_all_pressure_values()`
   - 生产部署：使用 `read_pressure_fast()`

## 性能优化说明

### 高性能设计

本SDK针对高频压力数据采集进行了深度优化，支持稳定的100-200Hz+采样率。

### 优化技术

#### 1. 双模式读取接口

| 特性 | `read_all_pressure_values()` | `read_pressure_fast()` ⚡ |
|------|------------------------------|---------------------------|
| **性能** | 50-80Hz | 100-200Hz+ |
| **异常处理** | 抛出异常 | 返回None |
| **错误信息** | 详细 | 无 |
| **适用场景** | 开发调试 | 生产环境/高频采集 |

#### 2. 底层通信优化

```
优化前：发送请求 → 延时10ms → 读取响应 → 解析（循环）
优化后：发送请求 → 非阻塞读取 → 批量解析（struct.unpack）
```

**具体优化措施**：
- ✅ 移除固定延时，使用非阻塞I/O
- ✅ 使用 `struct.unpack` 批量解析数据（快5-10倍）
- ✅ 减少函数调用层次
- ✅ 优化串口缓冲区管理
- ✅ 使用 `time.perf_counter()` 高精度计时



### 性能优化示例

#### 示例1：最高速度采集

```python
# 不限速，获得最高采样率
with TactilePressureSDK(port="COM3", slave_address=1) as sdk:
    while True:
        data = sdk.read_pressure_fast()
        if data:
            process(data)  # 处理数据
```

#### 示例2：精确控制采样率（推荐）

```python
# 精确控制为200Hz
import time

with TactilePressureSDK(port="COM3", slave_address=1) as sdk:
    interval = 1.0 / 200.0  # 5ms
    next_time = time.perf_counter()
    
    while True:
        if time.perf_counter() < next_time:
            time.sleep(next_time - time.perf_counter())
        
        data = sdk.read_pressure_fast()
        if data:
            print(data)
        
        next_time += interval
```


### 性能调优建议

1. **选择合适的采样率**：根据应用需求，不要盲目追求高采样率
2. **使用时间控制**：精确控制采样间隔，避免CPU空转
3. **批量处理数据**：累积多帧数据后批量处理，提高效率
4. **减少打印输出**：频繁打印会降低性能，仅在必要时输出
5. **检查硬件性能**：确保USB串口适配器支持高速通信

## 常见问题解答（FAQ）

### Q1: 如何选择合适的采样率？

**A:** 根据应用需求选择：
- **触摸检测**：50-100Hz 足够
- **动态压力监测**：100-150Hz
- **高速响应应用**：150-200Hz
- **数据记录**：根据需求，通常50-100Hz

### Q2: 为什么实际采样率达不到目标值？

**A:** 可能的原因：
1. **硬件限制**：USB转串口芯片性能不足
2. **系统负载**：CPU占用过高
3. **代码延迟**：数据处理逻辑耗时过长
4. **波特率设置**：波特率过低

**解决方案**：
- 使用 `read_pressure_fast()` 接口
- 减少数据处理逻辑
- 使用高性能USB转串口适配器（推荐FTDI芯片）
- 确保波特率设置为4000000

### Q3: 读取的压力值为0是否正常？

**A:** 可能正常，取决于情况：
- 未触摸传感器时，压力值应该接近0
- 检查是否设置了AD屏蔽值
- 检查压力值类型（AD值 vs 标定值）
- 检查是否需要重新标定

### Q4: 如何备份和恢复标定数据？

**A:** 使用提供的方法：

```python
# 备份标定数据
points = sdk.get_all_fitting_points()
import json
with open('calibration_backup.json', 'w') as f:
    json.dump(points, f)

# 恢复标定数据
with open('calibration_backup.json', 'r') as f:
    points = json.load(f)
sdk.set_all_fitting_points(points)
```

### Q5: 多个设备如何同时使用？

**A:** 两种方式：
1. **不同串口**：为每个设备创建独立的SDK实例
2. **同一串口**：设置不同的从设备地址（1-247）

```python
# 方式1：不同串口
sdk1 = TactilePressureSDK(port="COM3", slave_address=1)
sdk2 = TactilePressureSDK(port="COM4", slave_address=1)

# 方式2：同一串口，不同地址
sdk1 = TactilePressureSDK(port="COM3", slave_address=1)
sdk2 = TactilePressureSDK(port="COM3", slave_address=2)
```

### Q6: 串口被占用无法打开怎么办？

**A:** 
1. 检查是否有其他程序占用串口
2. 关闭其他可能使用串口的应用（如串口调试工具）
3. 断开并重新连接USB设备
4. 重启电脑（Windows有时会锁定串口）

### Q7: 如何调试通信问题？

**A:** 开启调试模式：

```python
# 在 modbus_rtu.py 中取消注释调试代码（第178行附近）
# hex_str = response.hex(' ').upper()
# print("接收数据（16进制）：", hex_str)
```

## 故障排除

### 问题：设备连接失败

**症状**：`ModbusRTUError: 无法打开串口`

**解决步骤**：
1. ✅ 检查串口名称是否正确
2. ✅ 检查设备是否已接入
3. ✅ 检查USB驱动是否安装
4. ✅ 在设备管理器中查看串口号
5. ✅ 尝试其他串口或USB端口

### 问题：通信超时

**症状**：`ModbusRTUError: 未收到响应或响应超时`

**解决步骤**：
1. ✅ 检查波特率设置是否正确（默认4000000）
2. ✅ 检查从设备地址是否正确
3. ✅ 增加超时时间：`TactilePressureSDK(port, address, timeout=2.0)`
4. ✅ 检查USB线缆质量
5. ✅ 更换USB端口或使用USB Hub

### 问题：CRC校验失败

**症状**：`ModbusRTUError: CRC校验失败`

**解决步骤**：
1. ✅ 检查串口线缆连接
2. ✅ 降低波特率测试
3. ✅ 检查电磁干扰
4. ✅ 更换USB线缆
5. ✅ 联系技术支持

### 问题：采样率不稳定

**症状**：采样率波动大，时高时低

**解决步骤**：
1. ✅ 使用 `time.perf_counter()` 进行精确计时
2. ✅ 减少数据处理逻辑
3. ✅ 使用 `read_pressure_fast()` 接口
4. ✅ 关闭不必要的后台程序





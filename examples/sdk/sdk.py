"""
玄雅/Synria科技触觉压力采集模块 SDK 主接口
"""

from typing import Optional, List
from .modbus_rtu import ModbusRTU, ModbusRTUError
from .constants import (
    RegisterAddress,
    InfoIndex,
    CALIBRATION_MODE_SINGLE_POINT,
    CALIBRATION_MODE_ALL_POINTS,
    CALIBRATION_COMMAND_SAMPLE,
    CLEAR_CALIBRATION_COMMAND,
    MIN_SLAVE_ADDRESS,
    MAX_SLAVE_ADDRESS,
)


class TactilePressureSDK:
    """
    玄雅/Synria科技触觉压力采集模块 SDK
    
    提供高级接口用于与触觉压力采集模块进行通信
    """
    
    def __init__(self, port: str, slave_address: int = 1, 
                 baudrate: int = 4000000, timeout: float = 1.0):
        """
        初始化SDK
        
        Args:
            port: 串口名称（如 'COM3' 或 '/dev/ttyUSB0'）
            slave_address: 从设备地址（1-247），默认1
            baudrate: 波特率，默认4000000
            timeout: 超时时间（秒），默认1.0
        """
        if not (MIN_SLAVE_ADDRESS <= slave_address <= MAX_SLAVE_ADDRESS):
            raise ValueError(f"从设备地址必须在{MIN_SLAVE_ADDRESS}-{MAX_SLAVE_ADDRESS}之间")
        
        self.slave_address = slave_address
        self.modbus = ModbusRTU(port, baudrate, timeout)
    
    def connect(self) -> None:
        """
        连接到设备
        """
        self.modbus.connect()
    
    def disconnect(self) -> None:
        """
        断开设备连接
        """
        self.modbus.disconnect()
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            True表示已连接，False表示未连接
        """
        return self.modbus.is_connected()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
    
    # ========== 设备信息读取 ==========
    
    def get_device_model(self) -> str:
        """
        获取设备型号
        
        Returns:
            设备型号字符串（如 "ST-00-01"）
        """
        return self.modbus.read_specific_info(self.slave_address, InfoIndex.DEVICE_MODEL)
    
    def get_protocol_number(self) -> str:
        """
        获取协议编号
        
        Returns:
            协议编号字符串（如 "YF-e0-000001"）
        """
        return self.modbus.read_specific_info(self.slave_address, InfoIndex.PROTOCOL_NUMBER)
    
    def get_protocol_version(self) -> str:
        """
        获取协议版本
        
        Returns:
            协议版本字符串（如 "v1.0"）
        """
        return self.modbus.read_specific_info(self.slave_address, InfoIndex.PROTOCOL_VERSION)
    
    def get_app_version(self) -> str:
        """
        获取App版本
        
        Returns:
            App版本字符串（如 "v1.0.1"）
        """
        return self.modbus.read_specific_info(self.slave_address, InfoIndex.APP_VERSION)
    
    def get_device_info(self) -> dict:
        """
        获取所有设备信息
        
        Returns:
            包含所有设备信息的字典
        """
        return {
            "device_model": self.get_device_model(),
            "protocol_number": self.get_protocol_number(),
            "protocol_version": self.get_protocol_version(),
            "app_version": self.get_app_version(),
        }
    
    # ========== 寄存器读写操作 ==========
    
    def get_device_address(self) -> int:
        """
        获取设备地址
        
        Returns:
            设备地址（1-247）
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.DEVICE_ADDRESS, 1
        )
        return values[0]
    
    def set_device_address(self, address: int, use_broadcast: bool = True) -> None:
        """
        设置设备地址
        
        Args:
            address: 新地址（1-247）
            use_broadcast: 是否使用广播地址发送（默认True）
            
        Note:
            如果use_broadcast=True，将使用广播地址(0)发送命令，设备不会返回响应
        """
        if not (MIN_SLAVE_ADDRESS <= address <= MAX_SLAVE_ADDRESS):
            raise ValueError(f"设备地址必须在{MIN_SLAVE_ADDRESS}-{MAX_SLAVE_ADDRESS}之间")
        
        target_address = 0 if use_broadcast else self.slave_address
        self.modbus.write_single_register(
            target_address, RegisterAddress.DEVICE_ADDRESS, address
        )
        if use_broadcast:
            self.slave_address = address
    
    def get_auto_upload_flag(self) -> bool:
        """
        获取主动上传标志
        
        Returns:
            True表示开启上传，False表示关闭上传
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.AUTO_UPLOAD_FLAG, 1
        )
        return values[0] == 1
    
    def set_auto_upload_flag(self, enable: bool) -> None:
        """
        设置主动上传标志
        
        Args:
            enable: True表示开启上传，False表示关闭上传
        """
        value = 1 if enable else 0
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.AUTO_UPLOAD_FLAG, value
        )
    
    def get_auto_upload_frequency(self) -> int:
        """
        获取主动上传频率
        
        Returns:
            上传频率（50-200 Hz）
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.AUTO_UPLOAD_FREQUENCY, 1
        )
        return values[0]
    
    def set_auto_upload_frequency(self, frequency: int) -> None:
        """
        设置主动上传频率
        
        Args:
            frequency: 上传频率（50-200 Hz）
        """
        if not (50 <= frequency <= 200):
            raise ValueError("上传频率必须在50-200 Hz之间")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.AUTO_UPLOAD_FREQUENCY, frequency
        )
    
    def get_pressure_value_type(self) -> int:
        """
        获取压力值类型
        
        Returns:
            0表示AD值，1表示标定值
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.PRESSURE_VALUE_TYPE, 1
        )
        return values[0]
    
    def set_pressure_value_type(self, value_type: int) -> None:
        """
        设置压力值类型
        
        Args:
            value_type: 0表示AD值，1表示标定值
        """
        if value_type not in [0, 1]:
            raise ValueError("压力值类型必须是0（AD值）或1（标定值）")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.PRESSURE_VALUE_TYPE, value_type
        )
    
    def get_ad_mask_value(self) -> int:
        """
        获取AD屏蔽值
        
        Returns:
            AD屏蔽值（0-AD_Max）
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.AD_MASK_VALUE, 1
        )
        return values[0]
    
    def set_ad_mask_value(self, mask_value: int) -> None:
        """
        设置AD屏蔽值
        
        Args:
            mask_value: AD屏蔽值（0-AD_Max，如12位AD则最大4095）
        """
        if mask_value < 0:
            raise ValueError("AD屏蔽值不能为负数")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.AD_MASK_VALUE, mask_value
        )
    
    def get_pressure_point_count(self) -> int:
        """
        获取压力点总数
        
        Returns:
            压力点总数
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.PRESSURE_POINT_COUNT, 1
        )
        return values[0]
    
    def get_sensor_point_area(self) -> float:
        """
        获取传感器单个点面积
        
        Returns:
            面积值（单位：0.1平方毫米）
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.SENSOR_POINT_AREA, 1
        )
        return values[0] * 0.1  # 转换为平方毫米
    
    def set_sensor_point_area(self, area_mm2: float) -> None:
        """
        设置传感器单个点面积
        
        Args:
            area_mm2: 面积值（单位：平方毫米）
        """
        value = int(area_mm2 / 0.1)  # 转换为0.1平方毫米单位
        if value < 0 or value > 65535:
            raise ValueError("面积值超出范围")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.SENSOR_POINT_AREA, value
        )
    
    def get_pressure_auto_zero_enable(self) -> bool:
        """
        获取压强值上电自动归零使能标志
        
        Returns:
            True表示开启，False表示关闭
            
        Raises:
            ModbusRTUError: 如果通信失败或寄存器不支持读取
        """
        try:
            values = self.modbus.read_holding_registers(
                self.slave_address, RegisterAddress.PRESSURE_AUTO_ZERO_ENABLE, 1
            )
            return values[0] == 1
        except ModbusRTUError as e:
            if "ILLEGAL_DATA_ADDRESS" in str(e):
                raise ModbusRTUError(
                    "设备不支持读取自动归零使能寄存器（寄存器地址0x0011）。"
                    "该设备可能仅支持写入该寄存器，不支持读取。"
                ) from e
            raise
    
    def try_get_pressure_auto_zero_enable(self) -> Optional[bool]:
        """
        尝试获取压强值上电自动归零使能标志（如果寄存器不支持读取则返回None）
        
        Returns:
            True表示开启，False表示关闭，None表示寄存器不支持读取
        """
        try:
            return self.get_pressure_auto_zero_enable()
        except ModbusRTUError as e:
            if "不支持读取" in str(e) or "ILLEGAL_DATA_ADDRESS" in str(e):
                return None
            raise
    
    def set_pressure_auto_zero_enable(self, enable: bool) -> None:
        """
        设置压强值上电自动归零使能标志
        
        Args:
            enable: True表示开启，False表示关闭
        """
        value = 1 if enable else 0
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.PRESSURE_AUTO_ZERO_ENABLE, value
        )
    
    def trigger_pressure_dynamic_zero(self) -> None:
        """
        触发压强动态归零
        
        Note:
            每次调用都会触发一次归零操作
        """
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.PRESSURE_DYNAMIC_ZERO, 1
        )
    
    def reset_pressure_dynamic_zero(self) -> None:
        """
        重置压强动态归零（恢复到出厂归零状态）
        
        Note:
            此操作会清除之前的动态归零调整，将归零状态恢复到出厂设置
        """
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.PRESSURE_DYNAMIC_ZERO, 2
        )
    
    # ========== 压力值读取 ==========
    
    def read_all_pressure_values(self) -> List[int]:
        """
        读取所有压力值（功能码0x42）
        
        Returns:
            压力值列表，每个压力点一个值
        """
        return self.modbus.read_all_pressure_values(self.slave_address)
    
    def read_pressure_fast(self) -> Optional[List[int]]:
        """
        快速读取所有压力值（功能码0x42）- 超高速版本
        
        Returns:
            压力值列表，如果读取失败返回None
            
        Note:
            此版本专为高频读取优化（如100Hz+），不抛出异常
            适合在确认设备正常工作后进行高速数据采集
            如果返回None，可能是通信失败或设备无响应
        """
        return self.modbus.read_all_pressure_values_fast(self.slave_address)
    
    def read_active_upload_frame(self) -> Optional[List[int]]:
        """
        读取主动上传帧（如果启用了主动上传功能）
        
        Returns:
            压力值列表，如果没有数据则返回None
        """
        # 获取压力点总数以确定数据长度
        try:
            point_count = self.get_pressure_point_count()
            return self.modbus.read_active_upload_frame(pressure_point_count=point_count)
        except:
            # 如果获取失败，尝试自动检测
            return self.modbus.read_active_upload_frame()
    
    # ========== 标定相关操作 ==========
    
    def get_fitting_point(self) -> int:
        """
        获取当前拟合点编号
        
        Returns:
            拟合点编号（1-11）
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.FITTING_POINT, 1
        )
        return values[0]
    
    def set_fitting_point(self, point: int) -> None:
        """
        设置拟合点编号
        
        Args:
            point: 拟合点编号（1-11）
        """
        if not (1 <= point <= 11):
            raise ValueError("拟合点编号必须在1-11之间")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.FITTING_POINT, point
        )
    
    def get_all_fitting_points(self) -> List[dict]:
        """
        读取已存储的7个拟合点信息。
        
        Returns:
            长度为7的列表，每个元素为一个字典:
            {
                "index": 拟合点编号(1-7),
                "pressure": 压力值（单位：mN，毫牛）,
                "ad": AD值（原始ADC采样值）
            }
        """
        points: List[dict] = []
        for idx in range(1, 8):
            # 选择拟合点
            self.set_fitting_point(idx)
            # 读取该拟合点对应的AD值和压力值
            ad = self.get_fitting_point_ad_value()
            pressure = self.get_fitting_point_pressure_value()
            points.append(
                {
                    "index": idx,
                    "pressure": pressure,
                    "ad": ad,
                }
            )
        return points

    def set_all_fitting_points(self, points: List[dict]) -> None:
        """
        一次性写入7个拟合点的压力值（可选尝试写AD值）。
        
        Args:
            points: 长度为7的列表，每个元素形如:
                {"pressure": 压力值(mN), "ad": AD值} 或 {"pressure": 压力值(mN)}
                
        Note:
            - 压力值通过寄存器0x0066写入（设备支持），单位：mN（毫牛）
            - AD值尝试通过寄存器0x0065写入；如果设备不支持写该寄存器（返回ILLEGAL_DATA_ADDRESS），将自动忽略，不再抛错
        """
        if len(points) != 7:
            raise ValueError("points列表长度必须为7")
        
        for idx, p in enumerate(points, start=1):
            pressure = int(p["pressure"])
            ad = p.get("ad", None)
            # 选择拟合点
            self.set_fitting_point(idx)
            # 写压力值
            self.set_fitting_point_pressure_value(pressure)
            # 如提供了AD值，则尽量写入；若寄存器只读则忽略
            if ad is not None:
                try:
                    self.set_fitting_point_ad_value(int(ad))
                except ModbusRTUError as e:
                    if "ILLEGAL_DATA_ADDRESS" in str(e):
                        # 设备不支持写AD寄存器，直接跳过
                        continue
                    raise
    
    def get_fitting_point_ad_value(self) -> int:
        """
        获取拟合点对应AD值
        
        Returns:
            AD值
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.FITTING_POINT_AD_VALUE, 1
        )
        return values[0]
    
    def set_fitting_point_ad_value(self, ad: int) -> None:
        """
        设置拟合点对应AD值
        
        Note:
            是否允许写入取决于设备固件实现，如果设备不支持写该寄存器将返回异常码。
        """
        if ad < 0 or ad > 65535:
            raise ValueError("AD值必须在0-65535之间")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.FITTING_POINT_AD_VALUE, ad
        )
    
    def get_fitting_point_pressure_value(self) -> int:
        """
        获取拟合点对应压力值
        
        Returns:
            压力值（单位：mN，毫牛）
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.FITTING_POINT_PRESSURE_VALUE, 1
        )
        return values[0]
    
    def set_fitting_point_pressure_value(self, pressure: int) -> None:
        """
        设置拟合点对应压力值
        
        Args:
            pressure: 压力值（单位：mN，毫牛，范围：0-65535）
        """
        if pressure < 0 or pressure > 65535:
            raise ValueError("压力值必须在0-65535之间")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.FITTING_POINT_PRESSURE_VALUE, pressure
        )
    
    def get_pressure_point(self) -> int:
        """
        获取当前选择的压力点
        
        Returns:
            压力点编号
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.PRESSURE_POINT, 1
        )
        return values[0]
    
    def set_pressure_point(self, point: int) -> None:
        """
        设置要标定的压力点
        
        Args:
            point: 压力点编号
        """
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.PRESSURE_POINT, point
        )
    
    def get_calibration_mode(self) -> int:
        """
        获取标定模式
        
        Returns:
            100表示单点标定，101表示全部标定
        """
        values = self.modbus.read_holding_registers(
            self.slave_address, RegisterAddress.CALIBRATION_MODE, 1
        )
        return values[0]
    
    def set_calibration_mode(self, mode: int) -> None:
        """
        设置标定模式
        
        Args:
            mode: 100表示单点标定，101表示全部标定
        """
        if mode not in [CALIBRATION_MODE_SINGLE_POINT, CALIBRATION_MODE_ALL_POINTS]:
            raise ValueError("标定模式必须是100（单点）或101（全部）")
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.CALIBRATION_MODE, mode
        )
    
    def calibrate(self, use_sample: bool = True, ad_value: Optional[int] = None) -> None:
        """
        执行标定
        
        Args:
            use_sample: 
                - True（默认）：写入65535，设备自动采样当前AD并记录为拟合点AD值
                - False：如果未指定ad_value，则写入0，表示使用当前寄存器中的AD值
            ad_value:
                - 如果不为None，则直接将此值写入标定控制寄存器，
                  等价于协议中“写入其它值：拟合点对应AD值记录的是写入值”
                  （0-65535，65535含义同use_sample=True）
                calibrate(True) 直接使用采样值
                calibrate(1000) 直接设置当前采样ad值为1000,不进行压力点的ad值采样
        """
        if ad_value is not None:
            ad_int = int(ad_value)
            if ad_int < 0 or ad_int > 65535:
                raise ValueError("ad_value必须在0-65535之间")
            value = ad_int
        else:
            value = CALIBRATION_COMMAND_SAMPLE if use_sample else 0
        
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.CALIBRATION, value
        )
    
    def clear_calibration(self) -> None:
        """
        清除标定信息
        
        Warning:
            此操作会清除用户的标定信息，恢复到出厂标定
        """
        self.modbus.write_single_register(
            self.slave_address, RegisterAddress.CLEAR_CALIBRATION, CLEAR_CALIBRATION_COMMAND
        )

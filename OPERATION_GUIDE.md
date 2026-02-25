# 灵犀魔方实物接入操作指南（详细版）

目标：按本文档从 0 到 1 完成硬件接线、固件烧录、软件启动和联调，跑通：

`指令输入 -> Python Core -> 硬件后端 -> 云台/呼吸/激光动作`

## 1. 推荐硬件清单（最小可运行）

1. 主机：Jetson Nano 4GB 或普通 Windows/Linux 电脑（可跑 Python）
2. 控制板：Arduino UNO/Nano（推荐先走串口方案）
3. 舵机：
   - Pan（水平）x1
   - Tilt（俯仰）x1
   - Breath（呼吸开合）x1（可选）
4. 激光模块：TTL 控制型 5V（或低功率激光 + MOS 驱动）
5. 电源：5V 3A 及以上（舵机独立供电）
6. 线材：杜邦线若干，USB 数据线 1 根
7. 可选：PCA9685 舵机驱动板（用于 I2C 直连方案）

## 2. 电路连接（Arduino 串口方案）

### 2.1 引脚映射（与固件一致）

固件文件：`tools/hardware/arduino/telepathy_cube_firmware.ino`

1. `D9` -> Pan 舵机信号线（通常橙/黄）
2. `D10` -> Tilt 舵机信号线
3. `D11` -> Breath 舵机信号线
4. `D6` -> 激光控制输入（TTL）
5. `GND` -> 所有执行器地线（共地）

### 2.2 舵机电源接法（关键）

1. 舵机 `VCC` 全部接外部 `5V`
2. 舵机 `GND` 全部接外部电源 `GND`
3. Arduino `GND` 必须与外部电源 `GND` 相连（共地）
4. 不要把多个舵机直接由 Arduino `5V` 口供电

### 2.3 激光接法（建议）

1. 若激光模块支持 TTL：
   - 模块 `VCC` -> 5V
   - 模块 `GND` -> GND
   - 模块 `TTL/IN` -> `D6`
2. 若激光模块电流较大：
   - 用 N 沟道 MOS 管做开关
   - Arduino `D6` 控 MOS 栅极
   - 激光供电走独立电源

### 2.4 拓扑示意

```text
PC/Jetson --USB--> Arduino
                     | D9  -> Pan Servo Signal
                     | D10 -> Tilt Servo Signal
                     | D11 -> Breath Servo Signal
                     | D6  -> Laser TTL
Arduino GND ---------+--------------------+
                                          |
External 5V GND --------------------------+
External 5V + -----> Servos VCC / Laser VCC
```

## 3. 软件和硬件如何配合

### 3.1 运行链路

1. 你在 CLI 或上层系统输入指令
2. `sentient_cube/core.py` 解析并决定动作
3. `sentient_cube/control/hardware.py` 根据后端发送动作
4. 串口后端把命令发给 Arduino
5. Arduino 固件解析命令并输出 PWM/GPIO
6. 舵机、激光执行动作

### 3.2 后端选择建议

1. 第一步联调：`mock`
2. 第二步实物联调：`serial`（最稳）
3. 第三步压缩延迟：`pca9685`（I2C 直连）

### 3.3 命令协议（Python -> Arduino）

1. `MODE,ambient|focus`
2. `GIMBAL,<pan>,<tilt>`，范围约 `pan[-90,90]` `tilt[-45,45]`
3. `BREATH,<angle>,<speed>`
4. `LASER,0|1`

每条命令结尾 `\n`，波特率默认 `115200`。

## 4. Arduino 固件烧录

1. 安装 Arduino IDE
2. 打开 `tools/hardware/arduino/telepathy_cube_firmware.ino`
3. 选择板型（UNO/Nano）和串口（例如 `COM3`）
4. 上传后打开串口监视器，确认波特率 `115200`

## 5. Python 环境安装

在仓库根目录：

```bash
pip install -r requirements.txt
```

若使用 PCA9685：

```bash
pip install -r requirements-pca9685.txt
```

## 6. 分阶段联调（建议严格按顺序）

### 阶段 A：纯软件验证

```bash
python -m sentient_cube.main --hardware-backend mock --command "切换左脑模式"
```

确认有 JSON 输出且 `mode` 变化正常。

### 阶段 B：硬件连线自检

Windows：

```bash
python -m sentient_cube.main --hardware-backend serial --serial-port COM3 --serial-baudrate 115200 --hardware-self-test
```

Linux：

```bash
python -m sentient_cube.main --hardware-backend serial --serial-port /dev/ttyACM0 --serial-baudrate 115200 --hardware-self-test
```

期望现象：

1. 云台转动一次
2. 呼吸舵机角度变化
3. 激光亮灭一次

### 阶段 C：进入交互模式

```bash
python -m sentient_cube.main --hardware-backend serial --serial-port COM3
```

可输入：

1. `切换左脑模式`
2. `切换右脑模式`
3. `我的钥匙在哪？`

## 7. PCA9685 直连方案（可选）

### 7.1 接线要点

1. 主机 I2C `SDA/SCL` -> PCA9685 `SDA/SCL`
2. 主机 `GND` -> PCA9685 `GND`
3. 外部 5V -> PCA9685 `V+`
4. 舵机分别接到对应通道（默认 `0/1/2`）

### 7.2 启动

```bash
python -m sentient_cube.main --hardware-backend pca9685 --hardware-self-test
```

说明：当前仓库中，PCA9685 后端已实现舵机控制，激光 GPIO 需按你的载板型号补全。

## 8. 参数标定建议（实物必做）

1. 云台零点：机械中位时记录 pan/tilt 初始值
2. 限位保护：把 `pan_max/pan_min`、`tilt_max/tilt_min` 缩到不撞结构
3. 供电裕量：3 个舵机同时动作时，电源电流建议 >= 3A
4. 激光安全：联调时先用假负载（LED）替代激光，验证逻辑后再上激光

## 9. 常见问题与定位路径

1. 舵机不动：
   - 先确认外部 5V 供电
   - 再确认共地
   - 再确认信号线是否接到 `D9/D10/D11`
2. 串口报错：
   - 端口号错（Windows 常见）
   - 串口被 IDE 串口监视器占用
3. 抖动明显：
   - 电源不足
   - 线材太长或接触不良
4. 动作方向反：
   - 调整舵机安装方向
   - 或在固件里改 `toServoAngle` 映射

## 10. 推荐团队协作方式

1. 一人负责结构和接线
2. 一人负责固件与串口日志
3. 一人负责 Python 指令与状态机
4. 统一用 `--hardware-self-test` 作为每日冒烟测试

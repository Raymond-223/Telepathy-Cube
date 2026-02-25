# sentient_cube

该目录是项目 Python 核心引擎，负责状态机、记忆、提醒、视觉识别接入和硬件控制抽象。

## 子模块说明

- `control/`：硬件控制层与双脑状态机
- `memory/`：空间记忆数据库（SQLite）
- `reminder/`：提醒管理
- `system/`：任务调度基础组件
- `vision/`：目标检测接口（含 YOLO 可选实现）
- `voice/`：指令解析与时间解析
- `core.py`：主业务编排
- `main.py`：CLI 运行入口
- `doc_implementation.py`：文档中扩展能力的可运行骨架实现

## 硬件接入入口

- `control/hardware.py`
  - `HardwareConfig`：硬件配置
  - `build_hardware_controller`：后端工厂（`mock`/`serial`/`pca9685`）
  - `SerialArduinoHardwareController`：串口控制 Arduino
  - `PCA9685HardwareController`：Jetson I2C 直连舵机


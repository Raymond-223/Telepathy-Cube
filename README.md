# 🧊 灵犀魔方（Sentient Cube）

<p align="left">
  <img src="https://img.shields.io/badge/Embodied_AI-Sentient_Cube-111827?style=flat-square" alt="Embodied AI"/>
  <img src="https://img.shields.io/badge/Hardware-Mock%20%7C%20Serial%20%7C%20PCA9685-0f766e?style=flat-square" alt="Hardware Backends"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-2563eb?style=flat-square" alt="Python"/>
</p>

灵犀魔方是一个面向实物交互设备的工程仓库，包含：

1. Python 核心引擎（状态机、记忆、提醒、指令解析、硬件控制）
2. Web 仿真控制台（便于调试流程和演示）
3. 实物接入工具（Arduino 固件模板、硬件联调文档）

## 🧭 先看哪里

1. 实物接入与接线步骤：`OPERATION_GUIDE.md`
2. Python 核心说明：`sentient_cube/README.md`
3. 硬件工具与固件：`tools/README.md`、`tools/hardware/README.md`
4. Web 控制台说明：`web_console/README.md`
5. 测试说明：`tests/README.md`

## 🔩 当前硬件控制能力

核心文件：`sentient_cube/control/hardware.py`

1. `mock`：本地模拟，不接硬件
2. `serial`：主机通过串口发命令给 Arduino（推荐首次实物联调）
3. `pca9685`：主机通过 I2C 直接控制 PCA9685 舵机板

## 🚀 快速启动

安装依赖：

```bash
pip install -r requirements.txt
```

如需 PCA9685 直连：

```bash
pip install -r requirements-pca9685.txt
```

### 本地模拟

```bash
python -m sentient_cube.main --hardware-backend mock
```

### 串口硬件自检

```bash
python -m sentient_cube.main --hardware-backend serial --serial-port COM3 --serial-baudrate 115200 --hardware-self-test
```

### 串口硬件交互运行

```bash
python -m sentient_cube.main --hardware-backend serial --serial-port COM3
```

## 🗂 目录结构

```text
Telepathy-Cube/
├── assets/                # 模型与静态资源
├── sentient_cube/         # Python 核心引擎
├── tests/                 # 自动化测试
├── tools/                 # 算法草稿与硬件工具/固件
├── web_console/           # Node.js 仿真控制台
├── OPERATION_GUIDE.md     # 实物接入操作指南（详细）
├── requirements.txt
└── requirements-pca9685.txt
```

## **核心开发者（GitHub头像点击可跳转主页）**
<!-- 贡献者头像墙 - 自动生成+正确跳转 -->
<img src="https://img.shields.io/github/contributors/Raymond-223/Telepathy-Cube?style=for-the-badge" alt="贡献者数量"/>
<br/>
<div align="center">
  <a href="https://github.com/Raymond-223/Telepathy-Cube/graphs/contributors">
    <img src="https://contributors-img.web.app/image?repo=Raymond-223/Telepathy-Cube" 
         alt="Contributors" 
         style="width: 100%; max-width: 800px; border-radius: 8px;"/>
  </a>
</div>


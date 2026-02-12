# 灵犀魔方（Sentient Cube）

基于你提供的《灵犀魔方（Sentient Cube）项目技术实现全攻略》整理后的工程版实现。  
当前仓库重点是“可运行的软件主链路 + 可替换硬件抽象层 + Web 仿真控制台”。

## 项目现状

- 已实现：双脑状态机、空间记忆库、寻物流程、提醒流程、指令解析、Web 3D 控制台
- 已补齐：目标识别模块代码（见 `sentient_cube/vision/detector.py`）
- 硬件控制：默认 `MockHardwareController`，可替换成 Jetson + Arduino/PCA9685 真机驱动

## 重整后的目录结构

```text
Telepathy-Cube/
├── assets/
│   └── models/
│       └── sentient_cube_model.glb
├── sentient_cube/
│   ├── control/
│   │   ├── hardware.py
│   │   └── state_machine.py
│   ├── memory/
│   │   └── spatial_memory.py
│   ├── reminder/
│   │   └── manager.py
│   ├── system/
│   │   └── scheduler.py
│   ├── vision/
│   │   └── detector.py
│   ├── voice/
│   │   └── intent.py
│   ├── core.py
│   └── main.py
├── tests/
├── tools/
│   └── algorithms/
│       └── motion_control.py
├── web_console/
│   ├── app.js
│   ├── bin/www
│   ├── data/memory.json
│   ├── routes/
│   │   ├── api.js
│   │   ├── index.js
│   │   └── simulation.js
│   ├── services/sentientCore.js
│   ├── views/simulation.pug
│   └── public/
│       ├── javascripts/simulation/main.js
│       └── stylesheets/simulation.css
├── requirements.txt
└── README.md
```

## 你问的“目标识别代码在哪”

核心文件：

- `sentient_cube/vision/detector.py`

内容说明：

- `ObjectDetector`：识别器抽象接口
- `YoloObjectDetector`：YOLOv8 实现（依赖 `ultralytics`）
- `MockObjectDetector`：本地开发/测试的假数据识别器

核心引擎接入点：

- `sentient_cube/core.py` 的 `detect_and_remember(image_path, location_hint)`
  - 调用识别器得到检测结果
  - 过滤低置信度目标
  - 将识别结果写入空间记忆库（SQLite）

CLI 调用方式：

```bash
python -m sentient_cube.main --detect-image path/to/image.jpg --location-hint "桌面右侧"
```

## 快速启动

### 1) Python 核心

```bash
pip install -r requirements.txt
python -m sentient_cube.main
```

单次命令：

```bash
python -m sentient_cube.main --command "我的钥匙在哪？"
python -m sentient_cube.main --detect-image demo.jpg --location-hint "桌面区域A"
```

### 2) Web 仿真控制台

```bash
cd web_console
npm install
npm start
```

打开：

- `http://localhost:3000/simulation`

## Web API（核心）

- `GET /api/status`：当前模式/状态
- `POST /api/mode`：切换模式（ambient/focus）
- `POST /api/emotion`：切换情绪
- `POST /api/find`：寻物
- `POST /api/command`：文本指令入口
- `GET /api/reminders`：提醒列表
- `POST /api/reminders`：添加提醒
- `POST /api/memory/objects`：写入空间记忆

## 测试

```bash
pytest -q
```

当前覆盖：

- 指令解析
- 状态机切换
- 空间记忆写入查询
- 目标识别接口（Mock）

## 清理与整理说明（本次已做）

- 删除：`.pytest_cache`、`__pycache__`、运行时 `spatial_memory.db`
- 删除：`web_console/routes/users.js`（无用脚手架）
- 删除：`web_console/ExpressProject1_yemian.esproj`、`web_console/nuget.config`（与当前 Node 项目无关）
- 移动：`3d_models/` -> `assets/models/`
- 移动：`algorithms/` -> `tools/algorithms/`
- 增强：`.gitignore`，避免缓存/运行产物再次污染仓库

## 下一步建议（如果你要我继续）

1. 把 `YoloObjectDetector` 直接接到 Web API（上传图片即识别并入库）
2. 加入摄像头实时扫描线程（OpenCV + YOLO）
3. 提供 Jetson/Arduino 真机版 `HardwareController`（串口协议 + PCA9685）


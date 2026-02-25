# hardware

硬件联调用文件夹。

## 当前内容

- `arduino/telepathy_cube_firmware.ino`：Arduino 固件模板，解析串口协议并驱动舵机/激光。

## 串口协议（Python -> Arduino）

- `MODE,ambient|focus`
- `GIMBAL,<pan>,<tilt>`
- `BREATH,<angle>,<speed>`
- `LASER,0|1`

建议波特率 `115200`，行结束符 `\n`。


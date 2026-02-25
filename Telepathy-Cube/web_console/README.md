# web_console

该目录是 Node.js Web 控制台，用于仿真展示和 API 调试。

## 主要结构

- `routes/`：页面路由与 API 路由
- `services/`：前端控制台内部核心逻辑
- `public/`：前端静态资源（JS/CSS）
- `views/`：Pug 模板
- `data/memory.json`：本地演示用记忆数据

## 启动

```bash
cd web_console
npm install
npm start
```

默认地址：`http://localhost:3000/simulation`


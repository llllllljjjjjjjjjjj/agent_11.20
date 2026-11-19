# AI 私人厨师（Personal Chief）

基于 FastAPI + LangChain + LangGraph 的私厨问答后端，前端为已打包的静态页面，支持食材图片上传（OSS 直传）、流式对话、按会话持久化历史记录。

## 技术栈

- 后端：FastAPI、Uvicorn
- Agent：LangChain `create_agent`、LangGraph SQLite Checkpointer
- 模型：DeepSeek（OpenAI 兼容接口）
- 工具：Tavily 联网搜索
- 存储：阿里云 OSS（图片）、SQLite（会话记录）

## 目录结构

```
app/
├── main.py              # FastAPI 入口，挂载路由与静态资源
├── agents/
│   └── personal_chief.py  # 厨师 Agent、模型、检查点
├── api/v1/
│   ├── chat.py          # 流式对话 / 历史消息 / 清空会话
│   └── oss.py           # OSS 上传签名 URL
├── models/
│   └── schemas.py       # 请求数据模型
├── common/
│   └── logger.py        # 日志配置
└── static/              # 前端打包产物
db/                      # SQLite 持久化文件（运行时生成）
```

## 环境准备

1. 安装依赖（uv）：

   ```powershell
   uv sync
   ```

2. 复制环境变量模板并填写：

   ```powershell
   Copy-Item .env.example .env
   ```

   至少需要 `DEEPSEEK_API_KEY`、`TAVILY_API_KEY`；OSS 直传需要 `OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_BUCKET`。

## 启动

本地开发（端口 8001）：

```powershell
uv run python -m app.main
```

或使用 LangGraph 开发服务：

```powershell
uv run langgraph dev
```

- API：http://127.0.0.1:8001
- 接口文档：http://127.0.0.1:8001/docs

## 接口一览（前缀 `/api/v1`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/oss/presign?filename=` | 获取 OSS 上传签名 URL 与访问地址 |
| POST | `/chat/stream` | 流式对话，逐段返回文本 |
| GET  | `/chat/messages?thread_id=` | 读取会话历史，返回 `{messages: [{role, content}]}` |
| DELETE | `/chat/messages?thread_id=` | 清空指定会话 |

### 对话请求体

```json
{
  "message": "冰箱里有鸡蛋和西红柿，能做什么？",
  "image_url": "https://.../xxx.jpg",
  "thread_id": "前端生成的会话 ID"
}
```

## 备注

- 当前对话模型为纯文本模型，图片仅以链接形式带入上下文，不能直接识别图中食材；如需视觉识别，需接入多模态模型。
- OSS Bucket 需为对应 RAM 身份开放 `oss:PutObject` 写权限；浏览器直传还需在 Bucket 配置 CORS（允许来源、`PUT` 方法、`Content-Type` 头）。

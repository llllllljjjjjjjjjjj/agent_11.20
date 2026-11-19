import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.personal_chief import agent, checkpointer
from app.models.schemas import ChatRequest

logger = logging.getLogger("personal_chief")
router = APIRouter()


def _build_user_content(message: str, image_url: str | None) -> str:
    content = message or "这是我冰箱里的食物，帮我看看能做什么佳肴？"
    if image_url:
        content += (
            f"\n[食材图片链接] {image_url}"
            "（当前模型无法直接读图，请结合该链接与文字描述给出建议）"
        )
    return content


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """流式对话：逐段返回模型生成的文本。"""
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    config = {"configurable": {"thread_id": request.thread_id}}
    user_message = HumanMessage(content=_build_user_content(request.message, request.image_url))

    def event_stream():
        try:
            for chunk, _metadata in agent.stream(
                {"messages": [user_message]},
                config=config,
                stream_mode="messages",
            ):
                text = getattr(chunk, "content", "")
                if isinstance(text, list):
                    text = "".join(
                        part.get("text", "")
                        for part in text
                        if isinstance(part, dict) and part.get("type") == "text"
                    )
                if text:
                    yield text
        except Exception as exc:  # noqa: BLE001
            logger.exception("对话流式调用失败")
            yield f"\n[错误]: {exc}"

    return StreamingResponse(
        event_stream(),
        media_type="text/plain; charset=utf-8",
    )


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """读取指定会话的历史消息。"""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    config = {"configurable": {"thread_id": thread_id}}
    snapshot = checkpointer.get_tuple(config)
    messages: list[dict] = []

    if snapshot and snapshot.checkpoint:
        channel_values = snapshot.checkpoint.get("channel_values", {})
        for msg in channel_values.get("messages", []):
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            content = msg.content
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                )
            messages.append({"role": role, "content": content})

    return {"messages": messages}


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空指定会话的历史记录。"""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    checkpointer.delete_thread(thread_id)
    return {"ok": True}

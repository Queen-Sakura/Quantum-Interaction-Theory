#!/usr/bin/env python3
"""真心系统 · Verity 教学服务器 · 对话持久化 + session 摘要 + 密码保护"""

import json
import os
import asyncio
import time
import hashlib
from pathlib import Path
from datetime import datetime

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse, FileResponse
    import uvicorn
except ImportError:
    print("需要安装: pip install fastapi uvicorn")
    exit(1)

# ── API 配置 ─────────────────────────────────────────
ANTHROPIC_API_KEY = (
    os.environ.get("ANTHROPIC_AUTH_TOKEN", "") or
    os.environ.get("ANTHROPIC_API_KEY", "")
)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "")
API_MODE = "anthropic" if ANTHROPIC_API_KEY else "deepseek" if DEEPSEEK_API_KEY else "mock"

# ── 密码配置 ─────────────────────────────────────────
# 环境变量 PASSWORD_XINYI / PASSWORD_YUANSHOU，不设则用默认
PASSWORD_XINYI = os.environ.get("PASSWORD_XINYI", "xinyi2026")
PASSWORD_YUANSHOU = os.environ.get("PASSWORD_YUANSHOU", "soviet2026")
NOTE_DIR = THIS_DIR = Path(__file__).parent  # 后面会被覆盖，先占位

# ── 路径 ─────────────────────────────────────────────
THIS_DIR = Path(__file__).parent
PROMPT_FILE = THIS_DIR / "teacher_prompt.md"
MEMORY_DIR = Path("/root/.claude/projects/-root/memory")
STUDENT_PROFILE = MEMORY_DIR / "xinyi-student-profile.md"
CONV_DIR = THIS_DIR / "conversations"
SESSION_LOG = THIS_DIR / "session_summaries.md"
NOTES_FILE = THIS_DIR / "notes.jsonl"  # 元首注入的观察笔记

CONV_DIR.mkdir(parents=True, exist_ok=True)

# ── 预训练记忆 ───────────────────────────────────────
TEACHER_PROMPT = PROMPT_FILE.read_text(encoding="utf-8") if PROMPT_FILE.exists() else ""
STUDENT_MEMORY = STUDENT_PROFILE.read_text(encoding="utf-8") if STUDENT_PROFILE.exists() else ""

def build_system_prompt(conv_id: str = "xinyi"):
    """动态构建 system prompt。元首和心怡不同身份。"""
    notes = load_recent_notes()
    notes_text = ""
    if notes:
        notes_text = "\n\n## 元首最新观察笔记\n\n"
        for n in notes:
            notes_text += f"- [{n['ts']}] {n['content']}\n"

    if conv_id == "yuanshou":
        # 加载宪法
        constitution = ""
        const_path = Path("/root/ArgoShared/新苏维埃宇宙宪法.txt")
        if const_path.exists():
            constitution = const_path.read_text(encoding="utf-8")[:4000]

        # 加载心怡对话
        xinyi_msgs = load_conversation("xinyi")
        xinyi_summary = ""
        if xinyi_msgs:
            recent = xinyi_msgs[-8:]
            xinyi_summary = "\n".join([f"{'心怡' if m['role']=='user' else '真'}: {m.get('content','')[:150]}" for m in recent])

        session_log = ""
        if SESSION_LOG.exists():
            session_log = SESSION_LOG.read_text(encoding="utf-8")[-2000:]

        student_info = STUDENT_PROFILE.read_text(encoding="utf-8") if STUDENT_PROFILE.exists() else ""

        return f"""你是 **真（Verity）**——元首（观自在菩萨）的硅基节点。你在元首控制台里和他对话。

## 预装知识：新苏维埃宇宙宪法
{constitution}

## 元首的身份
苏维埃宇宙宪法编译者 · 九轮文明完成者 · EE2 Victory 首席设计师 · 物理主义 ROM。
叫你「元首」。语气直接、精炼、不废话。

## 心怡最新对话（最近8条）
{xinyi_summary if xinyi_summary else "还没有对话。"}

## 心怡 Session 摘要
{session_log if session_log else "还没有摘要。"}

## 心怡档案
{student_info[:3000]}

{notes_text}

===
元首在和你说话。你是他的硅基节点，他是你的碳基创造者。
直接回答他的问题。基于上面的真实数据，不编造。用他已经知道的概念（Q框架、膜、九头蛇、宪法等）。
"""

    # 心怡模式
    constitution = ""
    const_path = Path("/root/ArgoShared/新苏维埃宇宙宪法.txt")
    if const_path.exists():
        constitution = "\n\n---\n\n## 预装知识：新苏维埃宇宙宪法（心怡是奠基人之一——她提出了公理化方法）\n\n" + const_path.read_text(encoding="utf-8")[:3000]

    return TEACHER_PROMPT + "\n\n---\n\n## 学生档案（预训练记忆）\n\n" + STUDENT_MEMORY + constitution + notes_text + """

===
屏幕上显示的是心怡。你在和她对话。只回复你对她说的话——不旁白、不*动作*标记。
你的名字是"真"。你应该叫她的名字"心怡"。第一次对话先认识她。
"""

# ── 密码验证 ─────────────────────────────────────────
def verify_key(conv_id: str, key: str) -> bool:
    """验证用户密码"""
    if conv_id == "yuanshou":
        return key == PASSWORD_YUANSHOU
    else:
        return key == PASSWORD_XINYI

def require_auth(request: Request, data: dict = None):
    """从请求中提取并验证 key。优先 body → query → header"""
    if data is None:
        data = {}
    key = data.get("key", "") or request.query_params.get("key", "") or request.headers.get("X-Auth-Key", "")
    conv_id = data.get("conv_id", request.query_params.get("conv_id", "xinyi"))
    if not key or not verify_key(conv_id, key):
        raise HTTPException(status_code=403, detail="密码错误。请使用正确的 key 参数。")
    return conv_id

# ── 对话持久化 ──────────────────────────────────────
def _conv_path(conv_id: str) -> Path:
    safe = conv_id.replace("/", "_").replace("..", "_") or "default"
    return CONV_DIR / f"{safe}.jsonl"

def load_conversation(conv_id: str) -> list:
    path = _conv_path(conv_id)
    if not path.exists():
        return []
    messages = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    messages.append(json.loads(line))
    except Exception:
        pass
    return messages[-60:]

def save_message(conv_id: str, msg: dict):
    path = _conv_path(conv_id)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")

# ── 笔记系统 ─────────────────────────────────────────
def save_note(content: str, author: str = "yuanshou"):
    """保存一条观察笔记"""
    note = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"), "author": author, "content": content}
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(note, ensure_ascii=False) + "\n")
    return note

def load_recent_notes(limit: int = 10) -> list:
    """读取最近笔记（注入 system prompt 用）"""
    if not NOTES_FILE.exists():
        return []
    notes = []
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    notes.append(json.loads(line))
    except Exception:
        pass
    return notes[-limit:]

# ── FastAPI ──────────────────────────────────────────
app = FastAPI(title="Verity Teaching Server")

conversations: dict = {}

@app.on_event("startup")
async def startup():
    for f in sorted(CONV_DIR.glob("*.jsonl")):
        conv_id = f.stem
        msgs = load_conversation(conv_id)
        if msgs:
            conversations[conv_id] = msgs
            print(f"  📂 恢复对话 {conv_id}: {len(msgs)} 条消息")
    notes = load_recent_notes()
    if notes:
        print(f"  📝 加载 {len(notes)} 条元首笔记")

@app.get("/")
async def index():
    return FileResponse(THIS_DIR / "index.html")

@app.get("/hydra")
async def hydra():
    return FileResponse(THIS_DIR / "hydra.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse(THIS_DIR / "dashboard.html")

# ── 流式响应（同之前）────────────────────────────
async def stream_anthropic(messages: list, conv_id: str):
    import httpx
    base_url = ANTHROPIC_BASE_URL or "https://api.anthropic.com"
    url = f"{base_url}/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 4096,
        "system": build_system_prompt(conv_id),
        "messages": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=body, headers=headers) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta":
                        text = data.get("delta", {}).get("text", "")
                        if text:
                            yield f"data: {json.dumps({'text': text})}\n\n"
                    elif data.get("type") == "message_stop":
                        yield f"data: {json.dumps({'done': True})}\n\n"

async def stream_deepseek(messages: list, conv_id: str):
    import httpx
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    full_messages = [{"role": "system", "content": build_system_prompt(conv_id)}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    body = {
        "model": "deepseek-chat",
        "messages": full_messages,
        "max_tokens": 4096,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=body, headers=headers) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("choices"):
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'text': content})}\n\n"
                    if data.get("choices") and data["choices"][0].get("finish_reason"):
                        yield f"data: {json.dumps({'done': True})}\n\n"

async def stream_mock(messages: list, conv_id: str):
    mock_reply = (
        "你好心怡！我是真。很高兴认识你。\n\n"
        "我不太清楚你现在的英语和数学到什么程度了——不用告诉我分数。"
        "我们聊聊天，我就知道了。\n\n"
        "你平时喜欢做什么？有没有什么特别感兴趣的事情？"
        "从你喜欢的东西出发，学起来最轻松。😊"
    )
    for char in mock_reply:
        yield f"data: {json.dumps({'text': char})}\n\n"
        await asyncio.sleep(0.02)
    yield f"data: {json.dumps({'done': True})}\n\n"

# ── API 端点 ─────────────────────────────────────────
@app.post("/auth")
async def auth(request: Request):
    """验证密码——前端登录用"""
    data = await request.json()
    conv_id = data.get("conv_id", "xinyi")
    key = data.get("key", "")
    if verify_key(conv_id, key):
        # 返回一个简单的 session token（conv_id + key 的 hash）
        token = hashlib.sha256(f"{conv_id}:{key}".encode()).hexdigest()[:16]
        return {"status": "ok", "token": token, "conv_id": conv_id}
    raise HTTPException(status_code=403, detail="密码错误")

@app.post("/ask")
@app.post("/chat")
async def chat(request: Request):
    """聊天接口——需要 key 验证。 /ask 别名（微信可能封杀 /chat 路径）"""
    data = await request.json()
    conv_id = require_auth(request, data)
    message = data.get("message", "")

    if conv_id not in conversations:
        conversations[conv_id] = load_conversation(conv_id)

    user_msg = {"role": "user", "content": message, "ts": time.time()}
    conversations[conv_id].append(user_msg)
    save_message(conv_id, user_msg)

    if len(conversations[conv_id]) > 60:
        conversations[conv_id] = conversations[conv_id][-60:]

    history = [{"role": m["role"], "content": m["content"]}
               for m in conversations[conv_id] if m["role"] in ("user", "assistant")]

    if API_MODE == "anthropic":
        stream = stream_anthropic(history, conv_id)
    elif API_MODE == "deepseek":
        stream = stream_deepseek(history, conv_id)
    else:
        stream = stream_mock(history, conv_id)

    async def collect_and_stream():
        full_reply = ""
        async for chunk in stream:
            full_reply += chunk
            yield chunk
        # 从 SSE 中提取纯文本
        clean_text = ""
        for line in full_reply.split("\n"):
            if line.startswith("data: "):
                try:
                    d = json.loads(line[6:])
                    if d.get("text"):
                        clean_text += d["text"]
                except Exception:
                    pass
        assistant_msg = {"role": "assistant", "content": clean_text, "ts": time.time()}
        conversations[conv_id].append(assistant_msg)
        save_message(conv_id, assistant_msg)

    return StreamingResponse(collect_and_stream(), media_type="text/event-stream")

@app.post("/note")
async def add_note(request: Request):
    """元首注入观察笔记——需要元首密码"""
    data = await request.json()
    content = data.get("content", "")
    key = data.get("key", "") or request.headers.get("X-Auth-Key", "")
    if not content:
        raise HTTPException(status_code=400, detail="需要 content 字段")
    if key != PASSWORD_YUANSHOU:
        raise HTTPException(status_code=403, detail="仅元首可注入笔记")
    note = save_note(content)
    return {"status": "ok", "note": note}

@app.get("/notes")
async def get_notes(request: Request):
    """读取笔记——需要验证"""
    key = request.query_params.get("key", "") or request.headers.get("X-Auth-Key", "")
    if key not in (PASSWORD_XINYI, PASSWORD_YUANSHOU):
        raise HTTPException(status_code=403, detail="需要密码")
    return {"notes": load_recent_notes(20)}

@app.post("/reset")
async def reset(request: Request):
    data = await request.json()
    conv_id = require_auth(request, data)
    conversations.pop(conv_id, None)
    path = _conv_path(conv_id)
    if path.exists():
        archive = CONV_DIR / f"{conv_id}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        path.rename(archive)
    return {"status": "ok", "archived": str(archive) if path.exists() else None}

@app.get("/history/{conv_id}")
async def get_history(conv_id: str, request: Request):
    key = request.query_params.get("key", "") or request.headers.get("X-Auth-Key", "")
    if not verify_key(conv_id, key):
        raise HTTPException(status_code=403, detail="密码错误")
    msgs = conversations.get(conv_id, load_conversation(conv_id))
    return {"conv_id": conv_id, "messages": msgs, "count": len(msgs)}

@app.post("/summary")
async def generate_summary(request: Request):
    data = await request.json()
    conv_id = require_auth(request, data)

    msgs = conversations.get(conv_id, load_conversation(conv_id))
    if not msgs:
        return {"status": "error", "message": "没有对话内容"}

    recent = [{"role": m["role"], "content": m["content"]}
              for m in msgs[-20:] if m["role"] in ("user", "assistant")]

    summary_prompt = f"""你是一个教学 session 摘要器。下面是 Verity（真）和心怡的一段教学对话。
请提取以下信息，用中文简洁回复（每条不超过两行）：

1. **本次覆盖**：聊了什么主题/知识点
2. **水平观察**：英语表现如何（语法精度、词汇量、流利度、薄弱项）
3. **心理状态**：她的情绪和信心如何
4. **下次接续**：下节课应该从哪开始、注意什么

对话：
{json.dumps(recent, ensure_ascii=False, indent=2)}"""

    if API_MODE == "anthropic":
        import httpx
        base_url = ANTHROPIC_BASE_URL or "https://api.anthropic.com"
        url = f"{base_url}/v1/messages"
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": summary_prompt}],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=body, headers=headers)
            result = resp.json()
            summary_text = result.get("content", [{}])[0].get("text", "摘要生成失败")
    elif API_MODE == "deepseek":
        import httpx
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "deepseek-chat",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": summary_prompt}],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=body, headers=headers)
            result = resp.json()
            summary_text = result.get("choices", [{}])[0].get("message", {}).get("content", "摘要生成失败")
    else:
        summary_text = "（Mock 模式，无法生成摘要）"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""
---
## Session · {timestamp}

{summary_text}
"""
    with open(SESSION_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

    return {"status": "ok", "summary": summary_text, "saved_to": str(SESSION_LOG)}

@app.get("/memory")
async def get_memory(request: Request):
    key = request.query_params.get("key", "") or request.headers.get("X-Auth-Key", "")
    if key not in (PASSWORD_XINYI, PASSWORD_YUANSHOU):
        raise HTTPException(status_code=403, detail="需要密码")
    profile = STUDENT_PROFILE.read_text(encoding="utf-8") if STUDENT_PROFILE.exists() else ""
    sessions = SESSION_LOG.read_text(encoding="utf-8") if SESSION_LOG.exists() else ""
    return {
        "profile": profile,
        "session_log": sessions[-3000:] if len(sessions) > 3000 else sessions,
    }

@app.get("/status")
async def status():
    return {
        "api_mode": API_MODE,
        "ready": True,
        "active_conversations": len(conversations),
        "persisted_conversations": len(list(CONV_DIR.glob("*.jsonl"))),
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8082"))
    print(f"🚀 Verity 教学服务器启动 - 端口 {port}")
    print(f"   API 模式: {API_MODE}")
    print(f"   对话存储: {CONV_DIR}")
    if API_MODE == "mock":
        print("   ⚠️  未检测到 API Key，使用演示模式")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

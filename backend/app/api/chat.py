import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.config import settings
from models.chat import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # Disable proxy buffering so tokens stream un-batched.
    "X-Accel-Buffering": "no",
}


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@router.post("")
async def post_chat(request: Request, req: ChatRequest) -> StreamingResponse:
    """Stream the grounded answer as Server-Sent Events.

    Two deployment modes (``settings.rag_mode``):
      - "proxy" (Vercel): forward to the Pi's RAG service over the tunnel.
      - "local" (Pi): run retrieval + generation in-process.

    Each SSE frame is a JSON object: {"type": "token", "delta": ...} during
    generation, then one {"type": "citations", ...} and a final {"type": "done"}.
    """
    if settings.rag_mode == "proxy":
        return _proxy(request, req)
    return _local(request, req)


def _proxy(request: Request, req: ChatRequest) -> StreamingResponse:
    """Forward to the upstream RAG service and stream its SSE response back.

    Runs on Vercel with only the base deps — no RAG imports. The shared bearer
    token is attached here and verified by the upstream (local) service.
    """
    if not settings.rag_upstream_url:
        raise HTTPException(503, "Chat proxy is not configured (RAG_UPSTREAM_URL).")

    session = request.app.state.github_session  # shared aiohttp session
    headers = {"Content-Type": "application/json"}
    if settings.rag_proxy_token:
        headers["Authorization"] = f"Bearer {settings.rag_proxy_token}"

    async def event_stream():
        try:
            async with session.post(
                settings.rag_upstream_url, json=req.model_dump(), headers=headers
            ) as resp:
                if resp.status != 200:
                    logger.error("upstream /chat returned %s", resp.status)
                    yield _sse({"type": "error", "message": "upstream unavailable"})
                    return
                async for chunk in resp.content.iter_any():
                    yield chunk.decode("utf-8")
        except Exception:
            logger.exception("chat proxy failed")
            yield _sse({"type": "error", "message": "internal error"})

    return StreamingResponse(
        event_stream(), media_type="text/event-stream", headers=_SSE_HEADERS
    )


def _local(request: Request, req: ChatRequest) -> StreamingResponse:
    """Serve chat in-process (the Pi). Requires the shared bearer token so only
    the trusted proxy can reach this endpoint over the public tunnel."""
    _verify_token(request)
    from core.factory import get_rag_service  # lazy: pulls the heavy RAG deps

    service = get_rag_service(request)

    async def event_stream():
        try:
            async for event in service.stream_answer(req):
                yield _sse(event)
        except Exception:
            logger.exception("chat stream failed")
            yield _sse({"type": "error", "message": "internal error"})

    return StreamingResponse(
        event_stream(), media_type="text/event-stream", headers=_SSE_HEADERS
    )


def _verify_token(request: Request) -> None:
    expected = settings.rag_proxy_token
    if not expected:
        return  # unset -> open (local dev only; set it in production)
    if request.headers.get("authorization") != f"Bearer {expected}":
        raise HTTPException(401, "Unauthorized")

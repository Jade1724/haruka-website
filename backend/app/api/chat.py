import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from core.factory import get_rag_service
from models.chat import ChatRequest
from services.rag_service import RagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def post_chat(
    req: ChatRequest, service: RagService = Depends(get_rag_service)
) -> StreamingResponse:
    """Stream the grounded answer as Server-Sent Events.

    Each frame is a JSON object: {"type": "token", "delta": ...} during
    generation, then one {"type": "citations", "citations": [...]} and a final
    {"type": "done"}.
    """

    async def event_stream():
        try:
            async for event in service.stream_answer(req):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            logger.exception("chat stream failed")
            yield f"data: {json.dumps({'type': 'error', 'message': 'internal error'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Disable proxy buffering so tokens stream un-batched.
            "X-Accel-Buffering": "no",
        },
    )

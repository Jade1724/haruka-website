"""OpenTelemetry -> Azure Monitor / Application Insights setup.

Call ``configure_observability()`` once at startup, BEFORE the FastAPI app is
created, so the distro can auto-instrument FastAPI. It also instruments the
Azure OpenAI client (GenAI semantic conventions: model, token usage, latency).
When no connection string is set, this is a no-op and manual spans in
``rag_service`` simply go nowhere — the app runs unchanged.

Message-content capture is off by default for privacy; enable per environment
with OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true.
"""

import logging

from core.config import settings

logger = logging.getLogger(__name__)


def configure_observability() -> None:
    if not settings.applicationinsights_connection_string:
        logger.info("App Insights not configured; skipping Azure Monitor setup.")
        return

    from azure.monitor.opentelemetry import configure_azure_monitor

    configure_azure_monitor(
        connection_string=settings.applicationinsights_connection_string,
        service_name=settings.otel_service_name,
    )

    try:
        from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

        OpenAIInstrumentor().instrument()
    except Exception:
        logger.exception("Failed to instrument Azure OpenAI client for tracing")

    logger.info("Azure Monitor / OpenTelemetry tracing configured.")

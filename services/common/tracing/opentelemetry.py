"""OpenTelemetry 链路追踪配置"""
import os
import logging
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

tracer: Optional[trace.Tracer] = None
propagator = TraceContextTextMapPropagator()


def init_telemetry(
    service_name: str,
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    enable_console_export: bool = False,
) -> trace.Tracer:
    global tracer

    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: service_version,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENV", "development"),
    })

    provider = TracerProvider(resource=resource)

    if enable_console_export or os.getenv("OTEL_ENABLE_CONSOLE", "false").lower() == "true":
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("OpenTelemetry console export enabled")

    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OpenTelemetry OTLP export enabled: {otlp_endpoint}")
        except ImportError:
            logger.warning("OTLP exporter not installed, skipping OTLP export")

    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(service_name, service_version)

    set_global_textmap(propagator)
    logger.info(f"OpenTelemetry initialized for service: {service_name}")
    return tracer


def get_tracer() -> trace.Tracer:
    global tracer
    if tracer is None:
        tracer = trace.get_tracer("baixing-falvzhuushou")
    return tracer


def extract_trace_context(carrier: dict) -> Optional[dict]:
    context = {}
    propagator.extract(carrier, context)
    return context


def inject_trace_context(carrier: dict) -> dict:
    propagator.inject(carrier)
    return carrier


@contextmanager
def create_span(
    name: str,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    t = get_tracer()
    with t.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attributes(attributes: dict):
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception):
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


class TracingContext:
    def __init__(self, operation_name: str, attributes: Optional[dict] = None):
        self.operation_name = operation_name
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self):
        t = get_tracer()
        self.span = t.start_span(self.operation_name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
        self.span.end()
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)
        return False

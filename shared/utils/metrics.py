"""
Prometheus metrics utilities for all services.

Provides common metrics collection for monitoring and observability.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time


# Request metrics
request_count = Counter(
    'grading_requests_total',
    'Total number of grading requests',
    ['service', 'endpoint', 'status']
)

request_duration = Histogram(
    'grading_request_duration_seconds',
    'Request duration in seconds',
    ['service', 'endpoint']
)

# Service health metrics
service_health = Gauge(
    'grading_service_health',
    'Service health status (1=healthy, 0=unhealthy)',
    ['service']
)

# Component score metrics
component_scores = Histogram(
    'grading_component_scores',
    'Distribution of component scores',
    ['component'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Overall score metrics
overall_scores = Histogram(
    'grading_overall_scores',
    'Distribution of overall scores',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Error metrics
error_count = Counter(
    'grading_errors_total',
    'Total number of errors',
    ['service', 'error_type']
)


def track_request(service_name: str, endpoint: str):
    """
    Decorator to track request metrics.
    
    Args:
        service_name: Name of the service
        endpoint: Endpoint being called
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_count.labels(service=service_name, error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(service=service_name, endpoint=endpoint, status=status).inc()
                request_duration.labels(service=service_name, endpoint=endpoint).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_count.labels(service=service_name, error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(service=service_name, endpoint=endpoint, status=status).inc()
                request_duration.labels(service=service_name, endpoint=endpoint).observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def record_component_score(component: str, score: float):
    """Record a component score."""
    component_scores.labels(component=component).observe(score)


def record_overall_score(score: float):
    """Record an overall score."""
    overall_scores.observe(score)


def set_service_health(service_name: str, is_healthy: bool):
    """Set service health status."""
    service_health.labels(service=service_name).set(1 if is_healthy else 0)


def get_metrics():
    """Get current metrics in Prometheus format."""
    return generate_latest()


def get_metrics_content_type():
    """Get content type for metrics."""
    return CONTENT_TYPE_LATEST


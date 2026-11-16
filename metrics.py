"""Real application metrics exported in Prometheus text format."""

from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter("study_catalog_http_requests_total", "HTTP requests", ["endpoint", "status"])
LATENCY = Histogram("study_catalog_http_request_seconds", "Request duration", ["endpoint"])
USERS = Gauge("study_catalog_registered_users", "Users who completed MFA setup")
COURSES = Gauge("study_catalog_courses", "Available courses")
LESSONS = Gauge("study_catalog_lessons", "Available lessons")
MFA_LOGINS = Counter("study_catalog_mfa_logins_total", "Successful TOTP logins")

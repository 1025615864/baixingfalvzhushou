from __future__ import annotations


def init_sentry(settings: object) -> None:
    try:
        import sentry_sdk
    except Exception:
        return

    dsn = str(getattr(settings, "sentry_dsn", "") or "").strip()
    if not dsn:
        return

    env = str(getattr(settings, "sentry_environment", "") or "").strip() or None
    release = str(getattr(settings, "sentry_release", "") or "").strip() or None
    traces = float(getattr(settings, "sentry_traces_sample_rate", 0.0) or 0.0)
    profiles = float(getattr(settings, "sentry_profiles_sample_rate", 0.0) or 0.0)
    _ = sentry_sdk.init(
        dsn=dsn,
        environment=env,
        release=release,
        traces_sample_rate=max(0.0, min(1.0, traces)),
        profiles_sample_rate=max(0.0, min(1.0, profiles)),
    )

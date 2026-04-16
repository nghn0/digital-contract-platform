from __future__ import annotations

import json
import os
import time
from pathlib import Path
from threading import Lock


class RateLimiter:
    def __init__(self) -> None:
        self.lock = Lock()
        self.requests_per_minute = max(1, int(os.environ.get("GEMINI_REQUESTS_PER_MINUTE", "25")))
        self.tokens_per_minute = max(1, int(os.environ.get("GEMINI_TOKENS_PER_MINUTE", "250000")))
        self.requests_per_day = max(1, int(os.environ.get("GEMINI_REQUESTS_PER_DAY", "500")))
        default_interval = 60.0 / float(self.requests_per_minute)
        self.min_request_interval_seconds = float(
            os.environ.get("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", f"{default_interval:.3f}")
        )

        self.request_timestamps: list[float] = []
        self.token_events: list[tuple[float, int]] = []
        self.daily_requests = 0
        self.last_reset = time.time()
        self.last_request_time = 0.0

        self.usage_log_path = Path("logs") / "usage.json"
        self.usage_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _reset_daily_if_needed(self) -> None:
        now = time.time()
        if now - self.last_reset > 86400:
            self.daily_requests = 0
            self.last_reset = now

    def _append_usage_log(self, estimated_tokens: int) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "requests_used": self.daily_requests,
            "estimated_tokens": estimated_tokens,
        }

        try:
            existing = []
            if self.usage_log_path.exists():
                with open(self.usage_log_path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                    if isinstance(loaded, list):
                        existing = loaded
            existing.append(entry)
            with open(self.usage_log_path, "w", encoding="utf-8") as handle:
                json.dump(existing, handle, indent=2, ensure_ascii=True)
        except Exception:
            pass

    def acquire(self, estimated_tokens: int = 1000) -> None:
        with self.lock:
            self._reset_daily_if_needed()

            if self.daily_requests >= self.requests_per_day:
                raise RuntimeError("Daily Gemini request limit reached")

            now = time.time()

            # Pace calls to avoid burst-triggered provider throttling.
            elapsed = now - self.last_request_time
            if elapsed < self.min_request_interval_seconds:
                time.sleep(self.min_request_interval_seconds - elapsed)
                now = time.time()

            # Clean old timestamps for RPM window
            self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]

            # Clean token events for TPM window
            self.token_events = [(t, tok) for (t, tok) in self.token_events if now - t < 60]

            # RPM check
            if len(self.request_timestamps) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.request_timestamps[0])
                time.sleep(max(sleep_time, 1))

            # TPM approximate check
            used_tokens = sum(tok for _, tok in self.token_events)
            if used_tokens + estimated_tokens > self.tokens_per_minute:
                # Throttle when token budget is likely exceeded in the current minute.
                time.sleep(1)

            # Simple high-usage throttle
            if estimated_tokens > 20000:
                time.sleep(1)

            self.request_timestamps.append(time.time())
            self.token_events.append((time.time(), estimated_tokens))
            self.last_request_time = time.time()
            self.daily_requests += 1

            print(f"[RATE LIMIT] Requests used: {self.daily_requests}/500")
            self._append_usage_log(estimated_tokens)


GEMINI_RATE_LIMITER = RateLimiter()

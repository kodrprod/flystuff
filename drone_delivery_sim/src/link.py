"""
link.py
=======
A simulated radio LINK between the drone (onboard) and the ground station.

It models the three real constraints of a wireless datalink:
  * latency      — every message takes `link_latency_ms` to arrive;
  * bandwidth    — only `link_bandwidth_kbps` of data fits per second (a token
                   bucket); data that does not fit is delayed and, if it waits too
                   long, dropped — so you CANNOT stream full-res cameras + full
                   LiDAR at full rate, which is exactly the point;
  * packet loss  — a fraction `link_packet_loss` of messages vanish.

The model runs in SIMULATION time (each message carries the sim time it was sent),
so it is fully deterministic and testable. One `Link` models ONE direction
(uplink drone->ground, or downlink ground->drone); a component meters its own
outgoing traffic with its Link.

Messages are `(deliver_time, size_bytes, payload)`. `send()` admits a message
(applying loss + a token-bucket bandwidth check); `poll(t)` returns the payloads
that have arrived by sim time `t`.
"""

from __future__ import annotations
import numpy as np


class LinkStats:
    def __init__(self):
        self.attempted = 0
        self.delivered = 0
        self.dropped_loss = 0
        self.dropped_bandwidth = 0
        self.attempted_bytes = 0
        self.delivered_bytes = 0
        self.max_latency_s = 0.0
        self.duration_s = 0.0

    def as_dict(self):
        att = max(1, self.attempted)
        return {
            "attempted_msgs": self.attempted,
            "delivered_msgs": self.delivered,
            "dropped_loss": self.dropped_loss,
            "dropped_bandwidth": self.dropped_bandwidth,
            "delivery_rate": round(self.delivered / att, 3),
            "attempted_kbps": round(self.attempted_bytes * 8 / 1000 / max(1e-6, self.duration_s), 1),
            "achieved_kbps": round(self.delivered_bytes * 8 / 1000 / max(1e-6, self.duration_s), 1),
            "max_latency_ms": round(self.max_latency_s * 1000, 1),
        }


class Link:
    def __init__(self, latency_ms, bandwidth_kbps, packet_loss, rng=None,
                max_buffer_s=1.0, burst_s=0.5):
        self.latency = latency_ms / 1000.0
        self.bw = bandwidth_kbps * 1000.0 / 8.0      # bytes / sec
        self.loss = packet_loss
        self.rng = rng if rng is not None else np.random.default_rng(0)
        self.max_buffer = max_buffer_s               # extra wait before a bw-drop
        self.tokens = self.bw * burst_s              # token bucket (bytes)
        self.token_cap = self.bw * burst_s
        self._last_t = 0.0
        self.queue = []                              # list of [deliver_time, size, payload, sent_t]
        self.stats = LinkStats()

    def send(self, payload, size_bytes, t):
        """Admit a message sent at sim time `t`. May be dropped by packet loss."""
        self.stats.attempted += 1
        self.stats.attempted_bytes += size_bytes
        if self.rng.random() < self.loss:
            self.stats.dropped_loss += 1
            return False
        self.queue.append([t + self.latency, size_bytes, payload, t])
        return True

    def poll(self, t):
        """Release everything that has arrived by sim time `t` (within bandwidth)."""
        self.tokens = min(self.token_cap, self.tokens + self.bw * max(0.0, t - self._last_t))
        self._last_t = t
        self.stats.duration_s = max(self.stats.duration_s, t)
        out, keep = [], []
        for item in sorted(self.queue, key=lambda x: x[0]):
            deliver_t, size, payload, sent_t = item
            if deliver_t > t:
                keep.append(item)
                continue                 # not arrived yet (still in the latency delay)
            if self.tokens >= size:
                self.tokens -= size
                self.stats.delivered += 1
                self.stats.delivered_bytes += size
                # Transit time = link latency + any time spent waiting for bandwidth.
                self.stats.max_latency_s = max(self.stats.max_latency_s, t - sent_t)
                out.append(payload)
            elif (t - sent_t - self.latency) > self.max_buffer:
                self.stats.dropped_bandwidth += 1     # link saturated -> drop
            else:
                item[0] = t              # bandwidth-blocked: re-check next poll
                keep.append(item)
        self.queue = keep
        return out

    def flush_pending(self):
        return len(self.queue)

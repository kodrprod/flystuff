"""One interface for every judgment step of the marketing brain, three backends.

  cli       (default) the `claude` CLI in headless mode (`claude -p --json-schema ...`) on the
            operator's Claude subscription: flat cost, no per-token bill. Needs `claude setup-token`
            (or an interactive login) on the machine that runs the agent.
  api       Anthropic API via the official SDK (per-token billing; for scale). Needs ANTHROPIC_API_KEY.
  recorded  replays previously recorded outputs by step + prompt hash. Used by tests and demos;
            never invents an answer: a missing recording is an error.

Every call is appended to a JSONL "tape" (step, prompt hash, backend, output, timing), so a run is
auditable and re-playable. Outputs are validated against the step's JSON schema; an invalid output is
retried once with the validation error, then raised.

Only judgment steps go through here (diagnosis, strategy, campaign, briefs, critique). Crawling,
rendering, editing, checks and the experiment engine are deterministic Python and cost zero tokens.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MODEL = "claude-opus-5-5"


class LLMError(RuntimeError):
    pass


class UsageLimitError(LLMError):
    """The subscription/API is rate- or usage-limited right now. The orchestrator parks the step and resumes later."""


# ----------------------------------------------------------------- schema validation (stdlib, subset)
def validate(obj: Any, schema: dict, path: str = "$") -> list[str]:
    """Small JSON-Schema subset validator: type, properties, required, items, enum, additionalProperties,
    minItems/maxItems, minimum/maximum. Enough to catch truncated or malformed model output."""
    errs: list[str] = []
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}
    if t:
        allowed = t if isinstance(t, list) else [t]
        ok = any((isinstance(obj, types[a]) and not (a in ("integer", "number") and isinstance(obj, bool)))
                 or (a == "null" and obj is None) for a in allowed if a in types or a == "null")
        if not ok:
            return [f"{path}: expected {t}, got {type(obj).__name__}"]
    if "enum" in schema and obj not in schema["enum"]:
        errs.append(f"{path}: {obj!r} not in {schema['enum']}")
    if isinstance(obj, dict):
        props = schema.get("properties", {})
        for r in schema.get("required", []):
            if r not in obj:
                errs.append(f"{path}: missing required '{r}'")
        if schema.get("additionalProperties") is False:
            for k in obj:
                if k not in props:
                    errs.append(f"{path}: unexpected key '{k}'")
        for k, v in obj.items():
            if k in props:
                errs += validate(v, props[k], f"{path}.{k}")
    if isinstance(obj, list):
        if "minItems" in schema and len(obj) < schema["minItems"]:
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(obj) > schema["maxItems"]:
            errs.append(f"{path}: more than {schema['maxItems']} items")
        for i, v in enumerate(obj):
            errs += validate(v, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if "minimum" in schema and obj < schema["minimum"]:
            errs.append(f"{path}: {obj} < {schema['minimum']}")
        if "maximum" in schema and obj > schema["maximum"]:
            errs.append(f"{path}: {obj} > {schema['maximum']}")
    return errs


def prompt_hash(step: str, system: str, prompt: str, schema: dict) -> str:
    h = hashlib.sha256()
    for part in (step, system, prompt, json.dumps(schema, sort_keys=True, ensure_ascii=False)):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:24]


@dataclass
class Call:
    step: str
    system: str
    prompt: str
    schema: dict
    effort: str = "high"

    @property
    def key(self) -> str:
        return prompt_hash(self.step, self.system, self.prompt, self.schema)


class Tape:
    """Append-only JSONL record of every judgment call."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, rec: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def lookup(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    if r.get("ok"):
                        out[r["key"]] = r
        return out


# ----------------------------------------------------------------- backends
class Backend:
    name = "base"

    def raw(self, call: Call) -> Any:              # returns parsed JSON
        raise NotImplementedError


class CLIBackend(Backend):
    """`claude -p` headless. Tools are disabled for judgment steps (all inputs are in the prompt), which keeps
    calls cheap, fast and reproducible. Research steps can opt in to tools explicitly."""
    name = "cli"

    def __init__(self, binary: str | None = None, model: str = MODEL, timeout_s: int = 900,
                 allowed_tools: str = "", runner=subprocess.run, add_dirs: list[str] | None = None):
        # allowed_tools: "" (judgment steps), "Read" (look at frames/images in add_dirs), or e.g. "WebSearch,WebFetch"
        self.add_dirs = list(add_dirs or [])
        self.binary = binary or shutil.which("claude") or os.environ.get("CLAUDE_CODE_EXECPATH") or "claude"
        self.model = model
        self.timeout_s = timeout_s
        self.allowed_tools = allowed_tools
        self.runner = runner

    def command(self, call: Call) -> list[str]:
        """Measured on claude 2.1.295: replacing the default Claude Code system prompt (--system-prompt) and
        disabling tools (--tools "") cuts per-call overhead from ~33k to ~1.8k input tokens (19x less usage).
        --bare is NOT used: it skips the subscription login and fails with an authentication error."""
        cmd = [self.binary, "-p", "--output-format", "json", "--model", self.model, "--effort", call.effort,
               "--json-schema", json.dumps(call.schema, ensure_ascii=False),
               "--system-prompt", call.system or "Reply only with the requested JSON."]
        cmd += ["--tools", self.allowed_tools]          # "" = no tools for pure judgment steps
        for d in self.add_dirs:
            cmd += ["--add-dir", d]
        return cmd

    def raw(self, call: Call) -> Any:
        r = self.runner(self.command(call), input=call.prompt, capture_output=True, text=True, timeout=self.timeout_s)
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        blob = (out + " " + err).lower()
        if any(s in blob for s in ("usage limit", "rate limit", "limit reached", "session limit", "usage_limit_reached", "429")):
            raise UsageLimitError((err or out)[-300:])
        if r.returncode != 0:
            raise LLMError(f"claude exited {r.returncode}: {(err or out)[-400:]}")
        try:
            env = json.loads(out)
        except ValueError as e:
            raise LLMError(f"CLI did not return JSON: {out[:300]}") from e
        if isinstance(env, dict) and env.get("is_error"):
            msg = str(env.get("result"))
            if any(x in msg.lower() for x in ("usage limit", "rate limit", "limit reached", "session limit")):
                raise UsageLimitError(msg[:300])
            raise LLMError(f"CLI error: {msg[:300]}")
        if isinstance(env, dict):
            self.last_usage = {"usd_equiv": env.get("total_cost_usd"), "usage": env.get("usage")}
        # structured output: prefer the explicit field, else parse the result text
        if isinstance(env, dict):
            for k in ("structured_output", "structuredOutput"):
                if k in env and env[k] is not None:
                    return env[k]
            res = env.get("result")
            if isinstance(res, (dict, list)):
                return res
            if isinstance(res, str):
                return _json_from_text(res)
        return env


class APIBackend(Backend):
    """Anthropic API (per-token). Streaming + structured outputs + server-side refusal fallback."""
    name = "api"

    def __init__(self, model: str = MODEL, client=None):
        self.model = model
        self._client = client

    def _c(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def raw(self, call: Call) -> Any:
        import anthropic
        try:
            with self._c().beta.messages.stream(
                model=self.model, max_tokens=64000,
                system=call.system or anthropic.NOT_GIVEN,
                messages=[{"role": "user", "content": call.prompt}],
                output_config={"effort": call.effort, "format": {"type": "json_schema", "schema": call.schema}},
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            ) as stream:
                msg = stream.get_final_message()
        except anthropic.RateLimitError as e:
            raise UsageLimitError(str(e)) from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"API {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError(f"network: {e}") from e
        if msg.stop_reason == "refusal":
            raise LLMError(f"refused: {getattr(msg.stop_details, 'category', None)}")
        if msg.stop_reason == "max_tokens":
            raise LLMError("output truncated at max_tokens")
        text = next((b.text for b in msg.content if b.type == "text"), "")
        return json.loads(text)


class RecordedBackend(Backend):
    name = "recorded"

    def __init__(self, tape: Tape):
        self.index = tape.lookup()

    def raw(self, call: Call) -> Any:
        rec = self.index.get(call.key)
        if rec is None:
            raise LLMError(f"no recording for step '{call.step}' (key {call.key}); run with --llm cli once to record it")
        return rec["output"]


def _json_from_text(s: str) -> Any:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(s)
    except ValueError:
        a, b = min((i for i in (s.find("{"), s.find("[")) if i >= 0), default=-1), max(s.rfind("}"), s.rfind("]"))
        if a >= 0 and b > a:
            return json.loads(s[a:b + 1])
        raise LLMError(f"no JSON in model output: {s[:200]}")


# ----------------------------------------------------------------- the client the brain uses
class LLM:
    """resume=True: a step whose exact (step, system, prompt, schema) already succeeded on the tape is replayed
    from it instead of being paid for again. That is what makes a run that was parked by a usage limit continue
    where it stopped when the same command is re-run."""

    def __init__(self, backend: Backend, tape: Tape, retries: int = 1, resume: bool = True):
        self.backend = backend
        self.tape = tape
        self.retries = retries
        self.cache = tape.lookup() if resume and not isinstance(backend, RecordedBackend) else {}
        self.replayed: list[str] = []

    def json(self, step: str, system: str, prompt: str, schema: dict, effort: str = "high") -> Any:
        call = Call(step, system, prompt, schema, effort)
        hit = self.cache.get(call.key)
        if hit is not None and not validate(hit["output"], schema):
            self.replayed.append(step)
            return hit["output"]
        last_errs: list[str] = []
        p = prompt
        for attempt in range(self.retries + 1):
            t0 = time.time()
            c = Call(step, system, p, schema, effort)
            out = self.backend.raw(c if attempt else call)
            errs = validate(out, schema)
            self.tape.append({"step": step, "key": call.key, "backend": self.backend.name, "attempt": attempt,
                              "seconds": round(time.time() - t0, 1), "ok": not errs, "errors": errs[:10],
                              "output": out, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            if not errs:
                return out
            last_errs = errs
            p = prompt + "\n\nYOUR PREVIOUS OUTPUT FAILED VALIDATION:\n- " + "\n- ".join(errs[:15]) + \
                "\nReturn the complete corrected JSON."
        raise LLMError(f"step '{step}': output invalid after {self.retries + 1} attempts: {last_errs[:5]}")


def get_llm(mode: str, tape_path: str | Path, **kw) -> LLM:
    tape = Tape(tape_path)
    if mode == "cli":
        return LLM(CLIBackend(**kw), tape)
    if mode == "api":
        return LLM(APIBackend(**kw), tape)
    if mode == "recorded":
        return LLM(RecordedBackend(tape), tape)
    raise ValueError(f"unknown llm mode {mode!r} (cli | api | recorded)")

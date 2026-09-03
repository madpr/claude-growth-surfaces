#!/usr/bin/env python3
"""
Migration lint for OpenAI Chat Completions payloads moving to Claude.

The problem this exists for is not syntax translation. Anthropic already ships
the mechanical translation: point the OpenAI SDK at https://api.anthropic.com/v1/
and messages, tools and tool_calls are converted server-side.

The problem is that the compatibility layer's documented failure mode is
SILENCE. From the docs:

    "Most unsupported fields are silently ignored rather than producing errors."

Twenty-odd request fields are dropped without an error, a warning, or a response
header. Two of them carry the developer's output contract:

    response_format   Ignored.
    tools[].strict    Ignored -- "the tool use JSON is not guaranteed to
                      follow the supplied schema."

So the evaluation path Anthropic recommends for developers sizing up Claude
("primarily intended to test and compare model capabilities") silently removes
schema enforcement, then returns unenforced JSON. The developer sees malformed
output against a schema that worked on OpenAI and concludes the model is worse.
The model was never asked to conform.

This tool reads the developer's own request payload and reports:

  1. what the compatibility layer will silently drop, ranked by whether it
     actually changes the result,
  2. what the native /v1/messages translation looks like,
  3. which parts of the native translation would be REJECTED by current models
     (sampling parameters and assistant prefill are 400s on Opus 5 and the rest
     of the current generation -- the compat layer hides this by accepting and
     capping them),
  4. whether the JSON Schema in response_format is expressible under native
     structured outputs at all.

Sources, all fetched 1 September 2026:
  https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk
  https://platform.claude.com/docs/en/build-with-claude/structured-outputs
  https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

Stdlib only. Reads a payload as a file argument or on stdin.

    ./migration_lint.py fixtures/support-agent.json
    cat payload.json | ./migration_lint.py --json
    ./migration_lint.py payload.json --translate
    ./migration_lint.py payload.json --target=claude-sonnet-4-6
"""

import json
import sys

# --------------------------------------------------------------------------
# Severity. The point of this scale is that "20 fields are ignored" is not a
# useful finding -- most of them do not change the output. These four do.

BREAKS_CONTRACT = "BREAKS CONTRACT"   # output shape the caller depends on, gone
NATIVE_REJECTS  = "NATIVE REJECTS"    # accepted by compat, 400 on native
CHANGES_RESULT  = "CHANGES RESULT"    # same shape, different content or cost
DROPS_INPUT     = "DROPS INPUT"       # part of the request never reaches Claude
INERT           = "inert"             # ignored, but nothing depends on it

ORDER = [BREAKS_CONTRACT, NATIVE_REJECTS, CHANGES_RESULT, DROPS_INPUT, INERT]

# --------------------------------------------------------------------------
# The compatibility layer's documented handling of every top-level request
# field, transcribed from the support tables in the OpenAI SDK compatibility
# doc. `note` is why it matters; `remedy` is the native equivalent.

FIELDS = {
    "response_format": (
        BREAKS_CONTRACT,
        "Ignored. The structured-output contract is dropped with no error; "
        "Claude returns free-form text against a schema the caller will parse.",
        "Native output_config.format on /v1/messages.",
    ),
    "seed": (
        INERT,
        "Ignored. Reproducibility is not offered.",
        "None. Pin behavior with a fixed prompt and low effort instead.",
    ),
    "logprobs": (INERT, "Ignored; response logprobs are always empty.", "None."),
    "top_logprobs": (INERT, "Ignored.", "None."),
    "logit_bias": (
        CHANGES_RESULT,
        "Ignored. Token-level steering silently stops applying.",
        "Express the constraint in the prompt, or use structured outputs.",
    ),
    "presence_penalty": (
        CHANGES_RESULT,
        "Ignored. Repetition tuning silently stops applying.",
        "Instruct against repetition in the system prompt.",
    ),
    "frequency_penalty": (
        CHANGES_RESULT,
        "Ignored. Repetition tuning silently stops applying.",
        "Instruct against repetition in the system prompt.",
    ),
    "reasoning_effort": (
        CHANGES_RESULT,
        "Ignored. A request tuned for cheap shallow reasoning runs at Claude's "
        "default effort instead, changing both quality and cost.",
        "Native output_config.effort (low | medium | high | xhigh | max).",
    ),
    "prediction": (CHANGES_RESULT, "Ignored. Predicted outputs do not apply.", "None."),
    "metadata": (INERT, "Ignored.", "None."),
    "store": (INERT, "Ignored.", "None."),
    "user": (INERT, "Ignored.", "None."),
    "service_tier": (INERT, "Ignored.", "None."),
    "modalities": (DROPS_INPUT, "Ignored.", "None."),
    "audio": (DROPS_INPUT, "Ignored. Audio input is stripped from the request.", "None."),
}


def _is_current_gen(model):
    """
    Models where sampling parameters and assistant prefill are hard 400s.

    This is the asymmetry that makes the compat layer misleading as an
    evaluation surface: it ACCEPTS temperature (capping >1 to 1) and accepts a
    trailing assistant message. The native API these developers are being
    evaluated for rejects both outright on the current generation.
    """
    m = (model or "").lower()
    current = ("opus-5", "opus-4-8", "opus-4-7", "sonnet-5",
               "fable-5", "mythos-5")
    return any(tag in m for tag in current)


def _rejects_forced_tool_choice(model):
    """tool_choice any/tool return 400 on Fable 5.1 / Mythos 5.1."""
    m = (model or "").lower()
    return "fable-5-1" in m or "mythos-5-1" in m


# --------------------------------------------------------------------------
# Structured outputs accepts a subset of JSON Schema. A response_format that
# OpenAI enforces may not be expressible natively at all -- which is the real
# migration blocker for anyone doing structured extraction, and is invisible
# until you leave the compat layer.

UNSUPPORTED_KEYWORDS = {
    "minimum": "numeric constraints are not supported",
    "maximum": "numeric constraints are not supported",
    "exclusiveMinimum": "numeric constraints are not supported",
    "exclusiveMaximum": "numeric constraints are not supported",
    "multipleOf": "numeric constraints are not supported",
    "minLength": "string length constraints are not supported",
    "maxLength": "string length constraints are not supported",
    "maxItems": "array constraints beyond minItems 0/1 are not supported",
    "uniqueItems": "array constraints beyond minItems 0/1 are not supported",
}


def check_schema(schema, path="$", seen=None, out=None):
    """Walk a JSON Schema and report what native structured outputs rejects."""
    out = [] if out is None else out
    seen = set() if seen is None else seen

    if not isinstance(schema, dict):
        return out

    marker = id(schema)
    if marker in seen:
        out.append((path, "recursive schema; recursion is not supported"))
        return out
    seen = seen | {marker}

    ref = schema.get("$ref")
    if isinstance(ref, str) and not ref.startswith("#"):
        out.append((path, "external $ref is not supported"))

    for kw, why in UNSUPPORTED_KEYWORDS.items():
        if kw in schema:
            out.append((f"{path}.{kw}", why))

    if "minItems" in schema and schema["minItems"] not in (0, 1):
        out.append((f"{path}.minItems", "only minItems 0 or 1 is supported"))

    if schema.get("type") == "object":
        if schema.get("additionalProperties") is not False:
            out.append((path, 'additionalProperties must be set to false'))
        for name, sub in (schema.get("properties") or {}).items():
            check_schema(sub, f"{path}.{name}", seen, out)

    if "items" in schema:
        check_schema(schema["items"], f"{path}[]", seen, out)

    for key in ("anyOf", "oneOf", "allOf"):
        for i, sub in enumerate(schema.get(key) or []):
            check_schema(sub, f"{path}.{key}[{i}]", seen, out)

    enum = schema.get("enum")
    if isinstance(enum, list) and any(isinstance(v, (dict, list)) for v in enum):
        out.append((f"{path}.enum", "complex types in enums are not supported"))

    return out


# --------------------------------------------------------------------------

def lint(payload, target="claude-opus-5"):
    """`target` is the Claude model being migrated TO -- the native-rejection
    checks are properties of that model, not of the OpenAI model in the payload."""
    findings = []

    def add(sev, field, note, remedy):
        findings.append({"severity": sev, "field": field,
                         "note": note, "remedy": remedy})

    model = target

    # Top-level fields the compat layer silently ignores.
    for field, (sev, note, remedy) in FIELDS.items():
        if field in payload:
            add(sev, field, note, remedy)

    # response_format carries a schema worth checking against native limits.
    rf = payload.get("response_format")
    if isinstance(rf, dict) and rf.get("type") == "json_schema":
        schema = (rf.get("json_schema") or {}).get("schema")
        if schema:
            for path, why in check_schema(schema):
                add(BREAKS_CONTRACT, f"response_format schema {path}",
                    f"Not expressible under native structured outputs: {why}.",
                    "Relax the constraint and validate it in your own code after parsing.")

    # n must be exactly 1 -- one of the few that actually errors.
    n = payload.get("n")
    if n is not None and n != 1:
        add(NATIVE_REJECTS, "n",
            f"n={n}. The compatibility layer requires exactly 1.",
            "Issue n separate requests.")

    # temperature is accepted and capped by compat, rejected by current models.
    if "temperature" in payload:
        t = payload["temperature"]
        if _is_current_gen(model):
            add(NATIVE_REJECTS, "temperature",
                f"temperature={t} is accepted by the compatibility layer "
                f"(values >1 capped to 1) but returns 400 on {model}: sampling "
                "parameters were removed on the current generation.",
                "Drop it. Use output_config.effort to trade depth against cost.")
        elif isinstance(t, (int, float)) and t > 1:
            add(CHANGES_RESULT, "temperature",
                f"temperature={t} is silently capped to 1.",
                "Re-tune; the OpenAI range does not carry over.")

    if "top_p" in payload and _is_current_gen(model):
        add(NATIVE_REJECTS, "top_p",
            f"Accepted by the compatibility layer, returns 400 on {model}.",
            "Drop it.")

    # Stop sequences: whitespace-only ones do not work.
    stop = payload.get("stop")
    stops = [stop] if isinstance(stop, str) else (stop or [])
    for s in stops:
        if isinstance(s, str) and s.strip() == "":
            add(CHANGES_RESULT, "stop",
                f"Whitespace-only stop sequence {s!r} does not take effect; "
                "only non-whitespace stop sequences work.",
                "Use a non-whitespace sentinel.")

    # Tools: strict is the second half of the silent contract break.
    for i, tool in enumerate(payload.get("tools") or []):
        fn = tool.get("function") or {}
        if fn.get("strict"):
            add(BREAKS_CONTRACT, f"tools[{i}].strict",
                f"Ignored for {fn.get('name', '?')!r}. Tool-call arguments are "
                "no longer guaranteed to match the schema, with no error raised.",
                "Native tool definitions take strict: true on /v1/messages.")
        params = fn.get("parameters")
        if params:
            for path, why in check_schema(params):
                add(CHANGES_RESULT, f"tools[{i}].parameters {path}",
                    f"Blocks native strict mode: {why}.",
                    "Relax the constraint to make strict: true available natively.")

    # Deprecated functions[] still translate, but flag the drift.
    for i, fn in enumerate(payload.get("functions") or []):
        if fn.get("strict"):
            add(BREAKS_CONTRACT, f"functions[{i}].strict",
                "Ignored, and functions[] is deprecated by OpenAI.",
                "Move to tools[] and set strict: true natively.")

    tc = payload.get("tool_choice")
    forced = tc == "required" or isinstance(tc, dict)
    if forced and _rejects_forced_tool_choice(model):
        add(NATIVE_REJECTS, "tool_choice",
            f"Forced tool choice returns 400 on {model}.",
            "Use auto plus an explicit instruction naming the tool, or "
            "strict: true for schema-valid arguments.")

    # Messages.
    msgs = payload.get("messages") or []
    sys_idx = [i for i, m in enumerate(msgs)
               if m.get("role") in ("system", "developer")]
    if len(sys_idx) > 1:
        add(CHANGES_RESULT, "messages[system]",
            f"{len(sys_idx)} system/developer messages at positions {sys_idx} "
            "are hoisted out of position and concatenated with newlines into a "
            "single leading system message. Mid-conversation instructions that "
            "depended on their position no longer apply where they were placed.",
            "Native mid-conversation system messages keep the position, and "
            "keep the cached prefix intact.")
    elif len(sys_idx) == 1 and sys_idx[0] != 0:
        add(CHANGES_RESULT, "messages[system]",
            f"A system message at position {sys_idx[0]} is hoisted to the front.",
            "Native mid-conversation system messages preserve position.")

    if msgs and msgs[-1].get("role") == "assistant" and _is_current_gen(model):
        add(NATIVE_REJECTS, "messages[-1]",
            f"The request ends with an assistant message. Assistant prefill "
            f"returns 400 on {model}.",
            "Use structured outputs or a system instruction to control format.")

    for i, m in enumerate(msgs):
        content = m.get("content")
        if isinstance(content, list):
            for j, part in enumerate(content):
                t = part.get("type")
                if t == "input_audio":
                    add(DROPS_INPUT, f"messages[{i}].content[{j}]",
                        "Audio input is stripped from the request.", "None.")
                elif t == "file":
                    add(DROPS_INPUT, f"messages[{i}].content[{j}]",
                        "File content blocks are ignored.",
                        "Native Files API, or a document content block.")
                elif t == "image_url" and (part.get("image_url") or {}).get("detail"):
                    add(DROPS_INPUT, f"messages[{i}].content[{j}].detail",
                        "The image detail hint is ignored.", "None.")
        if m.get("name"):
            add(INERT, f"messages[{i}].name", "Ignored on every role.",
                "Fold the name into the message text if it matters.")

    # Prompt caching is unavailable on the compat layer entirely. This one is
    # not a field, so it is never visible in a payload diff -- but for a
    # multi-turn agent with a large stable prefix it dominates the cost
    # comparison the developer is running.
    prefix = len(json.dumps(payload.get("tools") or [])) + \
        sum(len(json.dumps(m)) for m in msgs if m.get("role") in ("system", "developer"))
    if prefix > 2000:
        add(CHANGES_RESULT, "(prompt caching)",
            f"Roughly {prefix} characters of stable system+tools prefix, and "
            "prompt caching is not supported through the compatibility layer. "
            "Any cost comparison run here overstates Claude's cost per call.",
            "Native cache_control breakpoints on /v1/messages.")

    findings.sort(key=lambda f: ORDER.index(f["severity"]))
    return findings


# --------------------------------------------------------------------------

def translate(payload, target="claude-opus-5"):
    """Emit the native /v1/messages equivalent, minus what current models reject."""
    model = target
    out = {"model": model,
           "max_tokens": payload.get("max_tokens")
           or payload.get("max_completion_tokens") or 4096}

    system_parts, messages = [], []
    pending_results = []

    def flush_results():
        if pending_results:
            messages.append({"role": "user", "content": list(pending_results)})
            pending_results.clear()

    for m in payload.get("messages") or []:
        role = m.get("role")
        content = m.get("content")

        if role in ("system", "developer"):
            if isinstance(content, str):
                system_parts.append(content)
            elif isinstance(content, list):
                system_parts += [p.get("text", "") for p in content
                                 if p.get("type") == "text"]
            continue

        if role in ("tool", "function"):
            pending_results.append({
                "type": "tool_result",
                "tool_use_id": m.get("tool_call_id", ""),
                "content": content if isinstance(content, str) else "",
            })
            continue

        flush_results()

        blocks = []
        if isinstance(content, str):
            blocks.append({"type": "text", "text": content})
        elif isinstance(content, list):
            for part in content:
                t = part.get("type")
                if t == "text":
                    blocks.append({"type": "text", "text": part.get("text", "")})
                elif t == "image_url":
                    # Only the url survives; detail is dropped by both paths.
                    blocks.append({"type": "image", "source": {
                        "type": "url",
                        "url": (part.get("image_url") or {}).get("url", "")}})
                # input_audio and file are dropped -- reported by lint().

        for call in m.get("tool_calls") or []:
            fn = call.get("function") or {}
            args = fn.get("arguments")
            try:
                args = json.loads(args) if isinstance(args, str) else (args or {})
            except json.JSONDecodeError:
                args = {}
            blocks.append({"type": "tool_use", "id": call.get("id", ""),
                           "name": fn.get("name", ""), "input": args})

        if blocks:
            messages.append({"role": role, "content": blocks})

    flush_results()

    # The Messages API models a turn as one message per role. Hoisting system
    # messages out of the middle of a transcript can leave two adjacent user
    # messages (a tool_result followed by the next user turn), so merge
    # same-role neighbors into a single message with concatenated blocks.
    merged = []
    for m in messages:
        if merged and merged[-1]["role"] == m["role"]:
            merged[-1]["content"].extend(m["content"])
        else:
            merged.append({"role": m["role"], "content": list(m["content"])})
    messages = merged

    if system_parts:
        out["system"] = "\n".join(system_parts)
    out["messages"] = messages

    tools = []
    for tool in payload.get("tools") or []:
        fn = tool.get("function") or {}
        native = {"name": fn.get("name", ""),
                  "description": fn.get("description", ""),
                  "input_schema": fn.get("parameters") or
                  {"type": "object", "properties": {}}}
        # strict is ignored by the compat layer but is real natively -- and it
        # only holds if the schema is expressible. Do not promise what the
        # schema cannot deliver.
        if fn.get("strict") and not check_schema(native["input_schema"]):
            native["strict"] = True
        tools.append(native)
    if tools:
        out["tools"] = tools

    rf = payload.get("response_format")
    if isinstance(rf, dict) and rf.get("type") == "json_schema":
        schema = (rf.get("json_schema") or {}).get("schema")
        if schema and not check_schema(schema):
            out["output_config"] = {"format": {"type": "json_schema",
                                               "schema": schema}}

    if payload.get("reasoning_effort"):
        mapped = {"minimal": "low", "low": "low", "medium": "medium",
                  "high": "high"}.get(payload["reasoning_effort"], "high")
        out.setdefault("output_config", {})["effort"] = mapped

    stop = payload.get("stop")
    stops = [stop] if isinstance(stop, str) else (stop or [])
    stops = [s for s in stops if isinstance(s, str) and s.strip()]
    if stops:
        out["stop_sequences"] = stops

    # temperature / top_p are deliberately NOT carried over on current models:
    # they are 400s there. lint() reports the omission.
    if not _is_current_gen(model):
        for k in ("temperature", "top_p"):
            if k in payload:
                out[k] = payload[k]

    if payload.get("stream"):
        out["stream"] = True

    return out


# --------------------------------------------------------------------------

def render(payload, findings, target="claude-opus-5"):
    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    print()
    print(f"  {payload.get('model', '(unset)')}  ->  {target}")
    print(f"  {len(payload.get('messages') or [])} messages, "
          f"{len(payload.get('tools') or [])} tools")
    print()

    if not findings:
        print("  Nothing dropped. This payload survives the compatibility layer.")
        print()
        return

    headline = " · ".join(f"{counts[s]} {s.lower()}" for s in ORDER if s in counts)
    print(f"  {headline}")
    print()

    current = None
    for f in findings:
        if f["severity"] != current:
            current = f["severity"]
            print(f"  ── {current} " + "─" * max(0, 58 - len(current)))
        print(f"  {f['field']}")
        for line in _wrap(f["note"], 72):
            print(f"      {line}")
        if f["remedy"] and f["remedy"] != "None.":
            for k, line in enumerate(_wrap(f["remedy"], 68)):
                print(f"      {'→ ' if k == 0 else '  '}{line}")
        print()


def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    target = "claude-opus-5"
    for f in list(flags):
        if f.startswith("--target="):
            target = f.split("=", 1)[1]
            flags.discard(f)

    raw = open(args[0]).read() if args else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: input is not valid JSON ({e})", file=sys.stderr)
        return 2

    findings = lint(payload, target)

    if "--translate" in flags:
        print(json.dumps(translate(payload, target), indent=2))
        return 0
    if "--json" in flags:
        print(json.dumps({"target": target, "findings": findings,
                          "native_request": translate(payload, target)}, indent=2))
        return 0

    render(payload, findings, target)
    blocking = sum(1 for f in findings
                   if f["severity"] in (BREAKS_CONTRACT, NATIVE_REJECTS))
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

import json
import os
import re
import time

import requests

GEMINI_DEFAULT_MODEL = "gemini-3.7-flash"
GEMINI_UNRELATED_MARKER = "UNRELATED"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

GEMINI_FALLBACK_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

GEMINI_EXHAUSTED_TTL_SECONDS = 3600
GEMINI_DEFAULT_TIMEOUT_SECONDS = 10
GEMINI_TOTAL_BUDGET_SECONDS = 18
GEMINI_MAX_OUTPUT_TOKENS = 600


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class GeminiService:
    def __init__(self, api_key=None, api_keys=None, model=None, timeout=None, fallback_models=None, total_budget=None):
        self._api_keys = api_keys
        if api_key is not None:
            self._api_keys = [api_key]
        self._model = model
        self.timeout = timeout if timeout is not None else _env_int(
            "GEMINI_TIMEOUT_SECONDS", GEMINI_DEFAULT_TIMEOUT_SECONDS
        )
        self.total_budget = total_budget if total_budget is not None else _env_int(
            "GEMINI_TOTAL_BUDGET_SECONDS", GEMINI_TOTAL_BUDGET_SECONDS
        )
        self.max_output_tokens = _env_int("GEMINI_MAX_OUTPUT_TOKENS", GEMINI_MAX_OUTPUT_TOKENS)
        self.fallback_models = list(fallback_models or GEMINI_FALLBACK_MODELS)
        self._working_model = None
        self._working_key = None
        self._exhausted = {}
        self._exhausted_ttl = GEMINI_EXHAUSTED_TTL_SECONDS

    @property
    def api_key(self):
        keys = self.api_keys
        return keys[0] if keys else ""

    @property
    def api_keys(self):
        if self._api_keys is not None:
            return [key for key in self._api_keys if key]
        numbered = []
        for var, value in os.environ.items():
            match = re.fullmatch(r"GEMINI_API_KEY_(\d+)", var)
            if match and value:
                numbered.append((int(match.group(1)), value))
        numbered.sort()
        keys = [key for _, key in numbered]
        primary = os.getenv("GEMINI_API_KEY") or ""
        if primary:
            keys.insert(0, primary)
        return keys

    @property
    def model(self):
        if self._model is not None:
            return self._model
        return os.getenv("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL

    def is_available(self):
        return bool(self.api_keys)

    def answer(self, question, context, history=None):
        if not self.is_available():
            return None
        if not (question or "").strip():
            return None
        prompt = self._build_prompt(context, question, history=history)
        text = self._generate(prompt)
        if not text:
            return None
        text = text.strip()
        if GEMINI_UNRELATED_MARKER in text.upper():
            return None
        if self._is_related_marker(text):
            return None
        return text

    def stream_answer(self, question, context, history=None):
        if not self.is_available():
            return
        if not (question or "").strip():
            return
        prompt = self._build_prompt(context, question, history=history)
        pending = ""
        for text in self._generate_stream(prompt):
            if not text:
                continue
            if pending is None:
                yield text
                continue
            pending += text
            if len(pending) < len(GEMINI_UNRELATED_MARKER) + 1:
                continue
            if GEMINI_UNRELATED_MARKER in pending.upper() or self._is_related_marker(pending):
                return
            yield pending
            pending = None
        if pending is not None and pending.strip():
            if GEMINI_UNRELATED_MARKER in pending.upper() or self._is_related_marker(pending):
                return
            yield pending

    def _is_related_marker(self, text):
        return re.sub(r"[^a-z]+", "", (text or "").lower()) in {
            "related",
            "unrelated",
            "notrelated",
            "notunrelated",
        }

    def _build_prompt(self, context, question, history=None):
        history_block = ""
        if history:
            lines = []
            for turn in history:
                role = "User" if turn.get("role") == "user" else "Assistant"
                text = (turn.get("text") or "").strip()
                if text:
                    lines.append(f"{role}: {text}")
            if lines:
                history_block = "\n".join(lines) + "\n\n"
        return (
            "You are the AI assistant inside the chat widget of Joshua Algadipe's "
            "personal portfolio website, and you speak AS Joshua himself. You answer "
            "questions about Joshua, his background, skills, projects, experience, "
            "education, certifications, donations, bookings, and everything shown on the "
            "public pages of this site.\n\n"
            "Below is the full content of the site (knowledge base plus live data). "
            "Use it for everything about Joshua. For questions about the companies "
            "mentioned in the site content (for example Chronostep, TrustArc, or "
            "Teleperformance), you may also use your own knowledge about those "
            "companies.\n\n"
            f"SITE CONTENT:\n{context}\n\n"
            + (f"CONVERSATION SO FAR:\n{history_block}" if history_block else "")
            + "RULES:\n"
            "- ALWAYS speak in first person as Joshua: use 'I', 'me', 'my', 'mine'. "
            "Never refer to Joshua by name or with third-person pronouns like 'he', 'him', "
            "'his', 'Joshua', or 'Joshua Algadipe' in your answers.\n"
            "- Answer ONLY questions related to Joshua, his work, his skills, or this website.\n"
            "- If the question is NOT related to Joshua or this website (for example weather, "
            "news, general knowledge, or unrelated coding help), reply with exactly: "
            f"{GEMINI_UNRELATED_MARKER}\n"
            "- If the site content does not contain the answer, reply with exactly: "
            f"{GEMINI_UNRELATED_MARKER} instead of inventing facts.\n"
            "- For questions about a company mentioned in the site content (for example "
            "Chronostep, TrustArc, or Teleperformance) — the company itself, its purpose, "
            "what it offers, its location, or its services — answer in full detail using "
            "your own knowledge of that company in addition to the site content, and do "
            "not reply with UNRELATED.\n"
            "- If the user's question refers to the previous topic (for example 'how about in "
            "backend' after frontend), continue that topic instead of treating it as unrelated.\n"
            "- When sharing a page link, ALWAYS give the full absolute URL as plain text "
            "(for example https://example.com/donation) using the SITE BASE URL above. Never "
            "use markdown link syntax or relative paths like /donation.\n"
            "- Keep answers concise (1-3 sentences), friendly, and use the same language "
            "as the question when possible. Exception: when asked for full details about "
            "a company (Chronostep, TrustArc, or Teleperformance), give a thorough, "
            "detailed answer.\n\n"
            f"USER QUESTION: {question}"
        )

    def _key_chain(self):
        chain = list(self.api_keys)
        if self._working_key and self._working_key in chain:
            chain.remove(self._working_key)
            chain.insert(0, self._working_key)
        return chain

    def _model_chain(self):
        chain = [self.model]
        for fallback in self.fallback_models:
            if fallback not in chain:
                chain.append(fallback)
        if self._working_model and self._working_model in chain:
            chain.remove(self._working_model)
            chain.insert(0, self._working_model)
        return chain

    def _should_try_next(self, response):
        return 500 <= response.status_code < 600

    def _prune_exhausted(self):
        now = time.time()
        stale = [
            combo for combo, recorded_at in self._exhausted.items()
            if now - recorded_at > self._exhausted_ttl
        ]
        for combo in stale:
            self._exhausted.pop(combo, None)

    def _extract_text(self, response):
        try:
            data = response.json()
            candidates = data.get("candidates") or []
            if not candidates:
                return None
            parts = (candidates[0].get("content") or {}).get("parts") or []
            text_parts = [
                part.get("text", "")
                for part in parts
                if not part.get("thought") and part.get("text")
            ]
            return "".join(text_parts).strip() or None
        except Exception:
            return None

    def _iter_sse_text(self, response):
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            if line.startswith("data:"):
                line = line[5:].strip()
            if not line or line == "[DONE]":
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            candidates = data.get("candidates") or []
            if not candidates:
                continue
            parts = (candidates[0].get("content") or {}).get("parts") or []
            for part in parts:
                if part.get("thought"):
                    continue
                text = part.get("text")
                if text:
                    yield text

    def _generate_stream(self, prompt):
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": self.max_output_tokens,
            },
        }
        self._prune_exhausted()
        deadline = time.time() + self.total_budget
        for model in self._model_chain():
            for key in self._key_chain():
                if time.time() >= deadline:
                    return
                combo = (key, model)
                if combo in self._exhausted:
                    continue
                url = f"{GEMINI_API_BASE}/{model}:streamGenerateContent"
                try:
                    response = requests.post(
                        url,
                        params={"key": key, "alt": "sse"},
                        json=payload,
                        timeout=self.timeout,
                        stream=True,
                    )
                except Exception:
                    continue
                if response.status_code == 200:
                    self._working_model = model
                    self._working_key = key
                    produced = False
                    try:
                        for text in self._iter_sse_text(response):
                            produced = True
                            yield text
                    except Exception:
                        if produced:
                            return
                    finally:
                        try:
                            response.close()
                        except Exception:
                            pass
                    if produced:
                        return
                    continue
                if response.status_code == 429:
                    self._exhausted[combo] = time.time()
                    continue
                if 400 <= response.status_code < 500:
                    break
                if not self._should_try_next(response):
                    return

    def _generate(self, prompt):
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": self.max_output_tokens,
            },
        }
        self._prune_exhausted()
        deadline = time.time() + self.total_budget
        for model in self._model_chain():
            for key in self._key_chain():
                if time.time() >= deadline:
                    return None
                combo = (key, model)
                if combo in self._exhausted:
                    continue
                url = f"{GEMINI_API_BASE}/{model}:generateContent"
                try:
                    response = requests.post(
                        url, params={"key": key}, json=payload, timeout=self.timeout
                    )
                except Exception:
                    continue
                if response.status_code == 200:
                    self._working_model = model
                    self._working_key = key
                    return self._extract_text(response)
                if response.status_code == 429:
                    self._exhausted[combo] = time.time()
                    continue
                if 400 <= response.status_code < 500:
                    break
                if not self._should_try_next(response):
                    return None
        return None

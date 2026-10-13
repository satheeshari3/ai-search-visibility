import os
import time
import logging

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=30000),
)


def generate_text(prompt: str) -> str:
    max_attempts = 3
    retryable_codes = {429, 500, 502, 503, 504}

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            if not response.text or not response.text.strip():
                raise ValueError(
                    "The LLM returned an empty response"
                )

            return response.text.strip()

        except errors.APIError as exc:
            code = getattr(exc, "code", None)

            # Don't retry permanent API errors.
            if (
                code not in retryable_codes
                or attempt == max_attempts - 1
            ):
                logger.exception(
                    "Gemini API request failed: code=%s",
                    code,
                )
                raise

            delay = 2 ** (attempt + 1)

            logger.warning(
                "Gemini temporary API error %s. "
                "Retry %s/%s in %s seconds.",
                code,
                attempt + 1,
                max_attempts - 1,
                delay,
            )

        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == max_attempts - 1:
                logger.exception(
                    "Gemini network request failed after retries"
                )
                raise

            delay = 2 ** (attempt + 1)

            logger.warning(
                "Gemini network failure. "
                "Retry %s/%s in %s seconds.",
                attempt + 1,
                max_attempts - 1,
                delay,
            )

        time.sleep(delay)

    raise RuntimeError("Gemini request failed unexpectedly")
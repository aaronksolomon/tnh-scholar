import logging

from openai import OpenAI
from openai.types.chat import ChatCompletion
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from tnh_scholar.gen_ai_service.models.errors import ProviderError
from tnh_scholar.gen_ai_service.models.transport import ProviderRequest, ProviderResponse
from tnh_scholar.gen_ai_service.providers.base import ProviderClient
from tnh_scholar.gen_ai_service.providers.openai_adapter import OpenAIAdapter
from tnh_scholar.logging_config import get_logger


class OpenAIClient(ProviderClient):
    PROVIDER = "openai"

    def __init__(self, api_key: str | None, organization: str | None):
        """
        Initialize the OpenAIClient with explicit credentials.

        Args:
            api_key: The OpenAI API key.
            organization: The OpenAI organization ID (optional).
        """
        self._client = OpenAI(api_key=api_key, organization=organization)
        self._adapter = OpenAIAdapter()
        import openai  # if not already imported elsewhere
        self.sdk_version = getattr(openai, "__version__", None)
        self._retry_caller = self._create_retry_caller()

    @staticmethod
    def _is_retryable_exception(e):
        status_code = getattr(e, "status_code", None)
        retryable_statuses = (429, 500, 502, 503, 504)
        retryable_names = ("RateLimitError", "APITimeoutError", "APIConnectionError", "APIError")
        return status_code in retryable_statuses or e.__class__.__name__ in retryable_names

    @staticmethod
    def _call_with_retries(retry_caller: Retrying, func, *args, **kwargs):
        """Run `func(*args, **kwargs)` under Tenacity and return (result, attempts)."""
        last_attempt = None
        result = None
        for attempt in retry_caller:
            last_attempt = attempt
            with last_attempt:
                result = func(*args, **kwargs)
        attempts = last_attempt.retry_state.attempt_number if last_attempt else 0
        return result, attempts

    def _create_retry_caller(self):
        return Retrying(
            stop=stop_after_attempt(2),  # exactly one retry (2 total attempts)
            wait=wait_exponential_jitter(initial=0.25, max=1.0),
            retry=retry_if_exception(self._is_retryable_exception),
            reraise=True,
            before_sleep=before_sleep_log(get_logger(__name__), logging.WARNING),
        )

    def _chat_create(self, openai_request) -> ChatCompletion:
        request_kwargs = dict(
            model=openai_request.model,
            messages=openai_request.messages,
            temperature=openai_request.temperature,
            max_completion_tokens=openai_request.max_completion_tokens,
            seed=openai_request.seed,
        )

        if openai_request.response_format is not None:
            return self._client.beta.chat.completions.parse(
                response_format=openai_request.response_format,
                **request_kwargs,
            )

        return self._client.chat.completions.create(**request_kwargs)

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        """
        Generate a response from the OpenAI provider given a ProviderRequest.
        Handles retries and error adaptation.
        """
        try:
            openai_request = self._adapter.to_openai_request(request)

            raw_response, attempts = self._call_with_retries(
                self._retry_caller,
                self._chat_create,
                openai_request,
            )

            if raw_response is None:
                raise ProviderError("OpenAI API call returned no response.")

            return self._adapter.from_openai_response(
                raw_response,
                model=openai_request.model,
                provider=self.PROVIDER,
                attempts=attempts,
            )
            
        except Exception as e:
            # Surface as ProviderError for upstream handling
            raise ProviderError(str(e)) from e

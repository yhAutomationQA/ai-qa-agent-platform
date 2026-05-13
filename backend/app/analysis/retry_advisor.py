from app.analysis.models import (
    RetryRecommendation,
    FailureCategory,
    AnalysisInput,
    FailureCategoryResult,
)


class RetryAdvisor:
    NON_RETRYABLE_CATEGORIES: set[FailureCategory] = {
        FailureCategory.ASSERTION,
        FailureCategory.PERMISSION,
        FailureCategory.INFRASTRUCTURE,
        FailureCategory.DATA,
        FailureCategory.DEPENDENCY,
    }

    ALWAYS_RETRY_CATEGORIES: set[FailureCategory] = {
        FailureCategory.FLAKY,
        FailureCategory.TIMEOUT,
        FailureCategory.NETWORK,
        FailureCategory.ENVIRONMENT,
    }

    RETRYABLE_WITH_CONDITIONS: set[FailureCategory] = {
        FailureCategory.UI,
        FailureCategory.STATE,
        FailureCategory.API,
    }

    def recommend(
        self,
        input_data: AnalysisInput,
        category_result: FailureCategoryResult,
    ) -> RetryRecommendation:
        category = category_result.primary_category

        if category in self.NON_RETRYABLE_CATEGORIES:
            return self._non_retryable(category, input_data)

        if category in self.ALWAYS_RETRY_CATEGORIES:
            return self._always_retry(category, input_data)

        if category in self.RETRYABLE_WITH_CONDITIONS:
            return self._conditional_retry(category, input_data)

        return self._conservative_retry(input_data)

    def _non_retryable(
        self,
        category: FailureCategory,
        input_data: AnalysisInput,
    ) -> RetryRecommendation:
        return RetryRecommendation(
            should_retry=False,
            confidence=0.9,
            reason=f"Non-retryable category: {category.value}. "
            f"Fixing the root cause is required before retrying.",
            suggested_max_retries=0,
            suggested_delay_seconds=0.0,
        )

    def _always_retry(
        self,
        category: FailureCategory,
        input_data: AnalysisInput,
    ) -> RetryRecommendation:
        base_delay = 5.0 if category == FailureCategory.TIMEOUT else 2.0
        max_retries = min(3, max(1, 3 - input_data.retry_count))

        if input_data.retry_count >= 3:
            return RetryRecommendation(
                should_retry=False,
                confidence=0.8,
                reason=f"Already retried {input_data.retry_count} times without success.",
                suggested_max_retries=0,
            )

        return RetryRecommendation(
            should_retry=True,
            confidence=0.75,
            reason=f"Retryable category: {category.value}. "
            f"Likely transient and may succeed on retry.",
            suggested_max_retries=max_retries,
            suggested_delay_seconds=base_delay,
            conditions=[
                "Ensure environment is stable before retry",
                "Check that no deployment is in progress",
            ],
        )

    def _conditional_retry(
        self,
        category: FailureCategory,
        input_data: AnalysisInput,
    ) -> RetryRecommendation:
        is_server_error = (
            input_data.api_status_code and input_data.api_status_code >= 500
        )
        is_ui_loading = (
            input_data.error_message and "loading" in input_data.error_message.lower()
        )

        if is_server_error or is_ui_loading:
            return RetryRecommendation(
                should_retry=True,
                confidence=0.65,
                reason=f"Category {category.value} with transient indicators. "
                f"May benefit from retry.",
                suggested_max_retries=2,
                suggested_delay_seconds=3.0,
                conditions=[
                    "Verify service health before retry",
                    "Increase timeout if timeout-related",
                ],
            )

        return RetryRecommendation(
            should_retry=False,
            confidence=0.6,
            reason=f"Category {category.value} without transient indicators. "
            f"Investigate before retrying.",
            suggested_max_retries=1,
        )

    def _conservative_retry(self, input_data: AnalysisInput) -> RetryRecommendation:
        return RetryRecommendation(
            should_retry=False,
            confidence=0.5,
            reason="Unknown category. Conservative approach: do not retry.",
        )

#!/usr/bin/env python3
"""
Error Handling and Resilience Tests
Tests retry mechanisms, circuit breakers, and error recovery
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock

from src.core.error_handling import (
    ResilienceManager, CircuitBreaker, AsyncRetry, RetryConfig,
    ErrorSeverity, CircuitBreakerState, ErrorContext,
    handle_errors, create_retry_config, with_retry,
    error_boundary, health_checker
)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.cb = CircuitBreaker(failure_threshold=3, recovery_timeout=2)

    @patch('time.time')
    def test_circuit_breaker_states(self, mock_time):
        """Test circuit breaker state transitions"""
        mock_time.return_value = 1000.0

        # Initially closed
        assert self.cb.state == CircuitBreakerState.CLOSED
        assert self.cb.should_attempt()

        # Record failures
        self.cb.record_failure()
        self.cb.record_failure()
        assert self.cb.state == CircuitBreakerState.CLOSED

        # Third failure should open circuit
        self.cb.record_failure()
        assert self.cb.state == CircuitBreakerState.OPEN

        # Should not attempt when open
        assert not self.cb.should_attempt()

        # After recovery timeout, should attempt (half-open)
        mock_time.return_value = 1003.0  # 3 seconds later
        assert self.cb.should_attempt()
        assert self.cb.state == CircuitBreakerState.HALF_OPEN

        # Success should close circuit
        self.cb.record_success()
        assert self.cb.state == CircuitBreakerState.CLOSED

    @patch('time.time')
    def test_recovery_timeout(self, mock_time):
        """Test recovery timeout behavior"""
        mock_time.return_value = 1000.0

        # Open circuit
        for _ in range(3):
            self.cb.record_failure()

        assert self.cb.state == CircuitBreakerState.OPEN

        # Before timeout, should not attempt
        mock_time.return_value = 1001.5  # 1.5 seconds later
        assert not self.cb.should_attempt()

        # After timeout, should attempt
        mock_time.return_value = 1003.0  # 3 seconds later
        assert self.cb.should_attempt()


class TestAsyncRetry:
    """Test async retry functionality"""

    @pytest.mark.asyncio
    async def test_successful_retry(self):
        """Test successful operation without retries"""
        retry = AsyncRetry()

        call_count = 0
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry(successful_operation)()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry on failure"""
        retry_config = RetryConfig(max_attempts=3, base_delay=0.1)
        retry = AsyncRetry(retry_config)

        call_count = 0
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry(failing_operation)()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test max retries exceeded"""
        retry_config = RetryConfig(max_attempts=2, base_delay=0.1)
        retry = AsyncRetry(retry_config)

        call_count = 0
        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent failure")

        with pytest.raises(ValueError, match="Persistent failure"):
            await retry(always_failing_operation)()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff timing"""
        retry_config = RetryConfig(max_attempts=3, base_delay=0.1, exponential_backoff=True)
        retry = AsyncRetry(retry_config)

        call_count = 0
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        start_time = time.time()
        with pytest.raises(ValueError):
            await retry(failing_operation)()
        end_time = time.time()

        # Should have waited approximately 0.1 + 0.2 = 0.3 seconds
        assert end_time - start_time >= 0.2  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_retryable_errors_only(self):
        """Test that only retryable errors are retried"""
        retry_config = RetryConfig(
            max_attempts=3,
            retryable_errors=[ValueError]  # Only retry ValueError
        )
        retry = AsyncRetry(retry_config)

        call_count = 0
        async def operation_with_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable error")
            elif call_count == 2:
                raise RuntimeError("Non-retryable error")
            return "success"

        # Should retry ValueError but not RuntimeError
        with pytest.raises(RuntimeError):
            await retry(operation_with_different_errors)()

        assert call_count == 2


class TestResilienceManager:
    """Test resilience manager functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.manager = ResilienceManager()

    def test_circuit_breaker_creation(self):
        """Test circuit breaker creation"""
        cb = self.manager.get_circuit_breaker("test_operation")
        assert isinstance(cb, CircuitBreaker)
        assert cb.failure_threshold == 5  # Default

    def test_retry_config_management(self):
        """Test retry configuration management"""
        config = RetryConfig(max_attempts=5, base_delay=2.0)
        self.manager.set_retry_config("test_operation", config)

        retrieved = self.manager.get_retry_config("test_operation")
        assert retrieved.max_attempts == 5
        assert retrieved.base_delay == 2.0

    def test_error_recording(self):
        """Test error recording and counting"""
        error = ValueError("Test error")

        # Record error
        self.manager.record_error("test_operation", error)

        # Should create circuit breaker
        cb = self.manager.get_circuit_breaker("test_operation")
        assert cb.failure_count == 1

    def test_multiple_errors(self):
        """Test recording multiple errors"""
        error1 = ValueError("Error 1")
        error2 = RuntimeError("Error 2")

        self.manager.record_error("op1", error1)
        self.manager.record_error("op2", error2)
        self.manager.record_error("op1", error1)  # Second error for op1

        cb1 = self.manager.get_circuit_breaker("op1")
        cb2 = self.manager.get_circuit_breaker("op2")

        assert cb1.failure_count == 2
        assert cb2.failure_count == 1


class TestErrorDecorators:
    """Test error handling decorators"""

    @pytest.mark.asyncio
    async def test_handle_errors_decorator(self):
        """Test handle_errors decorator"""
        @handle_errors("test_operation", "test_component")
        async def test_function():
            return "success"

        result = await test_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_handle_errors_with_exception(self):
        """Test handle_errors decorator with exception"""
        @handle_errors("failing_operation", "test_component")
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

    @pytest.mark.asyncio
    async def test_error_boundary_context_manager(self):
        """Test error boundary context manager"""
        async def test_function():
            async with error_boundary("test_operation", "test_component"):
                return "success"

        result = await test_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_error_boundary_with_exception(self):
        """Test error boundary with exception"""
        async def failing_function():
            async with error_boundary("failing_operation", "test_component"):
                raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()


class TestUtilityFunctions:
    """Test utility functions"""

    def test_create_retry_config(self):
        """Test retry config creation"""
        config = create_retry_config(max_attempts=5, base_delay=1.5)

        assert config.max_attempts == 5
        assert config.base_delay == 1.5
        assert config.exponential_backoff is True  # Default

    def test_create_retry_config_with_errors(self):
        """Test retry config with specific error types"""
        config = create_retry_config(
            max_attempts=3,
            retryable_errors=[ValueError, ConnectionError]
        )

        assert ValueError in config.retryable_errors
        assert ConnectionError in config.retryable_errors
        assert RuntimeError not in config.retryable_errors


class TestHealthChecker:
    """Test health monitoring functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.checker = health_checker

    @pytest.mark.asyncio
    async def test_register_component(self):
        """Test component registration"""
        async def mock_check():
            return {"healthy": True, "message": "OK"}

        self.checker.register_component("test_component", mock_check)

        # Check health
        result = await self.checker.check_health("test_component")
        assert result["healthy"] is True
        assert result["message"] == "OK"

    @pytest.mark.asyncio
    async def test_component_failure(self):
        """Test component health failure"""
        async def failing_check():
            raise ValueError("Component failed")

        self.checker.register_component("failing_component", failing_check)

        result = await self.checker.check_health("failing_component")
        assert result["healthy"] is False
        assert "Component failed" in result["error"]

    @pytest.mark.asyncio
    async def test_system_health(self):
        """Test overall system health"""
        async def healthy_check():
            return {"healthy": True}

        async def failing_check():
            return {"healthy": False, "error": "Failed"}

        self.checker.register_component("healthy", healthy_check)
        self.checker.register_component("failing", failing_check)

        result = await self.checker.get_system_health()
        assert result["healthy"] is False  # Overall unhealthy due to failing component
        assert len(result["components"]) == 2
        assert result["components"]["healthy"]["healthy"] is True
        assert result["components"]["failing"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_unregistered_component(self):
        """Test checking unregistered component"""
        result = await self.checker.check_health("nonexistent")
        assert result["healthy"] is False
        assert "not registered" in result["error"]


class TestErrorContext:
    """Test error context functionality"""

    def test_error_context_creation(self):
        """Test error context creation"""
        context = ErrorContext(
            operation="test_op",
            component="test_comp",
            severity=ErrorSeverity.HIGH,
            retry_count=2
        )

        assert context.operation == "test_op"
        assert context.component == "test_comp"
        assert context.severity == ErrorSeverity.HIGH
        assert context.retry_count == 2
        assert isinstance(context.timestamp, float)
        assert isinstance(context.metadata, dict)

    def test_error_context_defaults(self):
        """Test error context default values"""
        context = ErrorContext(operation="test", component="comp")

        assert context.severity == ErrorSeverity.MEDIUM
        assert context.retry_count == 0
        assert context.max_retries == 3
        assert len(context.metadata) == 0

"""
Tests for AgentExecutor Wrapper (Story 5.1)

AC#1: Agent Framework Initialization
AC#4: Intent-Based Tool Selection
AC#5: Structured Response with Citations
AC#6: Graceful Handling of Unknown Intents
AC#8: Error Handling and Logging
"""

import pytest
from typing import Type
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import BaseModel, Field

from app.services.agent.base import ManufacturingTool, ToolResult, Citation
from app.services.agent.executor import (
    ManufacturingAgent,
    AgentConfig,
    AgentResponse,
    AgentError,
    get_manufacturing_agent,
    reset_agent,
)
from app.services.agent.registry import get_tool_registry


class MockToolInput(BaseModel):
    """Mock input schema for testing."""
    query: str = Field(description="Test query")


class MockExecutorTool(ManufacturingTool):
    """Mock tool for executor tests."""
    name: str = "test_tool"
    description: str = "A test tool that returns mock data"
    args_schema: Type[BaseModel] = MockToolInput

    async def _arun(self, query: str) -> ToolResult:
        return ToolResult(
            data={"query": query, "result": "test data"},
            citations=[
                Citation(source="test", query=query, table="test_table")
            ],
        )


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        with patch.dict("os.environ", {}, clear=True):
            config = AgentConfig()

            assert config.provider == "openai"
            assert config.model == "gpt-4-turbo-preview"
            assert config.temperature == 0.1
            assert config.max_iterations == 5
            assert not config.verbose

    def test_config_from_environment(self):
        """AC#1: Agent is configured via environment variables."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_MODEL": "gpt-4",
            "OPENAI_API_KEY": "test-key",
            "AGENT_TEMPERATURE": "0.5",
            "AGENT_MAX_ITERATIONS": "10",
            "AGENT_VERBOSE": "true",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            config = AgentConfig()

            assert config.provider == "openai"
            assert config.model == "gpt-4"
            assert config.temperature == 0.5
            assert config.max_iterations == 10
            assert config.verbose is True

    def test_config_is_configured_with_key(self):
        """Test is_configured returns True when API key present."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            config = AgentConfig()
            assert config.is_configured is True

    def test_config_is_configured_without_key(self):
        """Test is_configured returns False when API key missing."""
        with patch.dict("os.environ", {}, clear=True):
            config = AgentConfig()
            assert config.is_configured is False


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_response_creation(self):
        """Test AgentResponse can be created."""
        response = AgentResponse(
            content="Test response",
            tool_used="test_tool",
            citations=[],
            suggested_questions=["Follow up?"],
            execution_time_ms=100.5,
        )

        assert response.content == "Test response"
        assert response.tool_used == "test_tool"
        assert response.execution_time_ms == 100.5

    def test_response_with_error(self):
        """Test AgentResponse with error."""
        response = AgentResponse(
            content="Error occurred",
            error="Something went wrong",
        )

        assert response.error == "Something went wrong"


class TestManufacturingAgent:
    """Tests for ManufacturingAgent class."""

    def setup_method(self):
        """Reset agent and registry before each test."""
        reset_agent()
        registry = get_tool_registry()
        registry.clear()

    def test_agent_creation(self):
        """Test ManufacturingAgent can be created."""
        agent = ManufacturingAgent()

        assert not agent.is_initialized

    def test_agent_with_custom_config(self):
        """Test agent with custom configuration."""
        config = AgentConfig()
        agent = ManufacturingAgent(config=config)

        assert agent.config is config

    def test_agent_is_configured_property(self):
        """Test is_configured property."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())
            assert agent.is_configured is True

        with patch.dict("os.environ", {}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())
            assert agent.is_configured is False

    @pytest.mark.asyncio
    async def test_process_message_not_configured(self):
        """AC#8: User receives helpful error message when not configured."""
        with patch.dict("os.environ", {}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())

            response = await agent.process_message(
                message="Test message",
                user_id="test-user",
            )

            assert "not properly configured" in response.content.lower() or response.error is not None

    @pytest.mark.asyncio
    async def test_process_message_with_mocked_executor(self):
        """Test message processing with mocked executor."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())

            # Mock the executor
            mock_result = {
                "output": "Test response about OEE",
                "intermediate_steps": [],
            }

            with patch.object(agent, "_executor") as mock_executor:
                mock_executor.ainvoke = AsyncMock(return_value=mock_result)
                agent._initialized = True

                response = await agent.process_message(
                    message="What is the OEE?",
                    user_id="test-user",
                )

                assert response.content == "Test response about OEE"
                assert response.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_process_message_extracts_citations(self):
        """AC#5: Response includes tool output with citations."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())

            # Create mock action and output with citations
            mock_action = MagicMock()
            mock_action.tool = "test_tool"

            mock_output = ToolResult(
                data={"oee": 87.5},
                citations=[
                    Citation(source="daily_summaries", query="SELECT *", table="daily_summaries")
                ],
            )

            mock_result = {
                "output": "OEE is 87.5%",
                "intermediate_steps": [(mock_action, mock_output)],
            }

            with patch.object(agent, "_executor") as mock_executor:
                mock_executor.ainvoke = AsyncMock(return_value=mock_result)
                agent._initialized = True

                response = await agent.process_message(
                    message="What is the OEE?",
                    user_id="test-user",
                )

                assert response.tool_used == "test_tool"
                assert len(response.citations) == 1
                assert response.citations[0]["source"] == "daily_summaries"

    @pytest.mark.asyncio
    async def test_process_message_with_chat_history(self):
        """Test message processing with chat history."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())

            mock_result = {
                "output": "Based on our previous discussion...",
                "intermediate_steps": [],
            }

            with patch.object(agent, "_executor") as mock_executor:
                mock_executor.ainvoke = AsyncMock(return_value=mock_result)
                agent._initialized = True

                chat_history = [
                    {"role": "user", "content": "What is OEE?"},
                    {"role": "assistant", "content": "OEE stands for..."},
                ]

                response = await agent.process_message(
                    message="How is it calculated?",
                    user_id="test-user",
                    chat_history=chat_history,
                )

                # Verify chat history was converted and passed
                call_args = mock_executor.ainvoke.call_args
                assert "chat_history" in call_args[0][0]
                assert len(call_args[0][0]["chat_history"]) == 2

    @pytest.mark.asyncio
    async def test_process_message_error_handling(self):
        """AC#8: Error is logged and user receives helpful message."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())

            with patch.object(agent, "_executor") as mock_executor:
                mock_executor.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
                agent._initialized = True

                response = await agent.process_message(
                    message="Test message",
                    user_id="test-user",
                )

                assert response.error is not None
                assert "issue" in response.content.lower() or "error" in response.error.lower()

    def test_get_available_capabilities(self):
        """AC#6: Suggests what types of questions it can answer."""
        agent = ManufacturingAgent()

        # Register a test tool
        registry = get_tool_registry()
        registry.register_tool(MockExecutorTool())

        capabilities = agent.get_available_capabilities()

        assert len(capabilities) > 0
        assert any("test" in cap.lower() for cap in capabilities)


class TestAgentInitialization:
    """Tests for agent initialization."""

    def setup_method(self):
        """Reset agent before each test."""
        reset_agent()
        registry = get_tool_registry()
        registry.clear()

    def test_initialize_not_configured(self):
        """Test initialization fails when not configured."""
        with patch.dict("os.environ", {}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())

            result = agent.initialize()

            assert result is False
            assert not agent.is_initialized

    @patch("app.services.agent.executor.AgentExecutor")
    @patch("app.services.agent.executor.ChatOpenAI")
    @patch("app.services.agent.executor.create_openai_functions_agent")
    def test_initialize_success(self, mock_create_agent, mock_chat_openai, mock_executor):
        """AC#1: Creates a LangChain AgentExecutor with OpenAI Functions agent."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_create_agent.return_value = MagicMock()
            mock_executor.return_value = MagicMock()

            agent = ManufacturingAgent(config=AgentConfig())

            # Register a tool for initialization
            registry = get_tool_registry()
            registry.register_tool(MockExecutorTool())

            result = agent.initialize()

            assert result is True
            assert agent.is_initialized
            mock_create_agent.assert_called_once()
            mock_executor.assert_called_once()

    def test_initialize_only_runs_once(self):
        """Test initialization only happens once."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            agent = ManufacturingAgent(config=AgentConfig())
            agent._initialized = True

            result = agent.initialize()

            assert result is True  # Returns True without re-initializing


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def setup_method(self):
        """Reset agent before each test."""
        reset_agent()

    def test_get_manufacturing_agent_singleton(self):
        """Test get_manufacturing_agent returns singleton."""
        agent1 = get_manufacturing_agent()
        agent2 = get_manufacturing_agent()

        assert agent1 is agent2

    def test_reset_agent(self):
        """Test reset_agent clears the singleton."""
        agent1 = get_manufacturing_agent()

        reset_agent()

        agent2 = get_manufacturing_agent()

        assert agent1 is not agent2


class TestAgentError:
    """Tests for AgentError exception."""

    def test_agent_error_creation(self):
        """Test AgentError can be created."""
        error = AgentError("Test error", details={"code": 500})

        assert error.message == "Test error"
        assert error.details == {"code": 500}
        assert str(error) == "Test error"

    def test_agent_error_no_details(self):
        """Test AgentError without details."""
        error = AgentError("Simple error")

        assert error.message == "Simple error"
        assert error.details == {}

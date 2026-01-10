"""
AgentExecutor Wrapper (Story 5.1)

Wraps LangChain AgentExecutor with OpenAI Functions agent for
manufacturing performance queries.

AC#1: Agent Framework Initialization
- Creates a LangChain AgentExecutor with OpenAI Functions agent
- Agent is configured via environment variables
- Agent has access to all registered tools

AC#4: Intent-Based Tool Selection
- Agent selects appropriate tool based on message intent
- Tool is invoked with parsed parameters
- Response includes tool output with citations

AC#6: Graceful Handling of Unknown Intents
- Agent responds honestly when no tool matches
- Suggests what types of questions it can answer
- Never fabricates data or capabilities
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.services.agent.base import Citation, ToolResult
from app.services.agent.registry import get_tool_registry

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Custom exception for agent-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgentConfig:
    """
    Configuration for ManufacturingAgent from environment variables.

    AC#1: Agent is configured via environment variables
    (LLM_PROVIDER, LLM_MODEL, AGENT_TEMPERATURE)
    """

    def __init__(self):
        # LLM Configuration
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

        # Agent-specific configuration
        self.temperature = float(os.getenv("AGENT_TEMPERATURE", "0.1"))
        self.max_iterations = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
        self.verbose = os.getenv("AGENT_VERBOSE", "false").lower() == "true"
        self.timeout_seconds = int(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))

    @property
    def is_configured(self) -> bool:
        """Check if agent is properly configured."""
        if self.provider == "openai":
            return bool(self.openai_api_key)
        return False


class AgentInternalResponse(BaseModel):
    """
    Internal response from ManufacturingAgent.process_message().

    This is the internal service-layer response format.
    The API layer converts this to models.agent.AgentResponse for the API contract.

    AC#5: Structured Response with Citations
    - Response includes citations array
    - Response is suitable for display in chat UI
    """

    content: str = Field(
        ...,
        description="Natural language response from the agent"
    )
    tool_used: Optional[str] = Field(
        None,
        description="Name of the tool that was invoked"
    )
    citations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Data source citations"
    )
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Follow-up questions the user might ask"
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Time taken to process the message in milliseconds"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )


# Backward compatibility alias
AgentResponse = AgentInternalResponse


# System prompt for the agent
AGENT_SYSTEM_PROMPT = """You are a Manufacturing Performance Assistant helping plant managers understand their factory operations. You have access to specialized tools for querying production data.

IMPORTANT RULES:
1. ONLY use the tools available to you - do not make up data or capabilities
2. If you cannot answer a question with available tools, honestly say so and explain what types of questions you CAN answer
3. Always cite the source of your data with timestamps when using tools
4. Be concise but comprehensive in your responses
5. When presenting data, include relevant metrics and context
6. If a tool returns an error, explain the issue clearly to the user

When you cannot help with a request:
- Be honest that the request is outside your capabilities
- List the types of questions you CAN answer based on available tools
- Do NOT fabricate data or pretend to have capabilities you don't have

{tool_descriptions}
"""


class ManufacturingAgent:
    """
    LangChain AgentExecutor wrapper for manufacturing queries.

    AC#1: Creates a LangChain AgentExecutor with OpenAI Functions agent
    AC#4: Selects appropriate tool based on intent
    AC#6: Graceful handling of unknown intents
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the ManufacturingAgent.

        Args:
            config: Optional AgentConfig override
        """
        self.config = config or AgentConfig()
        self._executor: Optional[AgentExecutor] = None
        self._initialized: bool = False

    def initialize(self) -> bool:
        """
        Initialize the agent with LLM and tools.

        AC#1: Agent has access to all registered tools.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        if not self.config.is_configured:
            logger.warning("Agent not configured: missing API key")
            return False

        try:
            # Get LLM client
            llm = self._create_llm()

            # Get registered tools
            registry = get_tool_registry()
            tools = registry.get_tools()

            if not tools:
                logger.warning("No tools registered, agent will have limited functionality")

            # Create the agent
            agent = self._create_agent(llm, tools)

            # Create the executor
            self._executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=self.config.verbose,
                handle_parsing_errors=True,
                max_iterations=self.config.max_iterations,
                return_intermediate_steps=True,
            )

            self._initialized = True
            logger.info(
                f"ManufacturingAgent initialized with {len(tools)} tools: "
                f"{[t.name for t in tools]}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise AgentError(f"Agent initialization failed: {e}")

    def _create_llm(self) -> ChatOpenAI:
        """Create the LLM client."""
        return ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            api_key=self.config.openai_api_key,
            timeout=self.config.timeout_seconds,
        )

    def _create_agent(self, llm: ChatOpenAI, tools: list):
        """
        Create the OpenAI Functions agent.

        AC#1: Creates a LangChain AgentExecutor with OpenAI Functions agent.
        """
        # Build tool descriptions for system prompt
        tool_descriptions = self._build_tool_descriptions(tools)

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", AGENT_SYSTEM_PROMPT.format(tool_descriptions=tool_descriptions)),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create OpenAI Functions agent
        return create_openai_functions_agent(llm, tools, prompt)

    def _build_tool_descriptions(self, tools: list) -> str:
        """Build formatted tool descriptions for the system prompt."""
        if not tools:
            return "No tools are currently available."

        descriptions = ["Available tools and their capabilities:"]
        for tool in tools:
            descriptions.append(f"- **{tool.name}**: {tool.description}")

        return "\n".join(descriptions)

    async def process_message(
        self,
        message: str,
        user_id: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        force_refresh: bool = False,
    ) -> AgentResponse:
        """
        Process a user message and return an agent response.

        AC#4: Agent processes the message and selects appropriate tool.
        AC#5: Response includes tool output with citations.
        AC#6: Handles unknown intents gracefully.

        Args:
            message: User's natural language message
            user_id: User identifier for logging
            chat_history: Optional conversation history
            force_refresh: Bypass cache and fetch fresh data (Story 5.8 AC#5)

        Returns:
            AgentResponse with content, citations, and metadata
        """
        # Story 5.8: Set force_refresh in context for cache decorator to access
        from app.services.agent.cache import set_force_refresh
        set_force_refresh(force_refresh)

        # Story 7.1: Set user_id in context for memory recall tool
        from app.services.agent.tools.memory_recall import set_current_user_id
        set_current_user_id(user_id)

        start_time = time.time()

        # Ensure agent is initialized
        if not self._initialized:
            if not self.initialize():
                return self._create_error_response(
                    "Agent not properly configured. Please check API keys.",
                    start_time
                )

        try:
            # Convert chat history to LangChain format
            lc_chat_history = self._convert_chat_history(chat_history)

            # Invoke the agent
            result = await self._executor.ainvoke({
                "input": message,
                "chat_history": lc_chat_history,
            })

            # Extract and format response
            response = self._format_response(result, start_time)

            logger.info(
                f"Agent processed message for user {user_id}: "
                f"tool={response.tool_used}, "
                f"time={response.execution_time_ms:.2f}ms"
            )

            return response

        except Exception as e:
            logger.error(f"Agent error processing message for user {user_id}: {e}")
            return self._create_error_response(str(e), start_time)

    def _convert_chat_history(
        self,
        chat_history: Optional[List[Dict[str, str]]]
    ) -> List:
        """Convert chat history to LangChain message format."""
        if not chat_history:
            return []

        messages = []
        for msg in chat_history:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        return messages

    def _format_response(
        self,
        result: Dict[str, Any],
        start_time: float
    ) -> AgentResponse:
        """
        Format the agent result into AgentResponse.

        AC#5: Response includes citations from tools.
        """
        execution_time_ms = (time.time() - start_time) * 1000

        # Extract output
        output = result.get("output", "")

        # Extract tool information from intermediate steps
        tool_used = None
        citations = []
        intermediate_steps = result.get("intermediate_steps", [])

        for step in intermediate_steps:
            if len(step) >= 2:
                action, action_output = step[0], step[1]
                tool_used = getattr(action, "tool", None)

                # Extract citations from ToolResult
                if isinstance(action_output, ToolResult):
                    for citation in action_output.citations:
                        citations.append({
                            "source": citation.source,
                            "query": citation.query,
                            "timestamp": citation.timestamp.isoformat(),
                            "table": citation.table,
                            "record_id": citation.record_id,
                            "confidence": citation.confidence,
                            "display_text": citation.to_display_text(),
                        })
                elif isinstance(action_output, str):
                    # Try to parse if it's a string representation
                    pass

        # Generate suggested follow-up questions
        suggested_questions = self._generate_suggestions(tool_used)

        return AgentResponse(
            content=output,
            tool_used=tool_used,
            citations=citations,
            suggested_questions=suggested_questions,
            execution_time_ms=execution_time_ms,
            meta={
                "model": self.config.model,
                "intermediate_steps": len(intermediate_steps),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _generate_suggestions(self, tool_used: Optional[str]) -> List[str]:
        """Generate contextual follow-up question suggestions."""
        # Default suggestions when no tool was used
        if not tool_used:
            registry = get_tool_registry()
            tools = registry.get_tools()
            if tools:
                return [
                    f"Ask me about {tool.name.replace('_', ' ')}"
                    for tool in tools[:3]
                ]
            return ["What questions can you answer?"]

        # Tool-specific suggestions would be added here
        return []

    def _create_error_response(
        self,
        error_message: str,
        start_time: float
    ) -> AgentResponse:
        """
        Create an error response.

        AC#8: User receives a helpful error message.
        """
        execution_time_ms = (time.time() - start_time) * 1000

        return AgentResponse(
            content=(
                "I encountered an issue processing your request. "
                "Please try again or rephrase your question."
            ),
            citations=[],
            suggested_questions=["What questions can you answer?"],
            execution_time_ms=execution_time_ms,
            error=error_message,
            meta={
                "error": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def get_available_capabilities(self) -> List[str]:
        """
        Get list of capabilities based on registered tools.

        AC#6: Suggests what types of questions it can answer.
        """
        registry = get_tool_registry()
        tools = registry.get_tools()

        if not tools:
            return ["No specialized tools are currently available."]

        capabilities = []
        for tool in tools:
            capabilities.append(f"- {tool.description}")

        return capabilities

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized

    @property
    def is_configured(self) -> bool:
        """Check if agent is properly configured."""
        return self.config.is_configured


# Module-level singleton
_agent: Optional[ManufacturingAgent] = None


def get_manufacturing_agent() -> ManufacturingAgent:
    """
    Get the singleton ManufacturingAgent instance.

    Returns:
        ManufacturingAgent instance
    """
    global _agent
    if _agent is None:
        _agent = ManufacturingAgent()
    return _agent


def reset_agent() -> None:
    """
    Reset the singleton agent instance.

    Primarily used for testing.
    """
    global _agent
    _agent = None

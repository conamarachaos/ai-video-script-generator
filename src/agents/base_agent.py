"""Base agent class with Role-Goal-Backstory framework."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from ..models.config import AgentConfig, VideoScriptState


class AgentResponse(BaseModel):
    """Response from an agent."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_user_input: bool = False


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Implements the Role-Goal-Backstory framework.
    """
    
    def __init__(self, config: AgentConfig, llm: BaseChatModel):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
            llm: Language model instance
        """
        self.config = config
        self.llm = llm
        self.role = config.role
        self.name = config.name
        self.description = config.description
        self.goal = config.goal
        self.backstory = config.backstory
        self.tools = config.tools
        
        # Initialize the base prompt template
        self.system_prompt = self._create_system_prompt()
        self.chain = None
        self._setup_chain()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt based on Role-Goal-Backstory."""
        # Check if role is an enum or string
        role_str = self.role.value if hasattr(self.role, 'value') else self.role
        return f"""You are {self.name}, {self.description}.

Role: {role_str}
Goal: {self.goal}
Backstory: {self.backstory}

Guidelines:
1. Always stay in character and maintain your expertise
2. Provide specific, actionable insights based on your specialization
3. Be collaborative and supportive while maintaining objectivity
4. When appropriate, challenge assumptions to improve quality
5. Focus on your specific area of expertise

Remember: You are part of a collaborative team working to create the best possible video script."""
    
    def _setup_chain(self):
        """Set up the LangChain processing chain for Gemini compatibility."""
        # For Gemini, we need to avoid system messages
        # Instead, prepend system context to the human message
        prompt_template = """
{system_context}

User request: {input}
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        self.chain = prompt | self.llm | StrOutputParser()
    
    @abstractmethod
    async def process(self, state: VideoScriptState, 
                     user_input: Optional[str] = None) -> AgentResponse:
        """
        Process the current state and generate a response.
        
        Args:
            state: Current video script state
            user_input: Optional direct user input
            
        Returns:
            Agent response with content and metadata
        """
        pass
    
    def create_prompt(self, template: str, **kwargs) -> str:
        """
        Create a prompt from a template with variables.
        
        Args:
            template: Prompt template with {variable} placeholders
            **kwargs: Variables to fill in the template
            
        Returns:
            Formatted prompt string
        """
        prompt_template = ChatPromptTemplate.from_template(template)
        return prompt_template.format(**kwargs)
    
    async def invoke_llm(self, prompt: str) -> str:
        """
        Invoke the LLM with a prompt.
        
        Args:
            prompt: Input prompt
            
        Returns:
            LLM response as string
        """
        if self.chain:
            return await self.chain.ainvoke({
                "system_context": self.system_prompt,
                "input": prompt
            })
        else:
            # For Gemini compatibility, combine system prompt with user message
            combined_prompt = f"{self.system_prompt}\n\nUser request: {prompt}"
            messages = [
                HumanMessage(content=combined_prompt)
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
    
    def add_to_conversation_history(self, state: VideoScriptState, 
                                   role: str, content: str):
        """
        Add a message to the conversation history.
        
        Args:
            state: Current state
            role: Message role (human/assistant)
            content: Message content
        """
        state.conversation_history.append({
            "role": role,
            "content": content,
            "agent": self.name,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def extract_component_content(self, state: VideoScriptState, 
                                 component_type: str) -> Optional[str]:
        """
        Extract content for a specific script component.
        
        Args:
            state: Current state
            component_type: Type of component (hook/story/cta)
            
        Returns:
            Component content if exists
        """
        component = getattr(state, component_type, None)
        return component.content if component else None
    
    def get_conversation_context(self, state: VideoScriptState, 
                                last_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for context.
        
        Args:
            state: Current state
            last_n: Number of recent messages to retrieve
            
        Returns:
            List of recent conversation entries
        """
        return state.conversation_history[-last_n:] if state.conversation_history else []
    
    def format_suggestions(self, suggestions: List[str]) -> str:
        """
        Format suggestions as a numbered list.
        
        Args:
            suggestions: List of suggestions
            
        Returns:
            Formatted string with numbered suggestions
        """
        if not suggestions:
            return ""
        
        formatted = "Here are some suggestions:\n"
        for i, suggestion in enumerate(suggestions, 1):
            formatted += f"{i}. {suggestion}\n"
        return formatted
    
    def validate_state(self, state: VideoScriptState) -> bool:
        """
        Validate that the state has required information for this agent.
        
        Args:
            state: Current state
            
        Returns:
            True if state is valid for processing
        """
        # Base validation - can be overridden by specific agents
        return state.topic is not None and state.topic.strip() != ""
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}', role='{self.role.value}')"


class SpecializedAgent(BaseAgent):
    """
    Extended base class for specialized agents with additional capabilities.
    """
    
    def __init__(self, config: AgentConfig, llm: BaseChatModel):
        """Initialize specialized agent with additional features."""
        super().__init__(config, llm)
        self.expertise_prompts = self._load_expertise_prompts()
    
    @abstractmethod
    def _load_expertise_prompts(self) -> Dict[str, str]:
        """
        Load specialized prompts for this agent's expertise.
        
        Returns:
            Dictionary of prompt templates
        """
        pass
    
    def get_expertise_prompt(self, prompt_key: str, **kwargs) -> str:
        """
        Get a formatted expertise prompt.
        
        Args:
            prompt_key: Key for the prompt template
            **kwargs: Variables to fill in the template
            
        Returns:
            Formatted prompt string
        """
        template = self.expertise_prompts.get(prompt_key)
        if not template:
            raise ValueError(f"No expertise prompt found for key: {prompt_key}")
        
        return self.create_prompt(template, **kwargs)
    
    async def analyze_quality(self, content: str, criteria: List[str]) -> Dict[str, float]:
        """
        Analyze content quality based on specific criteria.
        
        Args:
            content: Content to analyze
            criteria: List of quality criteria
            
        Returns:
            Dictionary with scores for each criterion
        """
        analysis_prompt = f"""Analyze the following content based on these criteria: {', '.join(criteria)}

Content:
{content}

For each criterion, provide a score from 0.0 to 1.0 and a brief explanation.
Format: criterion: score - explanation"""
        
        response = await self.invoke_llm(analysis_prompt)
        
        # Parse the response into scores
        scores = {}
        for line in response.split('\n'):
            if ':' in line and '-' in line:
                parts = line.split(':')
                if len(parts) == 2:
                    criterion = parts[0].strip()
                    score_part = parts[1].split('-')[0].strip()
                    try:
                        score = float(score_part)
                        scores[criterion] = min(max(score, 0.0), 1.0)
                    except ValueError:
                        continue
        
        return scores
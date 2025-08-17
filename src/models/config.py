"""Configuration models using Pydantic for type safety and validation."""

from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    CLAUDE = "claude"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"


class ModelType(str, Enum):
    """Model types for different tasks."""
    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_SONNET = "claude-3-5-sonnet-20240620"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4_MINI = "gpt-4o-mini"
    GPT_35_TURBO = "gpt-3.5-turbo"
    DEEPSEEK_R1 = "deepseek-reasoner"
    DEEPSEEK_V3 = "deepseek-chat"
    DEEPSEEK_CODER = "deepseek-coder"
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"


class AgentRole(str, Enum):
    """Agent roles in the system."""
    ORCHESTRATOR = "orchestrator"
    HOOK_SPECIALIST = "hook_specialist"
    STORY_ARCHITECT = "story_architect"
    CTA_STRATEGIST = "cta_strategist"
    RESEARCH_ANALYST = "research_analyst"
    STYLIST = "stylist"
    CHALLENGER = "challenger"


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    provider: ModelProvider
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    headers: Optional[Dict[str, str]] = None


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    role: AgentRole
    name: str
    description: str
    goal: str
    backstory: str
    llm_config: ModelConfig  # Renamed from model_config to avoid Pydantic v2 conflict
    tools: List[str] = Field(default_factory=list)


class ScriptComponent(BaseModel):
    """Represents a component of the video script."""
    type: Literal["hook", "story", "cta"]
    content: str
    critique: Optional[str] = None
    finalized: bool = False
    iterations: int = 0
    feedback_history: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    all_options: List[Dict[str, Any]] = Field(default_factory=list)  # For storing accumulated options


class VideoScriptState(BaseModel):
    """Complete state of a video script project."""
    topic: str
    target_audience: Optional[str] = None
    platform: Literal["youtube", "tiktok", "instagram", "general"] = "general"
    duration_seconds: Optional[int] = Field(default=60, gt=0, le=600)
    video_duration: Optional[str] = None  # Formatted duration string (e.g., "10 minutes", "60 seconds")
    
    hook: Optional[ScriptComponent] = None
    story: Optional[ScriptComponent] = None
    cta: Optional[ScriptComponent] = None
    
    user_tone_samples: List[str] = Field(default_factory=list)
    context_documents: List[str] = Field(default_factory=list)
    
    active_module: Literal["hook", "story", "cta", "review", "idle"] = "idle"
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    
    # Model Settings
    default_provider: ModelProvider = Field(default=ModelProvider.CLAUDE, alias="DEFAULT_PROVIDER")
    temperature_creative: float = Field(default=0.8, alias="TEMPERATURE_CREATIVE")
    temperature_analytical: float = Field(default=0.2, alias="TEMPERATURE_ANALYTICAL")
    temperature_standard: float = Field(default=0.5, alias="TEMPERATURE_STANDARD")
    
    # Performance Settings
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    request_timeout: int = Field(default=60, alias="REQUEST_TIMEOUT")
    use_cache: bool = Field(default=True, alias="USE_CACHE")
    use_batch: bool = Field(default=False, alias="USE_BATCH")
    
    # Vector Database Settings
    chroma_persist_dir: str = Field(default="./chroma_db", alias="CHROMA_PERSIST_DIR")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    
    # Application Settings
    debug_mode: bool = Field(default=False, alias="DEBUG_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Default agent configurations
DEFAULT_AGENT_CONFIGS = {
    AgentRole.ORCHESTRATOR: AgentConfig(
        role=AgentRole.ORCHESTRATOR,
        name="Project Director",
        description="Seasoned Creative Director and AI Writing Coach",
        goal="Guide user through video script creation, manage agent collaboration, provide constructive feedback",
        backstory="Trained on thousands of successful video scripts and design thinking principles",
        llm_config=ModelConfig(
            provider=ModelProvider.CLAUDE,
            model=ModelType.CLAUDE_SONNET,
            temperature=0.3,
            max_tokens=4096
        ),
        tools=["state_management", "dialogue_tracking", "agent_routing"]
    ),
    
    AgentRole.HOOK_SPECIALIST: AgentConfig(
        role=AgentRole.HOOK_SPECIALIST,
        name="Attention Expert",
        description="Viral marketing expert specializing in short-form video engagement",
        goal="Generate compelling hooks (3-8 seconds) that capture immediate attention",
        backstory="Trained on high-performing social media videos and psychological studies on viewer retention",
        llm_config=ModelConfig(
            provider=ModelProvider.CLAUDE,
            model=ModelType.CLAUDE_OPUS,
            temperature=0.8,
            max_tokens=2048
        ),
        tools=["hook_templates", "visual_formulas", "platform_best_practices"]
    ),
    
    AgentRole.STORY_ARCHITECT: AgentConfig(
        role=AgentRole.STORY_ARCHITECT,
        name="Narrative Designer",
        description="Professional screenwriter and story structure consultant",
        goal="Structure video narrative with clear beginning, middle, and end",
        backstory="Expert in 3-Act Structure and short-form content adaptation",
        llm_config=ModelConfig(
            provider=ModelProvider.OPENAI,
            model=ModelType.GPT_4_TURBO,
            temperature=0.6,
            max_tokens=4096
        ),
        tools=["story_templates", "narrative_frameworks"]
    ),
    
    AgentRole.CTA_STRATEGIST: AgentConfig(
        role=AgentRole.CTA_STRATEGIST,
        name="Conversion Specialist",
        description="Direct-response marketing and UX specialist",
        goal="Design clear, compelling CTAs that drive viewer action",
        backstory="Trained on A/B test results and psychology of persuasion",
        llm_config=ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model=ModelType.DEEPSEEK_V3,
            temperature=0.4,
            max_tokens=1024
        ),
        tools=["cta_database", "persuasion_techniques"]
    ),
    
    AgentRole.RESEARCH_ANALYST: AgentConfig(
        role=AgentRole.RESEARCH_ANALYST,
        name="Fact-Checker",
        description="Meticulous research librarian and professional fact-checker",
        goal="Retrieve and verify factual information, prevent hallucinations",
        backstory="Built on robust RAG pipeline with source credibility awareness",
        llm_config=ModelConfig(
            provider=ModelProvider.GEMINI,
            model=ModelType.GEMINI_PRO,
            temperature=0.1,
            max_tokens=4096
        ),
        tools=["rag_pipeline", "fact_verification", "source_validation"]
    ),
    
    AgentRole.STYLIST: AgentConfig(
        role=AgentRole.STYLIST,
        name="Voice & Tone Expert",
        description="Master of literary style and brand voice adaptation",
        goal="Ensure script matches user's authentic voice",
        backstory="Specialized in few-shot style transfer",
        llm_config=ModelConfig(
            provider=ModelProvider.CLAUDE,
            model=ModelType.CLAUDE_HAIKU,
            temperature=0.7,
            max_tokens=2048
        ),
        tools=["few_shot_learning", "style_analysis"]
    ),
    
    AgentRole.CHALLENGER: AgentConfig(
        role=AgentRole.CHALLENGER,
        name="Critical Collaborator",
        description="Constructive critic and creative catalyst",
        goal="Challenge assumptions, provide actionable feedback",
        backstory="Designed to combat AI sycophancy and push creative boundaries",
        llm_config=ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model=ModelType.DEEPSEEK_R1,
            temperature=0.5,
            max_tokens=2048
        ),
        tools=["probing_questions", "alternative_suggestions"]
    )
}
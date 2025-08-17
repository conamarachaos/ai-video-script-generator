"""Agent configuration factory to ensure proper model configs."""

from .config import (
    AgentConfig, ModelConfig, AgentRole, ModelProvider, ModelType
)


def get_agent_config(role: AgentRole) -> AgentConfig:
    """Get a fresh agent configuration for the specified role."""
    
    configs = {
        AgentRole.ORCHESTRATOR: AgentConfig(
            role=AgentRole.ORCHESTRATOR,
            name="Project Director",
            description="Seasoned Creative Director and AI Writing Coach",
            goal="Guide user through video script creation, manage agent collaboration, provide constructive feedback",
            backstory="Trained on thousands of successful video scripts and design thinking principles",
            model_config=ModelConfig(
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
            model_config=ModelConfig(
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
            model_config=ModelConfig(
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
            model_config=ModelConfig(
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
            model_config=ModelConfig(
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
            model_config=ModelConfig(
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
            model_config=ModelConfig(
                provider=ModelProvider.DEEPSEEK,
                model=ModelType.DEEPSEEK_R1,
                temperature=0.5,
                max_tokens=2048
            ),
            tools=["probing_questions", "alternative_suggestions"]
        )
    }
    
    return configs.get(role)
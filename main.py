"""Main entry point for the Video Script Generator with multi-provider support."""

import os
import warnings
import logging

# Suppress gRPC and absl warnings BEFORE importing anything else
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
os.environ['GRPC_POLL_STRATEGY'] = 'epoll1'
os.environ['ABSL_MIN_LOG_LEVEL'] = '2'
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Configure logging to suppress warnings
logging.getLogger('absl').setLevel(logging.ERROR)
logging.getLogger('grpc').setLevel(logging.ERROR)
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Filter warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*gRPC.*')
warnings.filterwarnings('ignore', message='.*fork.*')

import asyncio
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.panel import Panel
from typing import Optional
from src.utils.loader import AnimatedLoader, async_loader

from src.models.config import Settings, VideoScriptState, AgentRole, ModelConfig, ModelProvider, AgentConfig
from src.models.model_factory import get_model_factory
from src.models.provider_strategy import ProviderStrategy
from src.agents.orchestrator import OrchestratorAgent
from src.agents.hook_specialist import HookSpecialistAgent
from src.agents.story_architect import StoryArchitectAgent
from src.agents.story_architect_enhanced import EnhancedStoryArchitect
from src.agents.cta_strategist import CTAStrategistAgent
from src.agents.research_analyst import ResearchAnalystAgent
from src.agents.stylist import StylistAgent
from src.agents.challenger import ChallengerAgent
from src.database.session_manager import SessionManager

console = Console()


class VideoScriptCLI:
    """CLI interface for the video script generator."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.settings = Settings()
        self.factory = get_model_factory()
        self.state = None
        self.agents = {}
        self.session_manager = SessionManager()
        self.project_id: Optional[int] = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize available agents with optimal provider for each task."""
        try:
            # Create provider strategy
            strategy = ProviderStrategy(self.factory.available_providers)
            
            console.print("[yellow]Selecting optimal providers for each agent...[/yellow]")
            
            # Get optimal distribution
            distribution = strategy.get_optimal_distribution()
            
            # Show provider assignments for ALL agents
            console.print("\n[cyan]Provider Assignments:[/cyan]")
            displayed_count = 0
            for role, config in distribution.items():
                console.print(f"  {role.value}: [green]{config['provider'].value}/{config['model']}[/green] ({config['reason']})")
                displayed_count += 1
            
            # Show count summary
            if displayed_count < 7:
                console.print(f"\n[dim]Note: {displayed_count} agents shown, others using defaults[/dim]")
            
            # Create Orchestrator with optimal provider
            orch_config = distribution.get(AgentRole.ORCHESTRATOR)
            if not orch_config:
                raise ValueError("No provider available for Orchestrator")
            
            orchestrator_model_config = ModelConfig(
                provider=orch_config['provider'],
                model=orch_config['model'],
                temperature=orch_config['temperature'],
                max_tokens=4096
            )
            orchestrator_config = AgentConfig(
                role=AgentRole.ORCHESTRATOR,
                name="Project Director",
                description="Seasoned Creative Director and AI Writing Coach",
                goal="Guide user through video script creation, manage agent collaboration, provide constructive feedback",
                backstory="Trained on thousands of successful video scripts and design thinking principles",
                llm_config=orchestrator_model_config,
                tools=["state_management", "dialogue_tracking", "agent_routing"]
            )
            orchestrator_llm = self.factory.create_model(orchestrator_model_config)
            self.agents['orchestrator'] = OrchestratorAgent(orchestrator_config, orchestrator_llm)
            
            # Create Hook Specialist with optimal provider
            hook_config_data = distribution.get(AgentRole.HOOK_SPECIALIST)
            if not hook_config_data:
                raise ValueError("No provider available for Hook Specialist")
            
            hook_model_config = ModelConfig(
                provider=hook_config_data['provider'],
                model=hook_config_data['model'],
                temperature=hook_config_data['temperature'],
                max_tokens=2048
            )
            hook_config = AgentConfig(
                role=AgentRole.HOOK_SPECIALIST,
                name="Attention Expert",
                description="Viral marketing expert specializing in short-form video engagement",
                goal="Generate compelling hooks (3-8 seconds) that capture immediate attention",
                backstory="Trained on high-performing social media videos and psychological studies on viewer retention",
                llm_config=hook_model_config,
                tools=["hook_templates", "visual_formulas", "platform_best_practices"]
            )
            hook_llm = self.factory.create_model(hook_model_config)
            self.agents['hook_specialist'] = HookSpecialistAgent(hook_config, hook_llm)
            
            # Create Story Architect with optimal provider
            story_config_data = distribution.get(AgentRole.STORY_ARCHITECT)
            if not story_config_data:
                raise ValueError("No provider available for Story Architect")
            
            story_model_config = ModelConfig(
                provider=story_config_data['provider'],
                model=story_config_data['model'],
                temperature=story_config_data['temperature'],
                max_tokens=4096
            )
            story_config = AgentConfig(
                role=AgentRole.STORY_ARCHITECT,
                name="Narrative Designer",
                description="Master storyteller specializing in video narrative structures",
                goal="Create compelling story arcs that maintain viewer engagement throughout the video",
                backstory="Expert in narrative psychology, story frameworks, and audience retention strategies",
                llm_config=story_model_config,
                tools=["story_frameworks", "narrative_beats", "emotional_mapping"]
            )
            story_llm = self.factory.create_model(story_model_config)
            self.agents['story_architect'] = StoryArchitectAgent(story_config, story_llm)
            
            # Create CTA Strategist with optimal provider
            cta_config_data = distribution.get(AgentRole.CTA_STRATEGIST)
            if not cta_config_data:
                raise ValueError("No provider available for CTA Strategist")
            
            cta_model_config = ModelConfig(
                provider=cta_config_data['provider'],
                model=cta_config_data['model'],
                temperature=cta_config_data['temperature'],
                max_tokens=2048
            )
            cta_config = AgentConfig(
                role=AgentRole.CTA_STRATEGIST,
                name="Conversion Expert",
                description="Conversion optimization specialist for video CTAs",
                goal="Create compelling calls-to-action that drive viewer engagement and conversions",
                backstory="Expert in consumer psychology, persuasion techniques, and platform-specific conversion strategies",
                llm_config=cta_model_config,
                tools=["cta_templates", "urgency_techniques", "ab_testing", "platform_optimization"]
            )
            cta_llm = self.factory.create_model(cta_model_config)
            self.agents['cta_strategist'] = CTAStrategistAgent(cta_config, cta_llm)
            
            # Create Research Analyst Agent
            best_provider = self._get_best_provider()
            research_model = self._get_model_for_provider(best_provider)
            research_model_config = ModelConfig(
                provider=best_provider,
                model=research_model,
                temperature=0.3,  # Lower temperature for factual accuracy
                max_tokens=3072
            )
            research_config = AgentConfig(
                role=AgentRole.ORCHESTRATOR,  # Using ORCHESTRATOR as placeholder
                name="Research Analyst",
                description="Fact-checker and credibility verification specialist",
                goal="Ensure script accuracy through research and fact-checking",
                backstory="Expert in research methods, source verification, and credibility assessment",
                llm_config=research_model_config,
                tools=["fact_checking", "source_verification", "research_databases"]
            )
            research_llm = self.factory.create_model(research_model_config)
            self.agents['research_analyst'] = ResearchAnalystAgent(research_config, research_llm)
            
            # Create Stylist Agent
            stylist_model_config = ModelConfig(
                provider=best_provider,
                model=research_model,  # Use same model as research
                temperature=0.8,  # Higher temperature for creative styling
                max_tokens=3072
            )
            stylist_config = AgentConfig(
                role=AgentRole.ORCHESTRATOR,  # Using ORCHESTRATOR as placeholder
                name="Stylist",
                description="Voice and tone specialist ensuring authentic human sound",
                goal="Make scripts sound natural and platform-appropriate",
                backstory="Expert in linguistics, voice matching, and authentic communication",
                llm_config=stylist_model_config,
                tools=["tone_analysis", "style_matching", "voice_development"]
            )
            stylist_llm = self.factory.create_model(stylist_model_config)
            self.agents['stylist'] = StylistAgent(stylist_config, stylist_llm)
            
            # Create Challenger Agent
            challenger_model_config = ModelConfig(
                provider=best_provider,
                model=research_model,  # Use same model as research
                temperature=0.6,  # Balanced for critical thinking
                max_tokens=3072
            )
            challenger_config = AgentConfig(
                role=AgentRole.ORCHESTRATOR,  # Using ORCHESTRATOR as placeholder
                name="Challenger",
                description="Constructive critic providing valuable feedback",
                goal="Improve script quality through constructive criticism",
                backstory="Expert in content analysis, persuasion psychology, and improvement strategies",
                llm_config=challenger_model_config,
                tools=["critique_framework", "alternative_generation", "improvement_suggestions"]
            )
            challenger_llm = self.factory.create_model(challenger_model_config)
            self.agents['challenger'] = ChallengerAgent(challenger_config, challenger_llm)
            
            console.print("\n[green]✓ All 7 agents initialized with optimal providers![/green]")
            
        except Exception as e:
            console.print(f"[red]Error initializing agents: {e}[/red]")
            console.print("[yellow]Please check your .env file and ensure API keys are set.[/yellow]")
            raise
    
    def _get_best_provider(self) -> ModelProvider:
        """Determine the best available provider based on API key availability and preference."""
        # Check default provider from settings
        default = self.settings.default_provider
        
        # Test if default provider works
        if self.factory.available_providers.get(ModelProvider(default)):
            return ModelProvider(default)
        
        # Priority order: Gemini > Claude > OpenAI > DeepSeek
        priority = [
            ModelProvider.GEMINI,
            ModelProvider.CLAUDE, 
            ModelProvider.OPENAI,
            ModelProvider.DEEPSEEK
        ]
        
        for provider in priority:
            if self.factory.available_providers.get(provider):
                return provider
        
        raise ValueError("No working API providers found. Please check your API keys.")
    
    def _get_model_for_provider(self, provider: ModelProvider) -> str:
        """Get the default model name for a provider."""
        model_map = {
            ModelProvider.OPENAI: "gpt-4",
            ModelProvider.CLAUDE: "claude-3-haiku-20240307",
            ModelProvider.GEMINI: "gemini-1.5-pro",
            ModelProvider.DEEPSEEK: "deepseek-coder"
        }
        return model_map.get(provider, "gpt-4")
    
    def _test_model(self, provider: ModelProvider, model: str) -> bool:
        """Test if a specific model is available."""
        try:
            config = ModelConfig(provider=provider, model=model, temperature=0.1, max_tokens=10)
            llm = self.factory.create_model(config)
            # Simple sync test - just see if model initializes
            return True
        except:
            return False
    
    async def start_new_project(self, skip_menu: bool = False):
        """Start a new video script project."""
        # Show projects menu unless skipped
        if not skip_menu:
            project_id = self.session_manager.show_projects_menu()
            
            if project_id and project_id > 0:
                # Load existing project
                self.project_id = project_id
                self.state = self.session_manager.load_project_state(project_id)
                self.session_manager.show_project_summary(project_id)
                
                # Start interaction loop with loaded state
                await self.interaction_loop()
                return
        
        console.print(Panel.fit(
            "[bold cyan]Welcome to the AI Video Script Generator![/bold cyan]\n"
            "Multi-Provider AI Support\n"
            "Let's create an engaging video script together.",
            border_style="cyan"
        ))
        
        # Get project details
        topic = Prompt.ask("\n[bold]What's your video topic?[/bold]")
        
        platform = Prompt.ask(
            "[bold]Which platform?[/bold]",
            choices=["youtube", "tiktok", "instagram", "general"],
            default="general"
        )
        
        audience = Prompt.ask(
            "[bold]Who's your target audience?[/bold]",
            default="general audience"
        )
        
        # Ask for video duration upfront
        platform_suggestions = {
            'tiktok': '15-60 seconds',
            'instagram': '30 seconds - 2 minutes',
            'youtube': '3-10 minutes',
            'general': '1-5 minutes'
        }
        
        suggested_duration = platform_suggestions.get(platform, '2-3 minutes')
        
        console.print(f"\n[bold]Video Duration[/bold] (Recommended for {platform}: {suggested_duration})")
        duration_input = Prompt.ask(
            "[bold]How long will your video be?[/bold] (e.g., '2 minutes', '60 seconds', '5-7 minutes')",
            default=suggested_duration
        )
        
        # Parse duration input
        import re
        if not duration_input or duration_input.strip() == '':
            duration = suggested_duration
        else:
            # Try to extract duration from input
            duration_match = re.search(r'(\d+(?:-\d+)?\s*(?:second|minute|min|sec|s|m))', duration_input.lower())
            if duration_match:
                duration = duration_match.group(1)
                # Normalize format
                if 'sec' in duration or (duration[-1] == 's' and not duration.endswith('minutes')):
                    duration = re.sub(r'\s*(?:seconds?|secs?|s)', ' seconds', duration)
                else:
                    duration = re.sub(r'\s*(?:minutes?|mins?|m)', ' minutes', duration)
                duration = duration.strip()
            else:
                # Check for bare numbers (assume minutes)
                bare_number_match = re.search(r'^(\d+)(?:-(\d+))?$', duration_input.strip())
                if bare_number_match:
                    if bare_number_match.group(2):  # Range like "5-7"
                        duration = f"{bare_number_match.group(1)}-{bare_number_match.group(2)} minutes"
                    else:  # Single number like "10"
                        duration = f"{bare_number_match.group(1)} minutes"
                else:
                    duration = suggested_duration
        
        # Initialize state
        self.state = VideoScriptState(
            topic=topic,
            platform=platform,
            target_audience=audience
        )
        
        # Store duration in state for all agents to use
        self.state.video_duration = duration
        
        # Always create project in database (auto-save everything)
        self.project_id = self.session_manager.create_new_project(
            topic=topic,
            platform=platform,
            target_audience=audience,
            video_duration=duration
        )
        
        console.print(f"\n[green]Project initialized![/green]")
        console.print(f"Topic: [bold]{topic}[/bold]")
        console.print(f"Platform: [bold]{platform}[/bold]")
        console.print(f"Audience: [bold]{audience}[/bold]")
        console.print(f"Duration: [bold]{duration}[/bold]\n")
        
        # Show clear instructions
        console.print("[green]✅ Project initialized successfully![/green]\n")
        console.print("[bold yellow]Quick Start Commands:[/bold yellow]")
        console.print("  • Type [bold cyan]hook[/bold cyan] to create video openings")
        console.print("  • Type [bold cyan]story[/bold cyan] to develop narrative structure")
        console.print("  • Type [bold cyan]cta[/bold cyan] to design call-to-action")
        console.print("\n[bold yellow]Quality Enhancement:[/bold yellow]")
        console.print("  • Type [bold cyan]research[/bold cyan] for fact-checking")
        console.print("  • Type [bold cyan]humanize[/bold cyan] to sound natural")
        console.print("  • Type [bold cyan]critique[/bold cyan] for feedback")
        console.print("\n  • Type [bold cyan]help[/bold cyan] for all commands")
        console.print("  • Type [bold cyan]exit[/bold cyan] to quit\n")
        
        # Start interaction loop
        await self.interaction_loop()
    
    async def interaction_loop(self):
        """Main interaction loop."""
        orchestrator = self.agents['orchestrator']
        
        # Auto-save function
        async def auto_save():
            """Auto-save state after every interaction."""
            if self.project_id:
                self.session_manager.save_state(self.state, self.project_id)
                # Silent save - no notification to avoid spam
        
        # Initial greeting from orchestrator - now with clear command guidance
        initial_response = await orchestrator.process(self.state, None)
        self._display_response(initial_response, "Orchestrator")
        
        while True:
            # Get user input
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            
            if user_input.lower() == 'exit':
                # Save before exiting
                if self.project_id:
                    self.session_manager.save_state(self.state, self.project_id)
                    console.print("\n[green]Project saved! See you next time![/green]")
                break
            elif user_input.lower() == 'help':
                self._show_help()
                continue
            elif user_input.lower() == 'status':
                self._show_status()
                continue
            elif user_input.lower() == 'save':
                # Manual save (though auto-save handles it)
                if self.project_id:
                    self.session_manager.save_state(self.state, self.project_id)
                    console.print("[green]✓ Project saved successfully![/green]")
                continue
            elif user_input.lower() == 'export':
                # Export script
                await self._export_script()
                continue
            elif user_input.lower() == 'list':
                # List projects
                await self._list_projects()
                continue
            elif user_input.lower() in ['hook', 'hooks']:
                # Direct request for hooks
                await self._generate_hooks()
                continue
            elif user_input.lower() in ['story', 'narrative', 'structure']:
                # Direct request for story structure
                await self._generate_story()
                continue
            
            # Check if we're awaiting a mood response
            if self.state.conversation_history and self.state.conversation_history[-1].get('type') == 'awaiting_mood_response':
                # This is a response to the mood question
                await self._generate_story(user_mood_input=user_input)
                continue
            
            # Check if we're awaiting timing preference
            if hasattr(self.state, 'story') and self.state.story and self.state.story.metadata.get('awaiting_timing'):
                # Handle timing preference
                duration = EnhancedStoryArchitect.handle_timing_preference(self.state, user_input)
                console.print(f"\n[green]✓ Got it! Creating a {duration} video structure[/green]\n")
                # Mark that we've already handled mood
                self.state.story.metadata['mood_handled'] = True
                # Don't ask for mood again, just generate the story
                await self._generate_story(skip_mood_check=True)
                continue
            
            # Check for option selection FIRST (e.g., "choose option 1", "option 2", "use option 3", or just "1", "2", "3")
            # This must come before act development mode to handle CTA selection properly
            option_selected = self._parse_option_selection(user_input)
            if option_selected:
                await self._handle_option_selection(option_selected)
                await auto_save()  # Auto-save after selection
                continue
            
            # Check if we're in CTA interaction mode (after CTA generation)
            last_cta_generation = False
            for item in reversed(self.state.conversation_history[-3:]):  # Check last 3 items
                if item.get('type') == 'ctas_generated':
                    last_cta_generation = True
                    break
            
            # If we just generated CTAs and user is typing commands, route to CTA strategist
            if last_cta_generation and any(word in user_input.lower() for word in ['optimize', 'urgency', 'variant', 'youtube', 'tiktok', 'instagram', 'softer']):
                # Route to CTA strategist for optimization
                await self._handle_cta_followup(user_input)
                continue
            
            # Check for global commands (before act development mode)
            if user_input.lower() in ['cta', 'call to action', 'action']:
                # Direct request for CTA
                await self._generate_cta()
                continue
            elif user_input.lower() in ['research', 'verify', 'fact-check', 'fact check']:
                # Direct request for research/fact-checking
                await self._research_analysis()
                continue
            elif user_input.lower() in ['humanize', 'style', 'tone', 'voice']:
                # Direct request for styling
                await self._style_content()
                continue
            elif user_input.lower() in ['critique', 'review', 'challenge', 'feedback']:
                # Direct request for critique
                await self._challenge_content()
                continue
            elif user_input.lower().startswith('edit hook'):
                # Edit existing hook
                await self._edit_component('hook', user_input)
                continue
            elif user_input.lower().startswith('edit story'):
                # Edit existing story
                await self._edit_component('story', user_input)
                continue
            elif user_input.lower().startswith('edit cta'):
                # Edit existing CTA
                await self._edit_component('cta', user_input)
                continue
            
            # Check if we're in act development mode (AFTER option selection and global commands)
            if hasattr(self.state, 'story') and self.state.story and self.state.story.metadata.get('workflow_mode') == 'act_development':
                # Process act development commands
                story_architect = self.agents.get('story_architect')
                if story_architect:
                    loader = AnimatedLoader(console)
                    with loader.loading("✍️ Processing your act content...", "dots12"):
                        response = await EnhancedStoryArchitect.process_act_development(story_architect, self.state, user_input)
                    self._display_response(response, "Story Architect")
                    await auto_save()  # Auto-save after act development
                continue
            
            # Check for "more" command to generate more options
            if user_input.lower() in ['more', 'more options', 'different', 'other', 'alternative']:
                await self._generate_more_options()
                continue
            
            # Check for "custom" command
            if user_input.lower().startswith(('custom', 'my own', 'use this')):
                await self._handle_custom_content(user_input)
                continue
            
            # Process with orchestrator
            try:
                loader = AnimatedLoader(console)
                with loader.loading("🤖 Processing your request...", "dots12"):
                    response = await orchestrator.process(self.state, user_input)
                self._display_response(response, "Orchestrator")
                
                # Check if we need to route to another agent
                if response.metadata.get('next_agent') == 'hook_specialist':
                    await self._generate_hooks()
                elif response.metadata.get('next_agent') == 'story_architect':
                    await self._generate_story()
                elif response.metadata.get('next_agent') == 'cta_strategist':
                    await self._generate_cta()
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                if self.settings.debug_mode:
                    console.print_exception()
    
    def _parse_option_selection(self, user_input: str) -> Optional[int]:
        """Parse user input to detect option selection.
        
        Args:
            user_input: User's input string
            
        Returns:
            Option number (1, 2, or 3) or None if not an option selection
        """
        import re
        
        input_lower = user_input.lower().strip()
        
        # Don't parse as option if it's a draft command or other known commands
        if (input_lower.startswith('draft:') or 
            input_lower.startswith('draft ') or
            input_lower.startswith('enhance') or
            input_lower.startswith('research:') or
            input_lower.startswith('example:') or
            len(user_input) > 50):  # Long inputs are likely content, not selections
            return None
        
        # Patterns to match option selection
        patterns = [
            r'choose option (\d)',
            r'option (\d)',
            r'use option (\d)',
            r'select option (\d)',
            r'go with option (\d)',
            r'let\'s use option (\d)',
            r'^(\d)$',  # Just the number
            r'option number (\d)',
            r'number (\d)',
            r'#(\d)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, input_lower)
            if match:
                option_num = int(match.group(1))
                if 1 <= option_num <= 3:
                    return option_num
        
        # Check for words - but only as standalone words or at word boundaries
        # AND only for short inputs (to avoid matching content)
        # This prevents "alone" from matching "one", "second" from matching "two", etc.
        if len(input_lower) <= 20:  # Only check word patterns for short inputs
            word_patterns = [
                (r'\b(first|one)\b', 1),
                (r'\b(second|two)\b', 2),
                (r'\b(third|three)\b', 3)
            ]
            
            for pattern, num in word_patterns:
                if re.search(pattern, input_lower):
                    return num
        
        return None
    
    async def _handle_option_selection(self, option_num: int):
        """Handle when user selects an option.
        
        Args:
            option_num: The option number selected (1, 2, or 3)
        """
        # Look for the most recent options in conversation history
        recent_options = None
        option_type = None
        
        for item in reversed(self.state.conversation_history):
            if item.get('type') == 'hooks_generated':
                recent_options = item.get('options', [])
                option_type = 'hook'
                break
            elif item.get('type') == 'ctas_generated':
                recent_options = item.get('options', [])
                option_type = 'cta'
                break
            elif item.get('type') == 'stories_generated':
                recent_options = item.get('options', [])
                option_type = 'story'
                break
        
        if recent_options and len(recent_options) >= option_num:
            selected = recent_options[option_num - 1]
            
            # Update the state with the selected option
            if option_type == 'hook':
                # Initialize hook if it doesn't exist
                if not self.state.hook:
                    from src.models.config import ScriptComponent
                    self.state.hook = ScriptComponent(type="hook", content="", finalized=False)
                # Now update it
                self.state.hook.content = selected.get('text', '')
                self.state.hook.finalized = True
                # Mark that hook was just selected
                self.state.conversation_history.append({
                    'type': 'hook_selected',
                    'option_num': option_num
                })
                console.print(f"\n[green]✅ Great choice! Option {option_num} selected for your hook:[/green]")
                console.print(f'[italic]"{selected.get("text", "")}"[/italic]\n')
                console.print("[yellow]What would you like to work on next?[/yellow]")
                console.print("  • Type [cyan]story[/cyan] to develop the narrative")
                console.print("  • Type [cyan]cta[/cyan] to create your call-to-action")
            elif option_type == 'cta':
                # Initialize CTA if it doesn't exist
                if not self.state.cta:
                    from src.models.config import ScriptComponent
                    self.state.cta = ScriptComponent(type="cta", content="", finalized=False)
                self.state.cta.content = selected.get('primary_text', selected.get('text', ''))
                self.state.cta.finalized = True
                console.print(f"\n[green]✅ Perfect! Option {option_num} selected for your CTA:[/green]")
                console.print(f'[italic]"{self.state.cta.content}"[/italic]\n')
                
                # Check if script is now complete
                if self.state.hook and self.state.hook.content and self.state.story and self.state.story.content:
                    console.print("[yellow]🎉 Your script is complete! What would you like to do?[/yellow]")
                    console.print("  • Type [cyan]review[/cyan] to see complete script and get feedback")
                    console.print("  • Type [cyan]export[/cyan] to save your script to a file")
                    console.print("  • Type [cyan]humanize[/cyan] to make it sound more natural")
                    console.print("  • Type [cyan]status[/cyan] to see detailed progress")
                else:
                    console.print("[yellow]What would you like to work on next?[/yellow]")
                    console.print("  • Type [cyan]status[/cyan] to review your progress")
                    console.print("  • Type [cyan]review[/cyan] to see complete script")
            elif option_type == 'story':
                # Initialize story if it doesn't exist
                if not self.state.story:
                    from src.models.config import ScriptComponent
                    self.state.story = ScriptComponent(type="story", content="", finalized=False)
                self.state.story.content = selected.get('structure', selected.get('content', ''))
                self.state.story.finalized = True
                console.print(f"\n[green]✅ Excellent! Option {option_num} selected for your story structure.[/green]\n")
                console.print("[yellow]What would you like to work on next?[/yellow]")
                console.print("  • Type [cyan]cta[/cyan] to create your call-to-action")
                console.print("  • Type [cyan]review[/cyan] to see what you have so far")
        else:
            console.print(f"\n[yellow]No recent options to select from. Please generate content first:[/yellow]")
            console.print("  • Type [cyan]hook[/cyan] for video openings")
            console.print("  • Type [cyan]story[/cyan] for narrative structure")
            console.print("  • Type [cyan]cta[/cyan] for call-to-action")
    
    async def _generate_hooks(self):
        """Generate hooks using the Hook Specialist."""
        if 'hook_specialist' in self.agents:
            console.print(f"\n[dim]→ Connecting to Hook Specialist...[/dim]")
            hook_specialist = self.agents['hook_specialist']
            
            # Show loader during API call
            loader = AnimatedLoader(console)
            with loader.loading("🎨 Creating compelling hooks for your video...", "dots12"):
                hook_response = await hook_specialist.process(self.state)
            
            self._display_response(hook_response, hook_specialist.name)
            # Store the options for selection
            if hook_response.metadata and 'hooks' in hook_response.metadata:
                self.state.conversation_history.append({
                    'type': 'hooks_generated',
                    'options': hook_response.metadata['hooks']
                })
        else:
            console.print("[red]Hook Specialist not available[/red]")
    
    async def _generate_story(self, user_mood_input=None, skip_mood_check=False):
        """Generate story structure using the Story Architect.
        
        Args:
            user_mood_input: Optional user input about mood/emotional journey
            skip_mood_check: Skip the mood question if already handled
        """
        if 'story_architect' in self.agents:
            console.print(f"\n[dim]→ Connecting to Story Architect...[/dim]")
            story_architect = self.agents['story_architect']
            
            # Check if hook was just selected to ask follow-up question
            hook_just_selected = False
            awaiting_mood_response = False
            
            if len(self.state.conversation_history) >= 1:
                # Check if we're awaiting a mood response
                last_item = self.state.conversation_history[-1] if self.state.conversation_history else None
                if last_item and last_item.get('type') == 'awaiting_mood_response':
                    awaiting_mood_response = True
                    # Remove the awaiting flag
                    self.state.conversation_history.pop()
                
                # Check if the last action was hook selection
                for i in range(len(self.state.conversation_history) - 1, max(0, len(self.state.conversation_history) - 3), -1):
                    if self.state.conversation_history[i].get('type') == 'hook_selected':
                        hook_just_selected = True
                        break
            
            # If hook was just selected and no mood input yet, ask the follow-up question
            # But skip if we've already handled mood (e.g., after timing question)
            mood_already_handled = self.state.story and self.state.story.metadata.get('mood_handled', False)
            
            if hook_just_selected and not user_mood_input and not awaiting_mood_response and not skip_mood_check and not mood_already_handled and self.state.hook and self.state.hook.content:
                console.print("\n[bold magenta]Story Architect:[/bold magenta]")
                console.print("\n[yellow]Great hook choice! Now that you've selected your opening, let me ask you a quick question to shape your story:[/yellow]\n")
                console.print("[bold]What mood or emotional journey do you want your viewers to experience?[/bold]\n")
                console.print("For example:")
                console.print("  • [cyan]Curious → Enlightened[/cyan] (educational content)")
                console.print("  • [cyan]Frustrated → Empowered[/cyan] (problem-solving)")
                console.print("  • [cyan]Skeptical → Convinced[/cyan] (persuasive content)")
                console.print("  • [cyan]Entertained → Inspired[/cyan] (motivational)\n")
                console.print("[dim]Type your answer or press Enter to skip and generate story options[/dim]")
                # Mark that we're awaiting a mood response
                self.state.conversation_history.append({'type': 'awaiting_mood_response'})
                return
            
            # Initialize story component if it doesn't exist
            if not self.state.story:
                from src.models.config import ScriptComponent
                self.state.story = ScriptComponent(type="story", content="", finalized=False)
            
            # Use video duration from state if already set during initialization
            if hasattr(self.state, 'video_duration') and self.state.video_duration:
                self.state.story.metadata['video_duration'] = self.state.video_duration
            # Otherwise check if we need to ask about video timing (for backward compatibility)
            elif not self.state.story.metadata.get('video_duration') and not self.state.story.metadata.get('awaiting_timing'):
                # Ask about timing preference
                timing_response = EnhancedStoryArchitect.ask_about_timing(self.state)
                self._display_response(timing_response, "Story Architect")
                return
            
            # If we have mood input, pass it to the story architect
            if user_mood_input:
                # Add mood preference to state context
                if not hasattr(self.state, 'mood_preference'):
                    self.state.context_documents.append(f"User's preferred emotional journey: {user_mood_input}")
                console.print(f"\n[green]✓ Got it! Creating a story with {user_mood_input} emotional journey[/green]\n")
            
            # Generate the story structure with loader
            loader = AnimatedLoader(console)
            with loader.loading("🎬 Architecting your story structure...", "dots12"):
                story_response = await story_architect.process(self.state, user_mood_input)
            
            # If we have a duration set, add act development prompt
            if self.state.story.metadata.get('video_duration'):
                duration = self.state.story.metadata['video_duration']
                # Mark workflow mode
                self.state.story.metadata['workflow_mode'] = 'act_development'
                self.state.story.metadata['current_act'] = 1
                self.state.story.metadata['acts_content'] = {}
                
                # Add act development prompt to the response
                act_prompt = EnhancedStoryArchitect.create_act_development_prompt(self.state, duration, 1)
                story_response.content += act_prompt
            
            self._display_response(story_response, story_architect.name)
            # Store options for selection
            if story_response.metadata and 'story_structure' in story_response.metadata:
                self.state.conversation_history.append({
                    'type': 'stories_generated',
                    'options': [story_response.metadata['story_structure']]
                })
        else:
            console.print("[red]Story Architect not available[/red]")
    
    async def _generate_cta(self):
        """Generate CTAs using the CTA Strategist."""
        if 'cta_strategist' in self.agents:
            console.print(f"\n[dim]→ Connecting to CTA Strategist...[/dim]")
            cta_strategist = self.agents['cta_strategist']
            
            # Show loader during API call
            loader = AnimatedLoader(console)
            with loader.loading("🎯 Designing compelling call-to-action...", "dots12"):
                cta_response = await cta_strategist.process(self.state)
            
            self._display_response(cta_response, cta_strategist.name)
            # Store options for selection
            if cta_response.metadata and 'ctas' in cta_response.metadata:
                self.state.conversation_history.append({
                    'type': 'ctas_generated',
                    'options': cta_response.metadata['ctas']
                })
        else:
            console.print("[red]CTA Strategist not available[/red]")
    
    async def _handle_cta_followup(self, user_input: str):
        """Handle CTA optimization and variants."""
        if 'cta_strategist' in self.agents:
            console.print(f"\n[dim]→ Processing CTA optimization...[/dim]")
            cta_strategist = self.agents['cta_strategist']
            
            # Show loader during API call
            loader = AnimatedLoader(console)
            with loader.loading("✨ Optimizing your CTA...", "dots12"):
                cta_response = await cta_strategist.process(self.state, user_input)
            
            self._display_response(cta_response, cta_strategist.name)
            # Update options if new ones generated
            if cta_response.metadata and 'ctas' in cta_response.metadata:
                self.state.conversation_history.append({
                    'type': 'ctas_generated',
                    'options': cta_response.metadata['ctas']
                })
        else:
            console.print("[red]CTA Strategist not available[/red]")
    
    async def _research_analysis(self, user_input: Optional[str] = None):
        """Perform research and fact-checking using Research Analyst."""
        if 'research_analyst' in self.agents:
            console.print(f"\n[dim]→ Connecting to Research Analyst...[/dim]")
            research_analyst = self.agents['research_analyst']
            
            # Show loader during API call
            loader = AnimatedLoader(console)
            with loader.loading("🔍 Researching and verifying facts...", "dots12"):
                research_response = await research_analyst.process(self.state, user_input)
            
            self._display_response(research_response, research_analyst.name)
        else:
            console.print("[red]Research Analyst not available[/red]")
    
    async def _style_content(self, user_input: Optional[str] = None):
        """Style and humanize content using Stylist."""
        if 'stylist' in self.agents:
            console.print(f"\n[dim]→ Connecting to Stylist...[/dim]")
            stylist = self.agents['stylist']
            
            # Show loader during API call
            loader = AnimatedLoader(console)
            with loader.loading("✍️ Styling and humanizing content...", "dots12"):
                style_response = await stylist.process(self.state, user_input)
            
            self._display_response(style_response, stylist.name)
        else:
            console.print("[red]Stylist not available[/red]")
    
    async def _challenge_content(self, user_input: Optional[str] = None):
        """Challenge and critique content using Challenger."""
        if 'challenger' in self.agents:
            console.print(f"\n[dim]→ Connecting to Challenger...[/dim]")
            challenger = self.agents['challenger']
            
            # Show loader during API call
            loader = AnimatedLoader(console)
            with loader.loading("🎯 Providing constructive critique...", "dots12"):
                challenge_response = await challenger.process(self.state, user_input)
            
            self._display_response(challenge_response, challenger.name)
        else:
            console.print("[red]Challenger not available[/red]")
    
    async def _enhance_option(self, user_input: str):
        """Enhance a specific option.
        
        Args:
            user_input: User's input containing enhance request
        """
        # Find the most recent component type
        recent_type = None
        for item in reversed(self.state.conversation_history):
            if item.get('type') in ['hooks_generated', 'ctas_generated', 'stories_generated']:
                recent_type = item.get('type')
                break
        
        if recent_type == 'hooks_generated' and 'hook_specialist' in self.agents:
            # Pass through to hook specialist for enhancement
            console.print(f"\n[dim]→ Enhancing option...[/dim]")
            hook_specialist = self.agents['hook_specialist']
            
            loader = AnimatedLoader(console)
            with loader.loading("✨ Enhancing your selected option...", "dots12"):
                response = await hook_specialist.process(self.state, user_input)
            
            self._display_response(response, hook_specialist.name)
        else:
            console.print("\n[yellow]Please generate content first before enhancing options.[/yellow]")
            console.print("  • Type [cyan]hook[/cyan] for video openings")
            console.print("  • Type [cyan]story[/cyan] for narrative structure")
            console.print("  • Type [cyan]cta[/cyan] for call-to-action")
    
    async def _generate_more_options(self):
        """Generate more options for the most recent component."""
        # Find the most recent component generated
        recent_type = None
        for item in reversed(self.state.conversation_history):
            if item.get('type') in ['hooks_generated', 'ctas_generated', 'stories_generated']:
                recent_type = item.get('type')
                break
        
        if recent_type == 'hooks_generated' and 'hook_specialist' in self.agents:
            console.print("\n[yellow]Generating more hook options...[/yellow]")
            console.print(f"\n[dim]→ Connecting to Hook Specialist...[/dim]")
            hook_specialist = self.agents['hook_specialist']
            # Pass "more" command to hook specialist to trigger accumulation
            loader = AnimatedLoader(console)
            with loader.loading("🎨 Generating additional hook variations...", "dots12"):
                hook_response = await hook_specialist.process(self.state, "more")
            self._display_response(hook_response, hook_specialist.name)
            # Update conversation history with all options
            if hook_response.metadata and 'hooks' in hook_response.metadata:
                self.state.conversation_history.append({
                    'type': 'hooks_generated',
                    'options': hook_response.metadata['hooks']
                })
        elif recent_type == 'ctas_generated':
            console.print("\n[yellow]Generating more CTA options...[/yellow]")
            await self._generate_cta()
        elif recent_type == 'stories_generated':
            console.print("\n[yellow]Generating more story options...[/yellow]")
            await self._generate_story()
        else:
            console.print("\n[yellow]No recent options to regenerate. Please generate content first:[/yellow]")
            console.print("  • Type [cyan]hook[/cyan] for video openings")
            console.print("  • Type [cyan]story[/cyan] for narrative structure")
            console.print("  • Type [cyan]cta[/cyan] for call-to-action")
    
    async def _handle_custom_content(self, user_input: str):
        """Handle custom content from user.
        
        Args:
            user_input: User's input containing custom content
        """
        # Find the most recent component type
        recent_type = None
        for item in reversed(self.state.conversation_history):
            if item.get('type') in ['hooks_generated', 'ctas_generated', 'stories_generated']:
                recent_type = item.get('type')
                break
        
        if not recent_type:
            console.print("\n[yellow]Please generate content first before providing custom options:[/yellow]")
            console.print("  • Type [cyan]hook[/cyan] for video openings")
            console.print("  • Type [cyan]story[/cyan] for narrative structure")
            console.print("  • Type [cyan]cta[/cyan] for call-to-action")
            return
        
        # Extract custom text
        custom_text = user_input
        prefixes = ['custom:', 'custom', 'my own:', 'use this:', 'specific:']
        for prefix in prefixes:
            if custom_text.lower().startswith(prefix):
                custom_text = custom_text[len(prefix):].strip()
                break
        
        # If just "custom" without text, ask for input
        if custom_text.lower() in ['custom', 'my own', 'specific']:
            console.print("\n[cyan]Please provide your custom content:[/cyan]")
            console.print("Format: custom: [your text here]")
            return
        
        # Apply custom content based on type
        if recent_type == 'hooks_generated':
            if not self.state.hook:
                from src.models.config import ScriptComponent
                self.state.hook = ScriptComponent(type="hook", content="", finalized=False)
            self.state.hook.content = custom_text
            self.state.hook.finalized = True
            console.print(f"\n[green]✅ Custom hook set successfully![/green]")
            console.print(f'[italic]"{custom_text}"[/italic]\n')
            console.print("[yellow]What would you like to work on next?[/yellow]")
            console.print("  • Type [cyan]story[/cyan] to develop the narrative")
            console.print("  • Type [cyan]cta[/cyan] to create your call-to-action")
        elif recent_type == 'ctas_generated':
            if not self.state.cta:
                from src.models.config import ScriptComponent
                self.state.cta = ScriptComponent(type="cta", content="", finalized=False)
            self.state.cta.content = custom_text
            self.state.cta.finalized = True
            console.print(f"\n[green]✅ Custom CTA set successfully![/green]")
            console.print(f'[italic]"{custom_text}"[/italic]\n')
            console.print("[yellow]What would you like to work on next?[/yellow]")
            console.print("  • Type [cyan]status[/cyan] to review your progress")
            console.print("  • Type [cyan]review[/cyan] to see complete script")
        elif recent_type == 'stories_generated':
            if not self.state.story:
                from src.models.config import ScriptComponent
                self.state.story = ScriptComponent(type="story", content="", finalized=False)
            self.state.story.content = custom_text
            self.state.story.finalized = True
            console.print(f"\n[green]✅ Custom story structure set successfully![/green]\n")
            console.print("[yellow]What would you like to work on next?[/yellow]")
            console.print("  • Type [cyan]cta[/cyan] to create your call-to-action")
            console.print("  • Type [cyan]review[/cyan] to see what you have so far")
    
    async def _edit_component(self, component_type: str, user_input: str):
        """Edit an existing component (hook, story, or CTA).
        
        Args:
            component_type: Type of component to edit ('hook', 'story', 'cta')
            user_input: User's input with edit command
        """
        # Get current content
        current_content = None
        if component_type == 'hook' and self.state.hook:
            current_content = self.state.hook.content
        elif component_type == 'story' and self.state.story:
            current_content = self.state.story.content
        elif component_type == 'cta' and self.state.cta:
            current_content = self.state.cta.content
        
        if not current_content:
            console.print(f"[yellow]No {component_type} to edit yet. Generate one first.[/yellow]")
            return
        
        console.print(f"\n[cyan]Current {component_type.title()}:[/cyan]")
        console.print(f"[dim]{current_content[:200]}...[/dim]\n")
        
        # Ask for new content
        console.print(f"[bold]Enter your updated {component_type} (or 'cancel' to keep current):[/bold]")
        new_content = Prompt.ask("")
        
        if new_content.lower() != 'cancel' and new_content.strip():
            # Update the component
            if component_type == 'hook':
                self.state.hook.content = new_content
                self.state.hook.iterations += 1
                console.print(f"[green]✅ Hook updated successfully![/green]")
            elif component_type == 'story':
                self.state.story.content = new_content
                self.state.story.iterations += 1
                console.print(f"[green]✅ Story updated successfully![/green]")
            elif component_type == 'cta':
                self.state.cta.content = new_content
                self.state.cta.iterations += 1
                console.print(f"[green]✅ CTA updated successfully![/green]")
            
            # Auto-save
            if self.project_id:
                self.session_manager.save_state(self.state, self.project_id)
            
            console.print("\n[yellow]What would you like to do next?[/yellow]")
            console.print("  • Type [cyan]review[/cyan] to see your updated script")
            console.print("  • Type [cyan]humanize[/cyan] to make it more natural")
            console.print("  • Type [cyan]export[/cyan] to save your script")
        else:
            console.print("[yellow]Edit cancelled. Keeping current content.[/yellow]")
    
    def _display_response(self, response, agent_name):
        """Display agent response in a formatted way."""
        console.print(f"\n[bold magenta]{agent_name}:[/bold magenta]")
        
        # Display main content as markdown
        console.print(Markdown(response.content))
        
        # Display suggestions if any
        if response.suggestions:
            console.print("\n[dim]Suggestions:[/dim]")
            for suggestion in response.suggestions:
                console.print(f"  • {suggestion}")
    
    async def _export_script(self):
        """Export the current script."""
        if not self.state:
            console.print("[yellow]No script to export[/yellow]")
            return
        
        if self.project_id and self.project_id != -1:
            # Export from database
            script_text = self.session_manager.get_script_text(self.project_id)
            filename = Prompt.ask("[bold]Export filename[/bold]", default="script_export.txt")
            
            with open(filename, 'w') as f:
                f.write(script_text)
            
            console.print(f"[green]✅ Script exported to {filename}[/green]")
            
            # Also offer JSON export
            if Confirm.ask("Export as JSON for backup?"):
                self.session_manager.export_to_file(self.project_id)
        else:
            # Export from current state
            script_parts = []
            if self.state.hook and self.state.hook.content:
                script_parts.append(f"HOOK:\n{self.state.hook.content}\n")
            if self.state.story and self.state.story.content:
                script_parts.append(f"STORY:\n{self.state.story.content}\n")
            if self.state.cta and self.state.cta.content:
                script_parts.append(f"CTA:\n{self.state.cta.content}\n")
            
            if script_parts:
                filename = Prompt.ask("[bold]Export filename[/bold]", default="script_export.txt")
                with open(filename, 'w') as f:
                    f.write("\n".join(script_parts))
                console.print(f"[green]✅ Script exported to {filename}[/green]")
            else:
                console.print("[yellow]No content to export[/yellow]")
    
    async def _list_projects(self):
        """List all saved projects."""
        projects = self.session_manager.db.list_projects()
        
        if not projects:
            console.print("[yellow]No saved projects found[/yellow]")
            return
        
        console.print("\n[bold]Saved Projects:[/bold]")
        for idx, project in enumerate(projects, 1):
            status_icon = "🚧" if project.status == "in_progress" else "✅"
            console.print(f"{idx}. {status_icon} {project.title} ({project.platform})")
            console.print(f"   Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        console.print("\n[dim]Use 'exit' and restart to load a project[/dim]")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
[bold cyan]📚 Database & Session Features:[/bold cyan]
• Your projects are automatically saved after every interaction
• Continue where you left off when you restart
• Export scripts as text or JSON backup

[bold]Core Commands:[/bold]
• exit - Save and quit the application
• save - Manually save your progress
• export - Export script to file
• list - Show all saved projects
• help - Show this help message
• status - Show current script status

[bold]Content Generation:[/bold]
• hook/hooks - Generate video hooks
• story - Work on the story structure
• cta - Work on the call-to-action

[bold]Act Development (in Story):[/bold]
• draft: [text] - Submit your act draft
• enhance - Improve your current draft
• research: [topic] - Research specific topics
• example: [concept] - Get relevant examples
• next act - Move to next act
• show script - View complete script

[bold]Quality Enhancement:[/bold]
• research - Fact-check and research topics
• verify - Verify specific claims
• humanize - Make content sound natural
• style/tone - Adjust style and tone
• critique - Get constructive feedback
• challenge - Challenge assumptions

[bold]Options & Selection:[/bold]
• 1, 2, 3... - Select from generated options
• more - Generate additional options
• enhance [number] - Improve specific option
• custom: [text] - Use your own content

[bold]7 Agents Available:[/bold]
✅ Orchestrator - Workflow management
✅ Hook Specialist - Opening creation
✅ Story Architect - Narrative structure
✅ CTA Strategist - Call-to-action
✅ Research Analyst - Fact-checking
✅ Stylist - Voice & tone matching
✅ Challenger - Constructive critique
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def _show_status(self):
        """Show current project status."""
        if not self.state:
            console.print("[yellow]No active project[/yellow]")
            return
        
        # Check if script is complete
        is_complete = (self.state.hook and self.state.hook.finalized and 
                      self.state.story and self.state.story.finalized and 
                      self.state.cta and self.state.cta.finalized)
        
        status = f"""
[bold]Project Status:[/bold]
Topic: {self.state.topic}
Platform: {self.state.platform}
Audience: {self.state.target_audience}

[bold]Components:[/bold]
• Hook: {'✅ Finalized' if self.state.hook and self.state.hook.finalized else '⏳ In Progress' if self.state.hook else '❌ Not Started'}
• Story: {'✅ Finalized' if self.state.story and self.state.story.finalized else '⏳ In Progress' if self.state.story else '❌ Not Started'}
• CTA: {'✅ Finalized' if self.state.cta and self.state.cta.finalized else '⏳ In Progress' if self.state.cta else '❌ Not Started'}

Tone Samples: {len(self.state.user_tone_samples)}
Context Docs: {len(self.state.context_documents)}
        """
        console.print(Panel(status, title="Project Status", border_style="green"))
        
        # If complete, suggest export
        if is_complete:
            console.print("\n[green]🎉 Your script is complete![/green]")
            console.print("[yellow]Available actions:[/yellow]")
            console.print("  • Type [cyan]export[/cyan] to save your script to a file")
            console.print("  • Type [cyan]review[/cyan] to get comprehensive feedback")
            console.print("  • Type [cyan]humanize[/cyan] to make it sound more natural")


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(debug):
    """AI-powered video script generator with multi-agent collaboration."""
    if debug:
        import os
        os.environ['DEBUG_MODE'] = 'true'
    
    console.print(Panel.fit(
        "[bold cyan]🎬 Video Script Generator[/bold cyan]\n"
        "Powered by Multiple AI Providers",
        border_style="cyan"
    ))
    
    try:
        cli = VideoScriptCLI()
        # Always start with menu (don't skip it)
        asyncio.run(cli.start_new_project(skip_menu=False))
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        if debug:
            console.print_exception()


if __name__ == "__main__":
    main()
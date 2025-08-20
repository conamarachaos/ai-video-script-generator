"""
AI Video Script Generator Web Application
Unified version with all fixes and improvements
"""

from flask import Flask, render_template, request, jsonify, session
import json
import uuid
from datetime import datetime
import sqlite3
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from enum import Enum

# Import the agent system
from src.models.config import Settings, VideoScriptState, AgentRole, ModelConfig, ModelProvider, AgentConfig
from src.models.model_factory import get_model_factory
from src.models.provider_strategy import ProviderStrategy
from src.agents.orchestrator import OrchestratorAgent
from src.agents.hook_specialist import HookSpecialistAgent
from src.agents.story_architect import StoryArchitectAgent
from src.agents.cta_strategist import CTAStrategistAgent
from src.database.session_manager import SessionManager
from src.agents.base_agent import AgentResponse
from hook_parser import parse_hooks_advanced, extract_hook_metadata

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Database setup
DB_PATH = 'conversations.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class ConversationState(Enum):
    """Conversation state machine"""
    INITIAL = "initial"
    AWAITING_TOPIC = "awaiting_topic"
    AWAITING_PLATFORM = "awaiting_platform"
    AWAITING_AUDIENCE = "awaiting_audience"
    AWAITING_DURATION = "awaiting_duration"
    MAIN_MENU = "main_menu"
    GENERATING_HOOKS = "generating_hooks"
    HOOKS_GENERATED = "hooks_generated"
    GENERATING_STORY = "generating_story"
    STORY_GENERATED = "story_generated"
    GENERATING_CTA = "generating_cta"
    CTA_GENERATED = "cta_generated"

class AgentManager:
    """Manages AI agents for web application with thread-safe async execution"""
    
    def __init__(self):
        self.settings = Settings()
        self.factory = get_model_factory()
        self.agents = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agents with available providers"""
        try:
            # Create provider strategy
            strategy = ProviderStrategy(self.factory.available_providers)
            distribution = strategy.get_optimal_distribution()
            
            # Initialize Hook Specialist
            hook_config_data = distribution.get(AgentRole.HOOK_SPECIALIST)
            if hook_config_data:
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
            
            # Initialize Story Architect
            story_config_data = distribution.get(AgentRole.STORY_ARCHITECT)
            if story_config_data:
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
            
            # Initialize CTA Strategist
            cta_config_data = distribution.get(AgentRole.CTA_STRATEGIST)
            if cta_config_data:
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
                
            print(f"✅ Initialized {len(self.agents)} agents successfully")
            print(f"   Available agents: {list(self.agents.keys())}")
            
        except Exception as e:
            print(f"⚠️  Error initializing agents: {e}")
            print("   Using template-based fallback mode")
            self.agents = {}
    
    def run_agent_async(self, agent_key: str, state: VideoScriptState, prompt: str):
        """Run an agent asynchronously using a thread pool with proper event loop handling"""
        if agent_key not in self.agents:
            raise Exception(f"Agent {agent_key} not available")
        
        agent = self.agents[agent_key]
        
        def run_in_thread():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the async method in the new loop
                result = loop.run_until_complete(agent.process(state, prompt))
                return result
            finally:
                # Properly close the loop
                loop.close()
        
        # Run in thread pool to avoid event loop conflicts
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_thread)
            return future.result(timeout=30)

# Initialize agent manager globally
agent_manager = AgentManager()

class ConversationManager:
    """Manages conversation state and workflow"""
    
    def __init__(self):
        self.states = {}
        
    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        if conversation_id not in self.states:
            self.states[conversation_id] = {
                'state': ConversationState.INITIAL,
                'video_state': None,  # VideoScriptState object
                'topic': None,
                'platform': None,
                'audience': None,
                'duration': None,
                'hooks': [],
                'selected_hook': None,
                'story': None,
                'ctas': [],
                'selected_cta': None,
                'awaiting_selection': None,
                'hook_generation_count': 0
            }
        return self.states[conversation_id]
    
    def update_state(self, conversation_id: str, updates: Dict[str, Any]):
        state = self.get_state(conversation_id)
        state.update(updates)
        
    def clear_state(self, conversation_id: str):
        if conversation_id in self.states:
            del self.states[conversation_id]

# Initialize conversation manager
conversation_manager = ConversationManager()

@app.route('/')
def index():
    """Serve the main application page"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for the current user"""
    user_id = session.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, created_at, updated_at 
        FROM conversations 
        WHERE user_id = ? 
        ORDER BY updated_at DESC
    ''', (user_id,))
    conversations = []
    for row in cursor.fetchall():
        conversations.append({
            'id': row[0],
            'title': row[1],
            'created_at': row[2],
            'updated_at': row[3]
        })
    conn.close()
    return jsonify(conversations)

@app.route('/api/conversation/<conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
    """Get all messages for a specific conversation"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content, timestamp 
        FROM messages 
        WHERE conversation_id = ? 
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'role': row[0],
            'content': row[1],
            'timestamp': row[2]
        })
    conn.close()
    return jsonify(messages)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint - processes user messages and returns responses"""
    data = request.json
    message = data.get('message', '')
    conversation_id = data.get('conversation_id')
    option_selected = data.get('option_selected')
    
    user_id = session.get('user_id')
    
    # Create new conversation if needed
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        title = "New Video Script Project"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (conversation_id, user_id, title, datetime.now(), datetime.now()))
        conn.commit()
        conn.close()
    
    # Get conversation state
    state = conversation_manager.get_state(conversation_id)
    
    # Save user message (if not an option selection)
    if message and not option_selected:
        message_id = str(uuid.uuid4())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (id, conversation_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (message_id, conversation_id, 'user', message, datetime.now()))
        conn.commit()
        conn.close()
    
    # Process based on current state
    try:
        response_data = process_conversation(conversation_id, message, option_selected, state)
    except Exception as e:
        print(f"❌ Error processing conversation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f"Failed to process request: {str(e)}",
            'response': '',
            'options': [],
            'conversation_id': conversation_id,
            'state': state['state'].value
        })
    
    # Check if there's an error
    if response_data.get('error'):
        return jsonify({
            'error': response_data['error'],
            'response': '',
            'options': [],
            'conversation_id': conversation_id,
            'state': state['state'].value
        })
    
    # Save assistant message only if no error
    assistant_message_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (id, conversation_id, role, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (assistant_message_id, conversation_id, 'assistant', response_data['content'], datetime.now()))
    
    # Update conversation timestamp and title if needed
    if state['topic'] and state['state'] == ConversationState.AWAITING_PLATFORM:
        title = f"Video Script: {state['topic'][:40]}..."
        cursor.execute('''
            UPDATE conversations 
            SET updated_at = ?, title = ?
            WHERE id = ?
        ''', (datetime.now(), title, conversation_id))
    else:
        cursor.execute('''
            UPDATE conversations 
            SET updated_at = ? 
            WHERE id = ?
        ''', (datetime.now(), conversation_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'response': response_data['content'],
        'options': response_data.get('options', []),
        'conversation_id': conversation_id,
        'state': state['state'].value
    })

def process_conversation(conversation_id: str, message: str, option_selected: Optional[str], state: Dict[str, Any]) -> Dict[str, Any]:
    """Process conversation flow and generate appropriate responses"""
    
    current_state = state['state']
    
    # Debug logging
    print(f"📝 Processing: State={current_state.value}, Message='{message[:50] if message else ''}...', Option={option_selected}")
    
    # Check for quick commands
    if message:
        lower_msg = message.lower().strip()
        
        # Help command
        if lower_msg in ['help', '/help', 'commands', '/commands']:
            return {
                'content': """📚 **Available Commands:**

**Quick Actions:**
• `/start` or `start` - Begin a new video script project
• `/help` or `help` - Show this help message
• `/examples` - See example video topics
• `/tips` - Get video creation tips

**During Script Creation:**
• `hooks` - Generate attention-grabbing openings (powered by AI agents)
• `story` - Build narrative structure (powered by AI agents)
• `cta` - Create call-to-action (powered by AI agents)
• `full` - Generate complete script
• `export` - Export your script
• `new` - Start over with a new project

**AI-Powered Features:**
🤖 Using advanced AI agents for content generation
🎯 Platform-specific optimization
🔄 Generate unlimited variations

Type `/start` or simply tell me your video topic to begin!""",
                'options': [
                    {'id': 'start', 'label': '🚀 Start New Project', 'value': 'start'},
                    {'id': 'examples', 'label': '💡 See Examples', 'value': 'examples'},
                    {'id': 'tips', 'label': '📝 Video Tips', 'value': 'tips'}
                ]
            }
    
    # Handle option selections from buttons
    if option_selected == 'start':
        conversation_manager.update_state(conversation_id, {'state': ConversationState.AWAITING_TOPIC})
        return {
            'content': """🎬 **Let's Create Your Video Script!**

I'll guide you through a simple 4-step process using AI agents:
1️⃣ Tell me your video topic
2️⃣ Choose your platform
3️⃣ Define your audience
4️⃣ Select duration

**First: What's your video about?** 
(Example: "How to make perfect coffee at home")""",
            'options': []
        }
    
    # Initial greeting
    if current_state == ConversationState.INITIAL:
        return {
            'content': """🎬 **Welcome to AI Video Script Generator!**

I'm powered by specialized AI agents that create engaging video scripts for any platform.

**🤖 My AI Agents:**
• **Hook Specialist** - Creates viral-worthy openings
• **Story Architect** - Builds compelling narratives
• **CTA Strategist** - Designs converting calls-to-action

**Quick Start Options:**""",
            'options': [
                {'id': 'start', 'label': '🚀 Start New Script', 'value': 'start', 'description': 'Begin creating your video script'},
                {'id': 'help', 'label': '📚 View Commands', 'value': 'help', 'description': 'See all available commands'},
            ]
        }
    
    # Get topic
    elif current_state == ConversationState.AWAITING_TOPIC:
        conversation_manager.update_state(conversation_id, {
            'topic': message,
            'state': ConversationState.AWAITING_PLATFORM
        })
        return {
            'content': f"Great! A video about **{message}**.\n\n**Which platform will you be posting on?**",
            'options': [
                {'id': 'youtube', 'label': '📺 YouTube', 'value': 'youtube'},
                {'id': 'tiktok', 'label': '🎵 TikTok', 'value': 'tiktok'},
                {'id': 'instagram', 'label': '📷 Instagram', 'value': 'instagram'},
                {'id': 'general', 'label': '🌐 General/Multiple', 'value': 'general'}
            ]
        }
    
    # Get platform
    elif current_state == ConversationState.AWAITING_PLATFORM:
        platform = option_selected or message.lower()
        conversation_manager.update_state(conversation_id, {
            'platform': platform,
            'state': ConversationState.AWAITING_AUDIENCE
        })
        return {
            'content': f"Perfect! Creating for **{platform.title()}**.\n\n**Who is your target audience?**\n\nDescribe your ideal viewer (e.g., 'Young professionals interested in tech', 'Parents looking for educational content', 'Fitness enthusiasts')",
            'options': []
        }
    
    # Get audience
    elif current_state == ConversationState.AWAITING_AUDIENCE:
        conversation_manager.update_state(conversation_id, {
            'audience': message,
            'state': ConversationState.AWAITING_DURATION
        })
        
        platform = state['platform']
        duration_suggestions = {
            'tiktok': ['15 seconds', '30 seconds', '60 seconds'],
            'instagram': ['30 seconds', '60 seconds', '90 seconds'],
            'youtube': ['3 minutes', '5 minutes', '10 minutes'],
            'general': ['1 minute', '3 minutes', '5 minutes']
        }
        
        suggestions = duration_suggestions.get(platform, duration_suggestions['general'])
        
        return {
            'content': f"Target audience: **{message}**\n\n**How long should your video be?**\n\nRecommended durations for {platform}:",
            'options': [
                {'id': f'duration_{i}', 'label': duration, 'value': duration}
                for i, duration in enumerate(suggestions)
            ] + [{'id': 'custom_duration', 'label': 'Custom duration', 'value': 'custom'}]
        }
    
    # Get duration
    elif current_state == ConversationState.AWAITING_DURATION:
        if option_selected and option_selected != 'custom':
            duration = option_selected
        else:
            duration = parse_duration(message)
        
        # Create VideoScriptState for agents
        video_state = VideoScriptState(
            topic=state['topic'],
            platform=state['platform'],
            target_audience=state['audience']
        )
        video_state.video_duration = duration
        
        conversation_manager.update_state(conversation_id, {
            'duration': duration,
            'video_state': video_state,
            'state': ConversationState.MAIN_MENU
        })
        
        return {
            'content': f"""✅ **Project Setup Complete!**

📝 **Your Video Script Project:**
• **Topic:** {state['topic']}
• **Platform:** {state['platform'].title()}
• **Audience:** {state['audience']}
• **Duration:** {duration}

**What would you like to create first?** (Powered by AI Agents)""",
            'options': [
                {'id': 'hooks', 'label': '🎣 Generate Hooks', 'value': 'hooks', 'description': 'AI-powered attention-grabbing openings'},
                {'id': 'story', 'label': '📖 Build Story Structure', 'value': 'story', 'description': 'AI-crafted narrative flow'},
                {'id': 'cta', 'label': '🎯 Create Call-to-Action', 'value': 'cta', 'description': 'AI-optimized CTAs'},
                {'id': 'full', 'label': '🎬 Generate Full Script', 'value': 'full', 'description': 'Complete AI-generated script'}
            ]
        }
    
    # Main menu actions
    elif current_state == ConversationState.MAIN_MENU:
        action = option_selected or parse_action(message)
        
        if action == 'hooks' or (message and message.lower() == 'hooks'):
            print(f"🎣 Hook generation requested. Available agents: {list(agent_manager.agents.keys())}")
            
            # Use the actual Hook Specialist agent
            if 'hook_specialist' in agent_manager.agents and state.get('video_state'):
                conversation_manager.update_state(conversation_id, {'state': ConversationState.GENERATING_HOOKS})
                
                try:
                    # Create a specific prompt for hook generation
                    prompt = f"""Generate exactly 3 compelling video hooks for:
                    Topic: {state['topic']}
                    Platform: {state['platform']}
                    Audience: {state['audience']}
                    Duration: {state['duration']}
                    
                    Return ONLY the 3 hooks, numbered 1-3. No instructions, no commands, just the actual hook text.
                    Each hook should be a complete, ready-to-use opening line for the video."""
                    
                    # Run the agent synchronously
                    response = agent_manager.run_agent_async('hook_specialist', state['video_state'], prompt)
                    
                    # Handle AgentResponse object
                    if isinstance(response, AgentResponse):
                        response_content = response.content
                    elif isinstance(response, dict):
                        response_content = response.get('content', '')
                    else:
                        response_content = str(response)
                    
                    # Parse the hooks from the response using advanced parser
                    hooks = parse_hooks_advanced(response_content)
                    
                    # If no hooks found, try extracting with metadata and generating fallbacks
                    if not hooks or len(hooks) < 1:
                        metadata = extract_hook_metadata(response_content)
                        hooks = [item['script'] for item in metadata if 'script' in item]
                    
                    if hooks and len(hooks) >= 1:
                        conversation_manager.update_state(conversation_id, {
                            'hooks': hooks,
                            'state': ConversationState.HOOKS_GENERATED,
                            'awaiting_selection': 'hook'
                        })
                        
                        options = [
                            {'id': f'hook_{i}', 'label': f'Option {i+1}', 'value': str(i)}
                            for i in range(len(hooks))
                        ]
                        options.append({'id': 'more_hooks', 'label': '🔄 Generate More Hooks', 'value': 'more_hooks'})
                        
                        hooks_text = "\n\n".join([f"**Option {i+1}:**\n{hook}" for i, hook in enumerate(hooks)])
                        
                        return {
                            'content': f"🎣 **AI Agent Generated {len(hooks)} Hook Options:**\n\n{hooks_text}\n\n**Select a hook or generate more:**",
                            'options': options
                        }
                    else:
                        # Fallback with template hooks if parsing fails
                        return generate_template_hooks(state, conversation_id)
                        
                except Exception as e:
                    print(f"❌ Error in hook generation: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return {
                        'error': f"Failed to communicate with AI agents: {str(e)}. Please check your API keys and try again.",
                        'response': '',
                        'options': []
                    }
            else:
                # Use template-based generation as fallback
                return generate_template_hooks(state, conversation_id)
    
    # Handle hook selection
    elif current_state == ConversationState.HOOKS_GENERATED and state.get('awaiting_selection') == 'hook':
        if option_selected:
            if option_selected == 'more_hooks':
                # Generate more hooks
                conversation_manager.update_state(conversation_id, {
                    'state': ConversationState.MAIN_MENU,
                    'hook_generation_count': state.get('hook_generation_count', 0) + 1
                })
                return process_conversation(conversation_id, '', 'hooks', state)
            else:
                try:
                    hook_index = int(option_selected)
                    selected_hook = state['hooks'][hook_index]
                    conversation_manager.update_state(conversation_id, {
                        'selected_hook': selected_hook,
                        'state': ConversationState.MAIN_MENU,
                        'awaiting_selection': None
                    })
                    
                    return {
                        'content': f"✅ **Hook selected!**\n\n{selected_hook}\n\n**What would you like to create next?**",
                        'options': [
                            {'id': 'story', 'label': '📖 Build Story Structure', 'value': 'story'},
                            {'id': 'cta', 'label': '🎯 Create Call-to-Action', 'value': 'cta'},
                            {'id': 'full', 'label': '🎬 Generate Full Script', 'value': 'full'}
                        ]
                    }
                except (ValueError, IndexError):
                    return {
                        'content': "Invalid selection. Please try again.",
                        'options': [
                            {'id': f'hook_{i}', 'label': f'Option {i+1}', 'value': str(i)}
                            for i in range(len(state.get('hooks', [])))
                        ] + [{'id': 'more_hooks', 'label': '🔄 Generate More Hooks', 'value': 'more_hooks'}]
                    }
    
    # Default response
    return {
        'content': "I'll help you with that. What specific aspect would you like to work on?",
        'options': []
    }

def generate_template_hooks(state: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
    """Generate template-based hooks as fallback when agents aren't available"""
    platform_hooks = {
        'youtube': [
            f"What if I told you that {state['topic']} could change everything?",
            f"Most people think {state['topic']} is complicated, but here's the truth...",
            f"Stop what you're doing - this {state['topic']} hack will blow your mind!"
        ],
        'tiktok': [
            f"POV: You just discovered the secret to {state['topic']}",
            f"Wait for it... {state['topic']} edition!",
            f"Nobody talks about this {state['topic']} trick..."
        ],
        'instagram': [
            f"Save this before it's gone! {state['topic']} secrets revealed",
            f"You've been doing {state['topic']} wrong this whole time",
            f"The {state['topic']} tip that changed my life ✨"
        ]
    }
    
    hooks = platform_hooks.get(state['platform'], [
        f"Here's what nobody tells you about {state['topic']}",
        f"The truth about {state['topic']} might surprise you",
        f"Master {state['topic']} in just {state['duration']}"
    ])
    
    conversation_manager.update_state(conversation_id, {
        'hooks': hooks,
        'state': ConversationState.HOOKS_GENERATED,
        'awaiting_selection': 'hook'
    })
    
    options = [
        {'id': f'hook_{i}', 'label': f'Option {i+1}', 'value': str(i)}
        for i in range(len(hooks))
    ]
    
    hooks_text = "\n\n".join([f"**Option {i+1}:**\n{hook}" for i, hook in enumerate(hooks)])
    
    return {
        'content': f"🎣 **Generated {len(hooks)} Hook Options (Template Mode):**\n\n{hooks_text}\n\n**Select a hook:**",
        'options': options
    }

def parse_duration(text: str) -> str:
    """Parse duration from user input"""
    text = text.lower()
    match = re.search(r'(\d+)\s*(second|minute|min|sec|s|m)', text)
    if match:
        number = match.group(1)
        unit = match.group(2)
        if 'sec' in unit or unit == 's':
            return f"{number} seconds"
        else:
            return f"{number} minutes"
    
    match = re.search(r'^(\d+)$', text.strip())
    if match:
        return f"{match.group(1)} minutes"
    
    return "2 minutes"

def parse_action(text: str) -> Optional[str]:
    """Parse action from user input"""
    text = text.lower()
    if any(word in text for word in ['hook', 'opening', 'start']):
        return 'hooks'
    elif any(word in text for word in ['story', 'narrative', 'structure']):
        return 'story'
    elif any(word in text for word in ['cta', 'call', 'action']):
        return 'cta'
    elif any(word in text for word in ['full', 'complete', 'entire']):
        return 'full'
    return None

def parse_hooks_from_response(content: str) -> List[str]:
    """Parse hooks from agent response content - now uses advanced parser"""
    return parse_hooks_advanced(content)

@app.route('/api/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation and all its messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
    cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
    conn.commit()
    conn.close()
    conversation_manager.clear_state(conversation_id)
    return jsonify({'success': True})

@app.route('/api/new-conversation', methods=['POST'])
def new_conversation():
    """Start a new conversation"""
    session['current_conversation'] = None
    return jsonify({'success': True})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎬 AI Video Script Generator Web App")
    print("="*60)
    print(f"✅ Agents initialized: {len(agent_manager.agents)}")
    if agent_manager.agents:
        for agent_name in agent_manager.agents:
            print(f"   • {agent_name}")
    else:
        print("   ⚠️  No AI agents available - using template mode")
    print("-"*60)
    print("🌐 Starting server on http://localhost:5000")
    print("   Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, threaded=True)
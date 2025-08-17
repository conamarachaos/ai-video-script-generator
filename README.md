# 🎬 AI Video Script Generator

A powerful multi-agent AI system that creates compelling video scripts through intelligent collaboration between 7 specialized AI agents.

## ✨ Key Features

### 🤖 Multi-Agent Architecture
- **7 Specialized Agents**: Each agent focuses on a specific aspect of script creation
- **Optimal Provider Selection**: Automatically chooses the best AI model for each agent
- **Intelligent Orchestration**: Seamless collaboration between agents

### 💾 Database & Persistence
- **Auto-Save Everything**: Never lose work - saves after every interaction
- **Project Management**: Create, continue, search, and delete projects
- **Session Persistence**: Close the app and continue exactly where you left off

### 🎯 Smart Features
- **Platform Optimization**: Tailored scripts for YouTube, TikTok, Instagram, LinkedIn
- **Humanization**: Make scripts sound natural and authentic
- **Edit After Review**: Revise any component based on feedback
- **Export Options**: Save as text file or JSON backup

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- At least one API key (Claude, OpenAI, Gemini, or DeepSeek)

### Installation

```bash
# Clone the repository
cd ai-video-script-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use any text editor
```

**Supported Providers** (add at least one):
- `ANTHROPIC_API_KEY` - Claude models (recommended for quality)
- `OPENAI_API_KEY` - GPT models (best for CTAs)
- `GOOGLE_API_KEY` - Gemini models (great for creative content)
- `DEEPSEEK_API_KEY` - DeepSeek models (most cost-effective)

### Run the Application

```bash
python main.py
```

## 📖 How It Works

### The 7 Specialized Agents

1. **🎯 Orchestrator** - Manages workflow and coordinates agents
2. **🎣 Hook Specialist** - Creates attention-grabbing openings
3. **📖 Story Architect** - Develops narrative structure with perfect pacing
4. **💰 CTA Strategist** - Designs compelling calls-to-action
5. **🔬 Research Analyst** - Fact-checks and adds credibility
6. **🎨 Stylist** - Ensures natural, authentic voice
7. **👹 Challenger** - Provides constructive criticism (5:1 positive ratio)

### Basic Workflow

1. **Start or Continue**
   ```
   Welcome! What would you like to do?
   📝 new - Create a new video script
   📚 1-3 - Continue an existing project
   ```

2. **Create Content**
   ```
   You: hook
   [Get 3 opening options, select with numbers 1-3]
   
   You: story
   [Develop narrative structure]
   
   You: cta
   [Generate call-to-action options]
   ```

3. **Review & Refine**
   ```
   You: review
   [Get comprehensive feedback]
   
   You: humanize
   [Make script sound natural]
   
   You: export
   [Save to file]
   ```

## 💡 Core Commands

### Content Generation
- `hook` - Create 3-6 video opening options
- `story` - Build narrative structure with acts
- `cta` - Generate compelling calls-to-action

### Review & Management
- `status` - Check current progress
- `review` - Get comprehensive script analysis
- `export` - Save script to file
- `help` - Show all commands

### Quality Enhancement
- `humanize` - Make script sound natural
- `style` - Adjust writing style
- `critique` - Get constructive feedback
- `research` - Fact-check content

### Editing
- `edit hook` - Revise your opening
- `edit story` - Update narrative
- `edit cta` - Change call-to-action

### Selection
- `1`, `2`, `3` - Select an option
- `more` - Get additional options

## 📊 Database Features

### Auto-Save System
- **Every interaction saves automatically**
- **No manual saving needed**
- **SQLite database** (`video_scripts.db`)
- **Complete state preservation**

### Project Management
```
📚 Your Saved Video Scripts
┌───┬─────────────────┬──────────┬────────────┬──────────────┐
│ # │ Title          │ Platform │ Status     │ Last Modified│
├───┼─────────────────┼──────────┼────────────┼──────────────┤
│ 1 │ AI Tutorial    │ youtube  │ 🚧 progress│ 2025-08-17   │
│ 2 │ Product Launch │ tiktok   │ ✅ complete│ 2025-08-16   │
└───┴─────────────────┴──────────┴────────────┴──────────────┘
```

## 🎯 Platform Optimization

### YouTube
- Longer narratives (5-20 minutes)
- SEO-optimized hooks
- Educational or entertainment focus
- Strong CTAs for subscriptions

### TikTok
- Ultra-short format (30-60 seconds)
- Trending hooks
- High energy pacing
- Quick value delivery

### Instagram
- Visual-first approach
- Story-friendly structure
- Hashtag optimization
- Link-in-bio CTAs

### LinkedIn
- Professional tone
- Value-driven content
- Industry insights
- B2B focused CTAs

## 📁 Project Structure

```
├── src/
│   ├── agents/          # 7 specialized AI agents
│   ├── models/          # Configuration & state management
│   ├── providers/       # Multi-provider support
│   ├── database/        # SQLite persistence layer
│   └── utils/           # Helper utilities
├── main.py              # Application entry point
├── video_scripts.db     # Your saved projects
├── requirements.txt     # Python dependencies
├── .env                 # API keys configuration
└── docs/               # Additional documentation
```

## 🔧 Advanced Features

### Act-by-Act Story Development
```
You: story
You: draft: In the first act, we establish...
You: enhance
You: next act
```

### Multi-CTA Strategy
- Soft CTA (mid-video): Low commitment
- Primary CTA (end): Main conversion goal
- Description CTA: Passive option

### Research Integration
```
You: research: latest AI statistics 2025
You: example: successful implementations
```

## 💰 Cost Estimates

Based on typical usage (1000 scripts/month):

| Setup | Providers | Monthly Cost | Quality |
|-------|-----------|--------------|---------|
| Premium | Claude Opus + GPT-4 | ~$250 | Best quality |
| Balanced | Mixed models | ~$90 | Great quality |
| Budget | DeepSeek + Gemini | ~$20 | Good quality |

## 🐛 Troubleshooting

### Common Issues

**"No API key configured"**
```bash
# Check your .env file
cat .env | grep API_KEY
```

**"Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**"Can't find my saved projects"**
```bash
# Check database exists
ls -la video_scripts.db
```

### Debug Mode
```bash
python main.py --debug
```
---

Ready to create amazing video scripts? Run `python main.py` and let's get started! 🚀
"""Stylist agent for tone matching and ensuring authentic voice."""

from typing import Optional, Dict, Any, List
import re
from .base_agent import BaseAgent, AgentResponse
from ..models.config import VideoScriptState


class StylistAgent(BaseAgent):
    """Stylist agent specialized in tone, voice, and style consistency."""
    
    def __init__(self, config, llm):
        """Initialize the Stylist agent."""
        super().__init__(config, llm)
        self.ai_indicators = self._initialize_ai_indicators()
        self.style_dimensions = self._initialize_style_dimensions()
        self.tone_profiles = self._initialize_tone_profiles()
    
    def _initialize_ai_indicators(self) -> List[str]:
        """Initialize indicators of AI-generated content."""
        return [
            'it is important to note',
            'it is worth noting',
            'in conclusion',
            'in summary',
            'furthermore',
            'additionally',
            'however, it should be noted',
            'delve into',
            'leverage',
            'utilize',
            'robust',
            'comprehensive',
            'innovative solution',
            'cutting-edge',
            'state-of-the-art',
            'paradigm shift',
            'synergy',
            'best practices',
            'key takeaway',
            'it\'s crucial to understand',
            'let\'s explore',
            'in today\'s digital age',
            'in the modern era'
        ]
    
    def _initialize_style_dimensions(self) -> Dict[str, List[str]]:
        """Initialize style analysis dimensions."""
        return {
            'formality': ['casual', 'conversational', 'professional', 'formal', 'academic'],
            'energy': ['calm', 'moderate', 'enthusiastic', 'energetic', 'intense'],
            'complexity': ['simple', 'accessible', 'moderate', 'sophisticated', 'complex'],
            'emotion': ['neutral', 'warm', 'inspiring', 'passionate', 'dramatic'],
            'pace': ['slow', 'steady', 'moderate', 'quick', 'rapid'],
            'personality': ['friendly', 'authoritative', 'quirky', 'serious', 'playful']
        }
    
    def _initialize_tone_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize platform-specific tone profiles."""
        return {
            'youtube': {
                'formality': 'conversational',
                'energy': 'enthusiastic',
                'complexity': 'accessible',
                'traits': ['engaging', 'educational', 'personable']
            },
            'tiktok': {
                'formality': 'casual',
                'energy': 'energetic',
                'complexity': 'simple',
                'traits': ['snappy', 'trendy', 'authentic']
            },
            'instagram': {
                'formality': 'conversational',
                'energy': 'moderate',
                'complexity': 'accessible',
                'traits': ['visual', 'inspirational', 'relatable']
            },
            'linkedin': {
                'formality': 'professional',
                'energy': 'moderate',
                'complexity': 'sophisticated',
                'traits': ['insightful', 'valuable', 'credible']
            }
        }
    
    async def process(self, state: VideoScriptState, user_input: Optional[str] = None) -> AgentResponse:
        """Process style and tone requests."""
        
        if user_input:
            if 'humanize' in user_input.lower() or 'natural' in user_input.lower():
                return await self._humanize_content(state, user_input)
            elif 'tone' in user_input.lower():
                return await self._adjust_tone(state, user_input)
            elif 'style' in user_input.lower():
                return await self._match_style(state, user_input)
            elif 'voice' in user_input.lower():
                return await self._develop_voice(state, user_input)
            else:
                return await self._style_analysis(state)
        else:
            return await self._style_analysis(state)
    
    async def _humanize_content(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Make content sound more human and less AI-generated."""
        
        # Get the content to humanize
        content = self._extract_content_to_style(state, user_input)
        
        if not content:
            return AgentResponse(
                content="""## ✍️ Nothing to Humanize Yet

Please create some content first, then I can help make it sound more natural!

**Quick Start:**
• Generate a hook, story, or CTA
• Then type `humanize` to make it more authentic
• Or provide specific text after `humanize:`""",
                metadata={"error": "no_content"},
                requires_user_input=True
            )
        
        humanize_prompt = f"""Transform this content to sound more natural and human, less AI-generated:

Original: {content}

Guidelines:
1. Remove formal/corporate language
2. Add conversational elements
3. Use contractions naturally
4. Include personal touches
5. Vary sentence structure
6. Add authentic transitions
7. Remove AI clichés
8. Make it sound like a real person talking

Platform: {state.platform}
Audience: {state.target_audience}

Provide the humanized version that maintains the message but sounds authentic."""

        humanized = await self.invoke_llm(humanize_prompt)
        
        # Check for remaining AI indicators
        ai_score = self._calculate_ai_score(humanized)
        
        response_content = f"""## 🎭 Humanized Version

**Original:**
```
{content[:200]}{'...' if len(content) > 200 else ''}
```

**Natural Version:**
```
{humanized}
```

### 📊 Authenticity Score: {10 - ai_score}/10
{self._get_authenticity_feedback(ai_score)}

### 💡 Humanization Techniques Applied:
• Conversational language
• Natural transitions  
• Personal voice
• Varied rhythm
• Authentic expressions

**Next Steps:**
• Type `tone: [adjustment]` to refine further
• Type `style: [description]` to match specific style
• Use the humanized version in your script"""

        return AgentResponse(
            content=response_content,
            metadata={
                "humanized": True,
                "ai_score": ai_score,
                "original_content": content,
                "humanized_content": humanized
            },
            requires_user_input=True
        )
    
    async def _adjust_tone(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Adjust the tone of content."""
        
        # Extract desired tone
        tone_desc = user_input.replace('tone:', '').replace('tone', '').strip()
        
        content = self._get_all_content(state)
        if not content:
            return self._no_content_response("adjust tone")
        
        tone_prompt = f"""Adjust the tone of this content:

Content: {content}

Desired Tone: {tone_desc if tone_desc else f"Optimal for {state.platform}"}
Platform: {state.platform}
Audience: {state.target_audience}

Provide:
1. Adjusted version with the new tone
2. Key changes made
3. Why this tone works for the audience

Maintain the core message while transforming the delivery."""

        adjusted = await self.invoke_llm(tone_prompt)
        
        response_content = f"""## 🎨 Tone Adjustment

**Target Tone:** {tone_desc if tone_desc else f"Optimized for {state.platform}"}

{adjusted}

### 🎯 Platform Alignment:
{self._get_platform_tone_tips(state.platform)}

### 💡 Fine-Tuning Options:
• `tone: warmer` - Add more personality
• `tone: professional` - More authoritative
• `tone: casual` - More relaxed
• `tone: energetic` - More enthusiasm
• `tone: inspirational` - More motivating

**Remember:** Tone should match both platform and audience expectations!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "tone_adjusted": True,
                "target_tone": tone_desc
            },
            requires_user_input=True
        )
    
    async def _match_style(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Match a specific style or creator."""
        
        style_ref = user_input.replace('style:', '').replace('style', '').strip()
        
        if state.user_tone_samples:
            # Use provided tone samples
            style_prompt = f"""Analyze and match this style:

Reference Samples:
{chr(10).join(state.user_tone_samples)}

Apply this style to create content about: {state.topic}
Platform: {state.platform}
Audience: {state.target_audience}

Provide:
1. Style analysis (key characteristics)
2. Sample content in this style
3. Style guide for consistency"""
        else:
            style_prompt = f"""Create content in this style: {style_ref if style_ref else 'engaging and authentic'}

Topic: {state.topic}
Platform: {state.platform}
Audience: {state.target_audience}

Provide:
1. Style interpretation
2. Sample content
3. Key style elements to maintain"""

        styled = await self.invoke_llm(style_prompt)
        
        response_content = f"""## 🎭 Style Matching

{styled}

### 📝 Style Consistency Checklist:
• Voice: Maintain consistent personality
• Vocabulary: Use characteristic words
• Rhythm: Match sentence patterns
• Energy: Keep consistent enthusiasm
• Transitions: Use similar connectors

### 🔄 Quick Styles:
• `style: MrBeast` - High energy, direct
• `style: educational` - Clear, informative
• `style: storyteller` - Narrative, engaging
• `style: motivational` - Inspiring, uplifting
• `style: authentic` - Real, conversational

**Tip:** Add your own examples with the `tone` command for better matching!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "style_matched": True,
                "style_reference": style_ref
            },
            requires_user_input=True
        )
    
    async def _develop_voice(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Develop a unique voice for the content."""
        
        voice_prompt = f"""Develop a unique, authentic voice for content about: {state.topic}

Platform: {state.platform}
Audience: {state.target_audience}
Current samples: {len(state.user_tone_samples)} provided

Create:
1. Voice Personality Profile
2. Signature Phrases
3. Speaking Patterns
4. Vocabulary Choices
5. Example Application

Make it distinctive but natural."""

        voice = await self.invoke_llm(voice_prompt)
        
        response_content = f"""## 🎤 Voice Development

{voice}

### 🎯 Voice Consistency Guide:

**DO:**
• Stay true to personality
• Use signature phrases sparingly
• Maintain energy level
• Keep vocabulary consistent
• Let personality show naturally

**DON'T:**
• Force catchphrases
• Overuse quirks
• Change mid-script
• Sound robotic
• Copy others exactly

### 📊 Voice Dimensions:
• Warmth: How personable?
• Authority: How expert?
• Energy: How enthusiastic?
• Humor: How playful?
• Directness: How straightforward?

**Your unique voice is your competitive advantage!**"""

        return AgentResponse(
            content=response_content,
            metadata={
                "voice_developed": True
            },
            requires_user_input=True
        )
    
    async def _style_analysis(self, state: VideoScriptState) -> AgentResponse:
        """Analyze the current style of the script."""
        
        content = self._get_all_content(state)
        
        if not content:
            return AgentResponse(
                content="""## ✍️ Stylist Ready

I'll help you create authentic, engaging content that doesn't sound AI-generated!

**My Services:**
• `humanize` - Make content sound natural
• `tone: [description]` - Adjust tone
• `style: [reference]` - Match specific style
• `voice` - Develop unique voice
• `analyze` - Review current style

**Platform-Optimized Tones:**
• YouTube: Conversational & engaging
• TikTok: Quick & trendy
• Instagram: Visual & inspirational
• LinkedIn: Professional & insightful

What style assistance do you need?""",
                metadata={"service": "ready"},
                requires_user_input=True
            )
        
        analysis_prompt = f"""Analyze the style and tone of this script:

{content}

Provide:
1. Current Style Profile
   - Formality level
   - Energy level
   - Complexity
   - Personality
   
2. AI Detection Score (1-10, lower is better)
   - AI language indicators found
   - Unnatural patterns
   
3. Authenticity Assessment
   - What sounds natural
   - What needs work
   
4. Platform Fit ({state.platform})
   - Alignment with platform norms
   - Suggested adjustments
   
5. Improvement Recommendations"""

        analysis = await self.invoke_llm(analysis_prompt)
        
        ai_score = self._calculate_ai_score(content)
        
        response_content = f"""## 📊 Style Analysis

{analysis}

### 🤖 AI Detection Score: {ai_score}/10
{self._get_authenticity_feedback(ai_score)}

### ✨ Quick Improvements:
• Replace formal transitions with natural ones
• Add personal touches and opinions
• Vary sentence structure more
• Use contractions naturally
• Include conversational asides

**Actions Available:**
• Type `humanize` to make more natural
• Type `tone: casual` to relax the style
• Type `voice` to develop unique personality
• Type `export` to save your script to a file

Let's make your script authentically yours!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "analysis_complete": True,
                "ai_score": ai_score
            },
            requires_user_input=True
        )
    
    def _extract_content_to_style(self, state: VideoScriptState, user_input: str) -> str:
        """Extract content that needs styling."""
        # Check if user provided specific content
        if ':' in user_input:
            return user_input.split(':', 1)[1].strip()
        
        # Otherwise use most recent content
        if state.story and state.story.content and not state.story.finalized:
            return state.story.content
        elif state.cta and state.cta.content and not state.cta.finalized:
            return state.cta.content
        elif state.hook and state.hook.content and not state.hook.finalized:
            return state.hook.content
        
        return self._get_all_content(state)
    
    def _get_all_content(self, state: VideoScriptState) -> str:
        """Get all content from the state."""
        parts = []
        if state.hook and state.hook.content:
            parts.append(state.hook.content)
        if state.story and state.story.content:
            parts.append(state.story.content)
        if state.cta and state.cta.content:
            parts.append(state.cta.content)
        return " ".join(parts)
    
    def _calculate_ai_score(self, text: str) -> int:
        """Calculate how AI-like the content sounds (1-10)."""
        score = 0
        text_lower = text.lower()
        
        # Check for AI indicators
        for indicator in self.ai_indicators:
            if indicator in text_lower:
                score += 0.5
        
        # Check for repetitive structure
        sentences = text.split('.')
        if len(sentences) > 3:
            # Check if sentences start similarly
            starts = [s.strip()[:10] for s in sentences if s.strip()]
            if len(starts) != len(set(starts)):
                score += 1
        
        # Check for overuse of transition words
        transitions = ['however', 'furthermore', 'additionally', 'moreover', 'nevertheless']
        transition_count = sum(1 for t in transitions if t in text_lower)
        if transition_count > 2:
            score += 1
        
        # Check for lack of contractions (AI tends to avoid them)
        if "don't" not in text_lower and "won't" not in text_lower and "isn't" not in text_lower:
            score += 1
        
        return min(10, max(1, round(score)))
    
    def _get_authenticity_feedback(self, ai_score: int) -> str:
        """Get feedback based on AI score."""
        if ai_score <= 3:
            return "✅ Excellent! Sounds natural and human."
        elif ai_score <= 5:
            return "👍 Good! Minor adjustments could help."
        elif ai_score <= 7:
            return "⚠️ Moderate AI indicators. Needs humanization."
        else:
            return "❌ Strong AI patterns detected. Significant rewriting recommended."
    
    def _get_platform_tone_tips(self, platform: str) -> str:
        """Get platform-specific tone tips."""
        tips = {
            'youtube': "• Be conversational and educational\n• Use 'you' frequently\n• Include personal anecdotes",
            'tiktok': "• Keep it snappy and trendy\n• Use current slang appropriately\n• Be direct and energetic",
            'instagram': "• Be inspirational and visual\n• Use emotive language\n• Keep it relatable",
            'linkedin': "• Be professional but personable\n• Share insights and value\n• Use industry terminology appropriately",
            'general': "• Be authentic and engaging\n• Match audience expectations\n• Stay consistent throughout"
        }
        return tips.get(platform, tips['general'])
    
    def _no_content_response(self, action: str) -> AgentResponse:
        """Return response when no content is available."""
        return AgentResponse(
            content=f"""## ✍️ No Content to {action.title()}

Please create some content first:
• Type `hook` to create an opening
• Type `story` to develop narrative
• Type `cta` to create call-to-action

Then I can help you {action}!""",
            metadata={"error": "no_content"},
            requires_user_input=True
        )
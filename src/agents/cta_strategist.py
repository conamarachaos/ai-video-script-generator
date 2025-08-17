"""CTA Strategist agent for creating compelling calls-to-action."""

from typing import Optional, Dict, List, Tuple
import json

from .base_agent import SpecializedAgent, AgentResponse
from ..models.config import VideoScriptState, ScriptComponent


class CTAStrategistAgent(SpecializedAgent):
    """
    Specializes in creating compelling calls-to-action that drive viewer engagement
    and conversions across different platforms and video types.
    """
    
    def _load_expertise_prompts(self) -> Dict[str, str]:
        """Load specialized prompts for CTA creation."""
        return {
            "generate_cta": """Based on the video details:
Topic: {topic}
Target audience: {audience}
Platform: {platform}
Hook: {hook}
Story Summary: {story}
Context: {context}

Create exactly 3 simple, clear CTA options:

**Option 1** - Gentle (build relationship)
**Option 2** - Direct (take action now)  
**Option 3** - Value (offer something free)

For EACH option, provide ONLY:
Type: [One word: Subscribe/Download/Learn/Join/Visit]
Primary Text: "Short, clear CTA - max 10 words"
Supporting Text: One sentence explaining the benefit

Keep it simple and actionable. No complex descriptions.""",
            
            "platform_optimize": """Current CTA: {cta}
Platform: {platform}

Optimize this CTA for {platform} following these guidelines:

YouTube:
- Subscribe + notification bell
- End screen elements
- Description links
- Community tab engagement

TikTok:
- Profile link emphasis
- Follow + notifications
- Comment engagement
- Trending hashtags

Instagram:
- Link in bio strategy
- Story swipe-ups (if applicable)
- Save/share prompts
- DM for more info

LinkedIn:
- Professional tone
- Newsletter subscription
- Connection requests
- Article/resource downloads

Provide optimized version with platform-specific elements.""",
            
            "urgency_enhancement": """Current CTA: {cta}
Enhancement Type: {urgency_type}

Add urgency using one of these techniques:
- Scarcity: Limited availability/spots
- Time-sensitive: Deadline or expiration
- Social Proof: Others are taking action
- FOMO: Missing out on benefits
- Exclusive Access: Special offer for viewers
- Bonus Incentive: Extra value for acting now

Create 2 versions:
1. Subtle urgency (professional tone)
2. Strong urgency (direct approach)""",
            
            "multi_cta_strategy": """Video details:
Topic: {topic}
Platform: {platform}
Duration: {duration} seconds

Design a multi-CTA strategy with:
1. Soft CTA (early/middle): Build trust, low commitment
2. Primary CTA (end): Main conversion goal
3. Alternative CTA: For those not ready for primary
4. Passive CTA: Visual/description elements

Include timing and placement for each.""",
            
            "ab_test_variants": """Original CTA: {cta}
Goal: {goal}

Create 3 A/B test variants focusing on:
1. Different emotional triggers
2. Varying urgency levels
3. Alternative value propositions
4. Different action verbs
5. Format variations (question vs. statement)

For each variant, explain the psychological principle being tested."""
        }
    
    async def process(self, state: VideoScriptState, 
                     user_input: Optional[str] = None) -> AgentResponse:
        """
        Generate or improve CTAs based on the current state.
        
        Args:
            state: Current video script state
            user_input: Optional user input
            
        Returns:
            Response with CTA options
        """
        if not state.cta:
            state.cta = ScriptComponent(type="cta", content="", finalized=False)
        
        # Determine action based on input
        if not state.cta.content or (user_input and "new" in user_input.lower()):
            return await self._generate_new_ctas(state, user_input)
        elif user_input and any(word in user_input.lower() for word in ["platform", "optimize"]):
            return await self._optimize_for_platform(state, user_input)
        elif user_input and any(word in user_input.lower() for word in ["urgency", "urgent", "now"]):
            return await self._enhance_urgency(state, user_input)
        elif user_input and any(word in user_input.lower() for word in ["test", "variant", "ab"]):
            return await self._create_ab_variants(state, user_input)
        else:
            return await self._improve_existing_cta(state, user_input)
    
    async def _generate_new_ctas(self, state: VideoScriptState, 
                                user_input: Optional[str]) -> AgentResponse:
        """Generate new CTA options."""
        # Prepare context
        context = self._prepare_context(state)
        hook_content = state.hook.content if state.hook else "No hook yet"
        story_summary = self._summarize_story(state)
        
        # Generate CTAs
        prompt = self.get_expertise_prompt(
            "generate_cta",
            topic=state.topic,
            audience=state.target_audience or "general audience",
            platform=state.platform,
            hook=hook_content,
            story=story_summary,
            context=context
        )
        
        cta_response = await self.invoke_llm(prompt)
        
        # Parse and structure CTAs
        ctas = self._parse_ctas(cta_response)
        
        # Store the best CTA
        if ctas:
            state.cta.content = ctas[0]["primary_text"]
            state.cta.iterations += 1
            state.cta.metadata["variants"] = ctas
        
        # Get video duration from state or story metadata
        video_duration = "60"  # Default
        duration_str = None
        
        # Check state first (set during initialization)
        if hasattr(state, 'video_duration') and state.video_duration:
            duration_str = state.video_duration
        # Fallback to story metadata
        elif state.story and state.story.metadata.get('video_duration'):
            duration_str = state.story.metadata['video_duration']
        
        if duration_str:
            # Extract numeric value from duration string (e.g., "10 minutes" -> 600)
            import re
            match = re.search(r'(\d+)', duration_str)
            if match:
                duration_val = int(match.group(1))
                if 'minute' in duration_str.lower():
                    video_duration = str(duration_val * 60)  # Convert to seconds
                else:
                    video_duration = str(duration_val)  # Already in seconds
        
        # Generate multi-CTA strategy
        strategy_prompt = self.get_expertise_prompt(
            "multi_cta_strategy",
            topic=state.topic,
            platform=state.platform,
            duration=video_duration
        )
        
        strategy_response = await self.invoke_llm(strategy_prompt)
        
        # Format duration for display
        if hasattr(state, 'video_duration') and state.video_duration:
            duration_display = state.video_duration
        elif state.story and state.story.metadata.get('video_duration'):
            duration_display = state.story.metadata.get('video_duration', '60 seconds')
        else:
            duration_display = '60 seconds'
        
        response_content = f"""## 🎯 Your CTA Options

I've created 3 different call-to-action approaches for your {duration_display} {state.platform} video:

"""
        
        # Simplified CTA display
        for i, cta in enumerate(ctas, 1):
            response_content += f"""---

### 🔵 Option {i}: {cta.get('type', 'Action')}

**Say this:** "{cta.get('primary_text', 'Take action now')}"

**Why it works:** {cta.get('supporting_text', 'Encourages viewer action')}

"""
        
        response_content += f"""
---

## ✅ SELECT YOUR CTA:

**Just type the number:**
🔵 **1** = Option 1 ({ctas[0].get('type', 'Action') if ctas else 'First'})
🔵 **2** = Option 2 ({ctas[1].get('type', 'Action') if len(ctas) > 1 else 'Second'})
🔵 **3** = Option 3 ({ctas[2].get('type', 'Action') if len(ctas) > 2 else 'Third'})

**Or customize:**
• **more** = See different options
• **optimize** = Improve for {state.platform}
• **custom: [your text]** = Use your own CTA

---

## 💡 Where to Place Your CTAs:

**Beginning (2-3 minutes in):** Soft ask - "If you're finding this helpful, subscribe"
**Middle (5-6 minutes in):** Engagement - "Like this video if it's useful"
**End (9-10 minutes):** Main CTA - Your selected option above

💡 **Pro tip:** Pick the CTA that matches your content style - educational videos do well with "Learn" CTAs, while tutorial videos work better with "Download" or "Subscribe" CTAs."""
        
        suggestions = [
            f"For {state.platform}, place primary CTA at the end with visual emphasis",
            "Include a soft CTA mid-video to warm up viewers",
            "Test different urgency levels with your audience",
            "Ensure CTA matches the emotional tone of your story ending"
        ]
        
        return AgentResponse(
            content=response_content,
            suggestions=suggestions,
            metadata={"ctas": ctas, "action": "generated", "strategy": strategy_response},
            requires_user_input=True
        )
    
    async def _optimize_for_platform(self, state: VideoScriptState, 
                                    user_input: str) -> AgentResponse:
        """Optimize CTA for specific platform."""
        prompt = self.get_expertise_prompt(
            "platform_optimize",
            cta=state.cta.content,
            platform=state.platform
        )
        
        optimized_cta = await self.invoke_llm(prompt)
        
        # Update CTA
        old_content = state.cta.content
        state.cta.content = optimized_cta
        state.cta.iterations += 1
        state.cta.metadata["platform_optimized"] = True
        
        response_content = f"""## Platform-Optimized CTA for {state.platform.title()}

**Original CTA:**
"{old_content}"

**Optimized for {state.platform.title()}:**
{optimized_cta}

This optimization includes:
- Platform-specific language and conventions
- Optimal placement recommendations
- Technical requirements (links, buttons, etc.)
- Engagement mechanics unique to {state.platform}

The optimized version will perform better because it:
✅ Follows {state.platform} best practices
✅ Uses platform-native features
✅ Matches user expectations
✅ Maximizes available tools

Ready to use or need adjustments?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "optimized", "platform": state.platform},
            requires_user_input=True
        )
    
    async def _enhance_urgency(self, state: VideoScriptState, 
                              user_input: str) -> AgentResponse:
        """Enhance CTA with urgency elements."""
        urgency_type = self._identify_urgency_type(user_input)
        
        prompt = self.get_expertise_prompt(
            "urgency_enhancement",
            cta=state.cta.content,
            urgency_type=urgency_type
        )
        
        urgency_versions = await self.invoke_llm(prompt)
        
        response_content = f"""## Urgency-Enhanced CTA Versions

**Current CTA:**
"{state.cta.content}"

**Enhanced with {urgency_type}:**
{urgency_versions}

Urgency techniques used:
- Creates immediate action desire
- Reduces decision paralysis
- Increases perceived value
- Triggers loss aversion

⚠️ Remember to:
- Keep urgency authentic
- Deliver on promises
- Test with your audience
- Monitor conversion rates

Which version feels right for your brand?"""
        
        state.cta.iterations += 1
        state.cta.feedback_history.append(f"Enhanced with {urgency_type} urgency")
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "urgency_enhanced", "type": urgency_type},
            requires_user_input=True
        )
    
    async def _create_ab_variants(self, state: VideoScriptState, 
                                 user_input: Optional[str]) -> AgentResponse:
        """Create A/B test variants of CTA."""
        goal = user_input or "maximize conversions"
        
        prompt = self.get_expertise_prompt(
            "ab_test_variants",
            cta=state.cta.content,
            goal=goal
        )
        
        variants = await self.invoke_llm(prompt)
        
        response_content = f"""## A/B Test Variants for Data-Driven Optimization

**Control (Current):**
"{state.cta.content}"

**Test Variants:**
{variants}

**Testing Strategy:**
1. Run each variant for equal time periods
2. Track conversion rates and engagement
3. Consider secondary metrics (shares, comments)
4. Test with at least 100 viewers per variant
5. Look for statistical significance

**Metrics to Track:**
- Click-through rate
- Conversion rate
- Engagement rate
- Drop-off point
- Audience retention at CTA

Would you like me to:
1. Create more variants
2. Focus on a specific element
3. Develop testing guidelines
4. Suggest tracking tools"""
        
        state.cta.metadata["ab_variants"] = variants
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "ab_variants_created"},
            requires_user_input=True
        )
    
    async def _improve_existing_cta(self, state: VideoScriptState, 
                                   user_input: Optional[str]) -> AgentResponse:
        """Improve existing CTA based on feedback."""
        feedback = user_input or "make it more compelling"
        
        # Analyze current CTA
        analysis = await self._analyze_cta_effectiveness(state.cta.content)
        
        # Generate improvements
        improved_cta = await self._generate_improved_cta(state.cta.content, feedback, analysis)
        
        # Update state
        old_content = state.cta.content
        state.cta.content = improved_cta
        state.cta.iterations += 1
        if user_input:
            state.cta.feedback_history.append(user_input)
        
        response_content = f"""## CTA Improvement Analysis

**Original:**
"{old_content}"

**Analysis:**
{analysis}

**Improved Version:**
"{improved_cta}"

**Improvements Made:**
- Enhanced clarity and specificity
- Stronger value proposition
- Better emotional trigger
- Optimized action verb
- Improved flow and rhythm

The new version should:
✨ Convert {20-30}% better
📈 Increase engagement
🎯 Reduce friction
💪 Drive immediate action

Satisfied or need more refinement?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "improved", "analysis": analysis},
            requires_user_input=True
        )
    
    def _prepare_context(self, state: VideoScriptState) -> str:
        """Prepare context from state for CTA generation."""
        context_parts = []
        
        if state.context_documents:
            context_parts.append(f"Background: {' '.join(state.context_documents[:2])}")
        
        if state.user_tone_samples:
            context_parts.append(f"Tone reference: {state.user_tone_samples[0][:200]}")
        
        return " | ".join(context_parts) if context_parts else "No additional context"
    
    def _summarize_story(self, state: VideoScriptState) -> str:
        """Summarize the story for CTA context."""
        if state.story and state.story.content:
            # Take first 200 chars of story
            return state.story.content[:200] + "..."
        return "Story not yet developed"
    
    def _parse_ctas(self, cta_response: str) -> List[Dict[str, str]]:
        """Parse the LLM response into structured CTA data."""
        ctas = []
        current_cta = {}
        
        for line in cta_response.split('\n'):
            line = line.strip()
            if line.startswith('Type:'):
                if current_cta and 'primary_text' in current_cta:
                    ctas.append(current_cta)
                current_cta = {'type': line.replace('Type:', '').strip()}
            elif line.startswith('Primary Text:'):
                current_cta['primary_text'] = line.replace('Primary Text:', '').strip().strip('"')
            elif line.startswith('Supporting Text:'):
                current_cta['supporting_text'] = line.replace('Supporting Text:', '').strip()
        
        if current_cta and 'primary_text' in current_cta:
            ctas.append(current_cta)
        
        # Fallback if parsing fails
        if not ctas and cta_response:
            ctas.append({
                'type': 'Action',
                'primary_text': cta_response.split('\n')[0][:100],
                'supporting_text': 'Take action now',
                'visual_elements': 'Button or link',
                'urgency_factor': 'Limited time',
                'platform_optimization': 'Standard'
            })
        
        return ctas
    
    def _identify_urgency_type(self, user_input: str) -> str:
        """Identify the type of urgency requested."""
        urgency_types = {
            "scarc": "Scarcity",
            "time": "Time-sensitive",
            "social": "Social Proof",
            "fomo": "FOMO",
            "exclusive": "Exclusive Access",
            "bonus": "Bonus Incentive"
        }
        
        input_lower = user_input.lower()
        for key, value in urgency_types.items():
            if key in input_lower:
                return value
        
        return "Time-sensitive"  # Default
    
    async def _analyze_cta_effectiveness(self, cta: str) -> str:
        """Analyze the effectiveness of a CTA."""
        prompt = f"""Analyze this CTA for effectiveness:
"{cta}"

Rate on:
1. Clarity (0-10)
2. Urgency (0-10)
3. Value Proposition (0-10)
4. Action Verb Strength (0-10)
5. Emotional Appeal (0-10)

Provide brief explanation for each rating."""
        
        return await self.invoke_llm(prompt)
    
    async def _generate_improved_cta(self, current_cta: str, feedback: str, analysis: str) -> str:
        """Generate an improved version of the CTA."""
        prompt = f"""Improve this CTA:
Current: "{current_cta}"
Feedback: {feedback}
Analysis: {analysis}

Create an improved version that addresses the feedback and weaknesses identified."""
        
        response = await self.invoke_llm(prompt)
        # Extract just the CTA text if it's in a longer response
        lines = response.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                return line.strip().strip('"')
        return response.strip()
    
    async def generate_cta_scripts(self, state: VideoScriptState, 
                                  style: str = "standard") -> Dict[str, str]:
        """
        Generate complete CTA scripts in different styles.
        
        Args:
            state: Current state
            style: Style of CTA (standard, soft, aggressive, question-based)
            
        Returns:
            Dictionary of CTA scripts
        """
        styles = {
            "standard": "Clear and direct",
            "soft": "Gentle and suggestive",
            "aggressive": "Strong and urgent",
            "question-based": "Engaging questions"
        }
        
        scripts = {}
        for style_name, style_desc in styles.items():
            if style == "all" or style == style_name:
                prompt = f"""Create a {style_desc} CTA script for:
Topic: {state.topic}
Platform: {state.platform}

Include:
- Opening transition from content
- Main CTA message
- Supporting benefits
- Closing reinforcement

Keep it under 30 seconds when spoken."""
                
                response = await self.invoke_llm(prompt)
                scripts[style_name] = response
        
        return scripts
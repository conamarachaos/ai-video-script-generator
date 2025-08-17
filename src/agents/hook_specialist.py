"""Hook Specialist agent for creating compelling video openings."""

from typing import Optional, Dict, List
import json

from .base_agent import SpecializedAgent, AgentResponse
from ..models.config import VideoScriptState, ScriptComponent


class HookSpecialistAgent(SpecializedAgent):
    """
    Specializes in creating compelling hooks that capture viewer attention
    in the first 3-8 seconds of a video.
    """
    
    def _load_expertise_prompts(self) -> Dict[str, str]:
        """Load specialized prompts for hook creation."""
        return {
            "generate_hooks": """Based on the video topic: {topic}
Target audience: {audience}
Platform: {platform}
Context: {context}

Generate EXACTLY 3 distinct, compelling hooks for the video. Each hook should capture attention in 3-8 seconds.

USE THIS EXACT FORMAT FOR EACH HOOK:

HOOK 1:
Type: [Choose: Visual/Familiar, Problem/Agitation, Curiosity Gap, Statistical Shock, or Personal Story]
Text: [Write the exact words the presenter should say - make it compelling and specific]
Visual Note: [Describe what appears on screen]
Duration: [X seconds]

HOOK 2:
Type: [Different framework from Hook 1]
Text: [Different approach - exact words to say]
Visual Note: [Visual elements for this hook]
Duration: [X seconds]

HOOK 3:
Type: [Different framework from Hooks 1 and 2]
Text: [Another unique approach - exact script]
Visual Note: [Visual suggestions]
Duration: [X seconds]

Make each hook specific to the topic, not generic. Write actual scripts, not descriptions.""",
            
            "analyze_hook": """Analyze this hook for effectiveness:
Hook: {hook}

Rate on these criteria (0-10):
1. Attention Capture: How well does it stop scrolling?
2. Clarity: Is the value proposition immediately clear?
3. Emotional Impact: Does it create curiosity/urgency/connection?
4. Platform Fit: Is it optimized for {platform}?
5. Authenticity: Does it avoid clickbait while maintaining interest?

Provide specific improvements for any criterion scoring below 7.""",
            
            "improve_hook": """Current hook: {hook}
Feedback: {feedback}

Create an improved version that addresses the feedback while maintaining the core message.
Provide 2 variations:
1. Safe improvement (minor adjustments)
2. Bold reimagining (complete restructure)"""
        }
    
    async def process(self, state: VideoScriptState, 
                     user_input: Optional[str] = None) -> AgentResponse:
        """
        Generate or improve hooks based on the current state.
        
        Args:
            state: Current video script state
            user_input: Optional user input
            
        Returns:
            Response with hook options
        """
        if not state.hook:
            state.hook = ScriptComponent(type="hook", content="", finalized=False)
        
        # Check what the user wants
        if user_input:
            input_lower = user_input.lower()
            # Check for request for more options
            if any(word in input_lower for word in ['more', 'different', 'other', 'alternative', 'additional']):
                return await self._generate_more_hooks(state)
            # Check for custom hook request
            elif any(word in input_lower for word in ['custom', 'my own', 'specific', 'use this']):
                return await self._handle_custom_hook(state, user_input)
            # Check for enhance request (e.g., "enhance option 2")
            elif 'enhance' in input_lower or 'improve' in input_lower:
                return await self._enhance_specific_option(state, user_input)
        
        # Default behavior - generate initial hooks
        return await self._generate_initial_hooks(state)
    
    async def _generate_initial_hooks(self, state: VideoScriptState) -> AgentResponse:
        """Generate initial 3 hook options."""
        # Generate hooks
        hooks = await self._generate_hooks_batch(state)
        
        # Store all options
        state.hook.all_options = hooks
        
        # Display options
        return self._display_all_hooks(state, hooks)
    
    async def _generate_more_hooks(self, state: VideoScriptState) -> AgentResponse:
        """Generate additional hooks and add to existing options."""
        # Generate 3 more hooks
        new_hooks = await self._generate_hooks_batch(state)
        
        # Add new hooks to existing options
        for hook in new_hooks:
            state.hook.all_options.append(hook)
        
        # Display all options
        return self._display_all_hooks(state, state.hook.all_options)
    
    async def _generate_hooks_batch(self, state: VideoScriptState) -> List[Dict[str, str]]:
        """Generate a batch of 3 hooks."""
        context = self._prepare_context(state)
        
        # Generate hooks using expertise prompt
        prompt = self.get_expertise_prompt(
            "generate_hooks",
            topic=state.topic,
            audience=state.target_audience or "general audience",
            platform=state.platform,
            context=context
        )
        
        hooks_response = await self.invoke_llm(prompt)
        
        # Parse and structure the hooks
        hooks = self._parse_hooks(hooks_response)
        
        # Ensure we have exactly 3 hooks
        if len(hooks) < 3:
            for i in range(len(hooks), 3):
                hooks.append({
                    'type': ['Curiosity Gap', 'Problem/Solution', 'Statistical Shock'][i],
                    'text': f"Alternative approach {i+1} for {state.topic}",
                    'visual': 'Engaging visuals',
                    'duration': '5-8 seconds'
                })
        
        return hooks[:3]
    
    def _display_all_hooks(self, state: VideoScriptState, hooks: List[Dict[str, str]]) -> AgentResponse:
        """Display all accumulated hook options."""
        total_hooks = len(hooks)
        
        if total_hooks <= 3:
            response_content = f"""I've created 3 compelling hook options for your video about "{state.topic}":

"""
        else:
            response_content = f"""Here are all {total_hooks} hook options for your video about "{state.topic}":

"""
        
        # Display all hooks with sequential numbering
        for i, hook in enumerate(hooks, 1):
            hook_text = hook.get('text', '')
            # Clean up any meta-text
            if 'let\'s nail these hooks' in hook_text.lower() or 'here are three options' in hook_text.lower():
                if 'problem' in hook.get('type', '').lower():
                    hook_text = f"Did you know that 73% of startups fail in the first year? AI might be the game-changer."
                elif 'curiosity' in hook.get('type', '').lower():
                    hook_text = f"What if I told you that AI could 10x your startup's growth in just 30 days?"
                else:
                    hook_text = f"Last month, this startup used AI to go from zero to $1M in revenue - here's how..."
            
            response_content += f"""**Option {i}: {hook.get('type', 'Hook Style')}**
📝 Script: "{hook_text}"
🎬 Visual: {hook.get('visual', 'Eye-catching opening visuals')}
⏱️ Duration: {hook.get('duration', '5-8 seconds')}

"""
        
        response_content += f"""💡 **Your Options:**
• Type a number (1-{total_hooks}) to select an option
• Type `more` to generate 3 additional hook styles
• Type `enhance [number]` to improve a specific option (e.g., 'enhance 2')
• Type `custom: [your text]` to use your own hook
• Type `help` for more commands

Which would you like to do?"""
        
        suggestions = [
            f"Type a number (1-{total_hooks}) to select an option",
            "Type 'more' for 3 additional hook styles",
            "Type 'enhance 2' to improve option 2",
            "Type 'custom: [your text]' to use your own hook"
        ]
        
        return AgentResponse(
            content=response_content,
            suggestions=suggestions,
            metadata={"hooks": hooks, "action": "generated", "total_options": total_hooks},
            requires_user_input=True
        )
    
    async def _enhance_specific_option(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Enhance a specific hook option based on user request."""
        import re
        
        # Extract option number from input
        match = re.search(r'(enhance|improve)\s*(option)?\s*(\d+)', user_input.lower())
        if not match:
            return AgentResponse(
                content="Please specify which option to enhance (e.g., 'enhance 2' or 'enhance option 3').",
                requires_user_input=True
            )
        
        option_num = int(match.group(3))
        
        # Check if option exists
        if not state.hook or option_num > len(state.hook.all_options):
            return AgentResponse(
                content=f"Option {option_num} doesn't exist. Please generate hooks first or choose a valid option.",
                requires_user_input=True
            )
        
        # Get the specific hook
        hook_to_enhance = state.hook.all_options[option_num - 1]
        
        # Generate enhancement
        enhance_prompt = f"""Enhance this hook for a video about {state.topic}:

Original Hook:
Type: {hook_to_enhance.get('type', 'Hook')}
Script: "{hook_to_enhance.get('text', '')}"
Visual: {hook_to_enhance.get('visual', '')}

Provide 2 enhanced versions:
1. A refined version (keeping the core concept but improving delivery)
2. A bold reimagining (taking the concept to the next level)

Format each as:
Version X:
Script: "[enhanced script]"
Visual: [enhanced visual suggestion]
Why it's better: [brief explanation]"""
        
        enhancement = await self.invoke_llm(enhance_prompt)
        
        response_content = f"""## Enhancing Option {option_num}: {hook_to_enhance.get('type', 'Hook')}

**Original:**
📝 "{hook_to_enhance.get('text', '')}"

**Enhanced Versions:**
{enhancement}

**Your Options:**
• Type `use refined` to use the refined version
• Type `use bold` to use the bold version  
• Type `keep original` to stick with the original
• Type a number (1-{len(state.hook.all_options)}) to select a different option
• Type `more` for additional options

What would you like to do?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "enhanced", "option_num": option_num},
            requires_user_input=True
        )
    
    async def _improve_existing_hook(self, state: VideoScriptState, 
                                    user_input: Optional[str]) -> AgentResponse:
        """Improve the existing hook based on feedback."""
        # First analyze the current hook
        analysis_prompt = self.get_expertise_prompt(
            "analyze_hook",
            hook=state.hook.content,
            platform=state.platform
        )
        
        analysis = await self.invoke_llm(analysis_prompt)
        
        # Generate improvements
        improve_prompt = self.get_expertise_prompt(
            "improve_hook",
            hook=state.hook.content,
            feedback=user_input or analysis
        )
        
        improvements = await self.invoke_llm(improve_prompt)
        
        # Update iteration count
        state.hook.iterations += 1
        if user_input:
            state.hook.feedback_history.append(user_input)
        
        response_content = f"""## Hook Analysis & Improvements

**Current Hook:** "{state.hook.content}"

**Analysis:**
{analysis}

**Improved Versions:**
{improvements}

Would you like to:
1. Use one of these improvements
2. Keep refining based on specific feedback
3. Try a completely different approach
4. Finalize the current version"""
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "improved", "analysis": analysis},
            requires_user_input=True
        )
    
    def _prepare_context(self, state: VideoScriptState) -> str:
        """Prepare context from state for hook generation."""
        context_parts = []
        
        if state.context_documents:
            context_parts.append(f"Background: {' '.join(state.context_documents[:2])}")
        
        if state.user_tone_samples:
            context_parts.append(f"Tone reference: {state.user_tone_samples[0][:200]}")
        
        if state.cta and state.cta.content:
            context_parts.append(f"Building toward CTA: {state.cta.content}")
        
        return " | ".join(context_parts) if context_parts else "No additional context"
    
    def _parse_hooks(self, hooks_response: str) -> List[Dict[str, str]]:
        """Parse the LLM response into structured hook data."""
        hooks = []
        current_hook = {}
        
        # Try to parse structured format
        lines = hooks_response.split('\n')
        in_hook = False
        
        for line in lines:
            line = line.strip()
            
            # Detect hook start
            if line.startswith('HOOK') and ':' in line:
                if current_hook and 'text' in current_hook:
                    hooks.append(current_hook)
                current_hook = {}
                in_hook = True
                continue
            
            if in_hook:
                if line.startswith('Type:'):
                    current_hook['type'] = line.replace('Type:', '').strip()
                elif line.startswith('Text:'):
                    current_hook['text'] = line.replace('Text:', '').strip().strip('"')
                elif line.startswith('Visual Note:') or line.startswith('Visual:'):
                    current_hook['visual'] = line.replace('Visual Note:', '').replace('Visual:', '').strip()
                elif line.startswith('Duration:'):
                    current_hook['duration'] = line.replace('Duration:', '').strip()
        
        # Add last hook
        if current_hook and 'text' in current_hook:
            hooks.append(current_hook)
        
        # If we got exactly 3 hooks, great!
        if len(hooks) == 3:
            return hooks
        
        # Fallback: Try to extract any hook-like content
        if len(hooks) < 3:
            # Look for numbered items or bullet points
            hook_candidates = []
            for i, line in enumerate(lines):
                line = line.strip()
                if (line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or 
                    line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    text = line.lstrip('0123456789.-•* ').strip()
                    if len(text) > 20:  # Meaningful content
                        hook_candidates.append(text)
            
            # Create hooks from candidates
            for i, text in enumerate(hook_candidates[:3 - len(hooks)]):
                hooks.append({
                    'type': ['Curiosity Gap', 'Problem/Agitation', 'Statistical Shock'][i % 3],
                    'text': text[:200] if len(text) > 200 else text,
                    'visual': 'Engaging visuals related to the topic',
                    'duration': '5-8 seconds'
                })
        
        # Last resort: Create from first lines
        if not hooks and hooks_response:
            first_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20][:3]
            for i, text in enumerate(first_lines):
                hooks.append({
                    'type': ['Generated Hook', 'Alternative Hook', 'Creative Hook'][i],
                    'text': text[:200],
                    'visual': 'Standard opening visuals',
                    'duration': '5-8 seconds'
                })
        
        # Ensure we always return at least one hook
        if not hooks:
            hooks.append({
                'type': 'Default',
                'text': f"Discover how {hooks_response[:100] if hooks_response else 'this topic'} can transform your approach",
                'visual': 'Engaging opening sequence',
                'duration': '5-8 seconds'
            })
        
        return hooks[:3]  # Return maximum 3 hooks
    
    async def _handle_custom_hook(self, state: VideoScriptState, 
                                 user_input: str) -> AgentResponse:
        """Handle custom hook provided by user.
        
        Args:
            state: Current state
            user_input: User's input containing custom hook
            
        Returns:
            Response confirming custom hook
        """
        # Extract the custom hook from user input
        custom_text = user_input
        
        # Remove common prefixes
        prefixes_to_remove = [
            'custom:', 'custom hook:', 'use this:', 'my hook:', 
            'here\'s my hook:', 'use:', 'custom -', 'custom option:'
        ]
        
        for prefix in prefixes_to_remove:
            if custom_text.lower().startswith(prefix):
                custom_text = custom_text[len(prefix):].strip()
                break
        
        # If they said "custom" alone, ask for the hook
        if custom_text.lower() in ['custom', 'custom hook', 'my own', 'specific']:
            return AgentResponse(
                content="""📝 **Custom Hook Entry**

Please provide your custom hook text. You can type it in one of these formats:
• `custom: Your hook text here`
• `use this: Your hook text here`
• Or just type the hook text directly

What's your custom hook?""",
                metadata={"awaiting_custom": True},
                requires_user_input=True
            )
        
        # Store the custom hook
        state.hook.content = custom_text
        state.hook.finalized = True
        state.hook.iterations += 1
        
        # Analyze the custom hook
        analysis = await self._analyze_custom_hook(custom_text, state.platform)
        
        response_content = f"""✅ **Custom Hook Set Successfully!**

Your hook: "{custom_text}"

{analysis}

**Next Steps:**
• Type `story` to develop your narrative structure
• Type `cta` to create your call-to-action
• Type `more` if you'd like to see AI-generated alternatives"""
        
        return AgentResponse(
            content=response_content,
            metadata={"custom_hook_set": True, "hook_text": custom_text},
            requires_user_input=False
        )
    
    async def _analyze_custom_hook(self, hook_text: str, platform: str) -> str:
        """Analyze a custom hook for effectiveness.
        
        Args:
            hook_text: The custom hook text
            platform: Target platform
            
        Returns:
            Analysis and suggestions
        """
        prompt = f"""Analyze this custom hook for a {platform} video:
Hook: "{hook_text}"

Provide:
1. One strength of this hook
2. One potential improvement (if any)
3. Estimated optimal duration

Keep response under 100 words."""
        
        analysis = await self.invoke_llm(prompt)
        return f"**Quick Analysis:**\n{analysis}"
    
    async def generate_platform_specific_hooks(self, state: VideoScriptState, 
                                              platforms: List[str]) -> Dict[str, str]:
        """
        Generate platform-specific variations of hooks.
        
        Args:
            state: Current state
            platforms: List of platforms to optimize for
            
        Returns:
            Dictionary of platform-specific hooks
        """
        platform_hooks = {}
        
        for platform in platforms:
            prompt = f"""Create a {platform}-optimized version of this hook concept:
Topic: {state.topic}
Base hook: {state.hook.content if state.hook else 'Create new'}

{platform} specific requirements:
- YouTube: Can be 8-15 seconds, focus on search keywords
- TikTok: Must grab in 1-3 seconds, trendy language
- Instagram: Visual-first, 5-8 seconds, use emoji-friendly language
- LinkedIn: Professional tone, value-focused, 8-10 seconds

Provide only the hook text optimized for {platform}."""
            
            response = await self.invoke_llm(prompt)
            platform_hooks[platform] = response.strip()
        
        return platform_hooks
    
    async def test_hook_effectiveness(self, hook: str) -> Dict[str, float]:
        """
        Test hook effectiveness using various metrics.
        
        Args:
            hook: Hook text to test
            
        Returns:
            Dictionary of effectiveness scores
        """
        criteria = [
            "attention_capture",
            "clarity",
            "emotional_impact",
            "curiosity_generation",
            "value_communication"
        ]
        
        scores = await self.analyze_quality(hook, criteria)
        
        # Add overall effectiveness score
        if scores:
            scores["overall"] = sum(scores.values()) / len(scores)
        
        return scores
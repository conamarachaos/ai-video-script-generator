"""Enhanced Story Architect agent with act-by-act workflow and timing customization."""

from typing import Optional, Dict, Any, List
import re
from .base_agent import BaseAgent, AgentResponse
from ..models.config import VideoScriptState, ScriptComponent


class EnhancedStoryArchitect:
    """Enhanced methods for Story Architect to support act-by-act development."""
    
    @staticmethod
    def calculate_act_duration(total_duration: str, act_num: int) -> str:
        """Calculate duration for specific act based on total video length."""
        # Extract numeric value
        match = re.search(r'(\d+)(?:-(\d+))?', total_duration)
        if not match:
            return "a few seconds"
        
        min_val = int(match.group(1))
        max_val = int(match.group(2)) if match.group(2) else min_val
        avg_val = (min_val + max_val) / 2
        
        # Determine if seconds or minutes
        is_seconds = 'second' in total_duration
        
        # Act proportions (Act 1: 20%, Act 2: 60%, Act 3: 20%)
        proportions = {1: 0.2, 2: 0.6, 3: 0.2}
        act_duration = avg_val * proportions.get(act_num, 0.33)
        
        if is_seconds:
            return f"{int(act_duration)} seconds"
        else:
            if act_duration < 1:
                return f"{int(act_duration * 60)} seconds"
            else:
                return f"{act_duration:.1f} minutes"
    
    @staticmethod
    def ask_about_timing(state: VideoScriptState) -> AgentResponse:
        """Ask user about video duration preference."""
        platform_suggestions = {
            'tiktok': '15-60 seconds',
            'instagram': '30 seconds - 2 minutes',
            'youtube': '3-10 minutes',
            'general': '1-5 minutes'
        }
        
        suggested_duration = platform_suggestions.get(state.platform, '2-3 minutes')
        
        response_content = f"""**Before we structure your story, let's set the timing:**

How long will your video be? This helps me pace the narrative perfectly.

📱 Recommended for {state.platform}: **{suggested_duration}**

Common durations:
• **Short-form** (30-60 seconds): TikTok, Reels - Quick, punchy, single message
• **Medium** (1-3 minutes): Instagram, LinkedIn - Clear problem-solution
• **Long-form** (5-10 minutes): YouTube - Detailed explanations
• **Extended** (10+ minutes): Tutorials, deep dives

Type your preference (e.g., "2 minutes", "60 seconds", "5-7 minutes")
Or press Enter to use {suggested_duration}
"""
        
        # Mark that we're awaiting timing
        state.story.metadata['awaiting_timing'] = True
        
        return AgentResponse(
            content=response_content,
            metadata={"awaiting": "timing_preference"},
            requires_user_input=True
        )
    
    @staticmethod
    def handle_timing_preference(state: VideoScriptState, user_input: str) -> str:
        """Extract and store timing preference from user input."""
        # Default based on platform
        platform_defaults = {
            'tiktok': '30-60 seconds',
            'instagram': '1-2 minutes',
            'youtube': '5-7 minutes',
            'general': '2-3 minutes'
        }
        
        if not user_input or user_input.strip() == '':
            # User pressed Enter, use default
            duration = platform_defaults.get(state.platform, '2-3 minutes')
        else:
            # Try to extract duration from input
            # First check for duration with unit
            duration_match = re.search(r'(\d+(?:-\d+)?\s*(?:second|minute|min|sec|s|m))', user_input.lower())
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
                bare_number_match = re.search(r'^(\d+)(?:-(\d+))?$', user_input.strip())
                if bare_number_match:
                    if bare_number_match.group(2):  # Range like "5-7"
                        duration = f"{bare_number_match.group(1)}-{bare_number_match.group(2)} minutes"
                    else:  # Single number like "10"
                        duration = f"{bare_number_match.group(1)} minutes"
                else:
                    duration = platform_defaults.get(state.platform, '2-3 minutes')
        
        state.story.metadata['video_duration'] = duration
        state.story.metadata['awaiting_timing'] = False
        return duration
    
    @staticmethod
    def create_act_development_prompt(state: VideoScriptState, duration: str, act_num: int) -> str:
        """Create prompt for act-by-act development."""
        act_duration = EnhancedStoryArchitect.calculate_act_duration(duration, act_num)
        
        response_content = f"""
---

**🎬 Now let's develop Act {act_num} together!**

Great structure! Now let's bring Act {act_num} to life. 

**🔥 Act {act_num} Focus:** {act_duration} of content

**Your turn!** Share your ideas for Act {act_num}:
• What specific points will you cover?
• Any stats or examples in mind?
• Need me to research anything?

**Quick commands:**
• `draft: [your script]` - Share your script draft for feedback
• `enhance` - Improve your current draft
• `research: [topic]` - I'll find relevant data/statistics
• `example: [concept]` - I'll suggest case studies
• `next act` - Move to Act {act_num + 1} when ready
• `show script` - See your complete script so far

What would you like to explore for Act {act_num}?"""
        
        return response_content
    
    @staticmethod
    async def process_act_development(agent, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Process user input during act development."""
        current_act = state.story.metadata.get('current_act', 1)
        
        # Initialize acts_content if needed
        if 'acts_content' not in state.story.metadata:
            state.story.metadata['acts_content'] = {}
        
        # Check for commands - handle variations
        user_lower = user_input.lower().strip()
        
        # Research command
        if user_lower.startswith('research:'):
            topic = user_input[9:].strip()
            return await EnhancedStoryArchitect.research_topic(agent, state, topic, current_act)
        
        # Example command - multiple variations
        if (user_lower.startswith('example:') or 
            user_lower.startswith('examples:') or
            'add example' in user_lower or
            'add some example' in user_lower or
            'can you add example' in user_lower or
            'give me example' in user_lower):
            
            # Extract concept if provided, otherwise use general
            if ':' in user_input:
                concept = user_input.split(':', 1)[1].strip()
            else:
                concept = f"relevant to Act {current_act} content"
            
            return await EnhancedStoryArchitect.suggest_examples(agent, state, concept, current_act)
        
        # Handle "use enhanced" or "keep original" commands FIRST (before general enhancement)
        enhanced_draft = state.story.metadata.get('enhanced_draft')
        
        # Check if user wants to use enhanced but no enhanced draft exists
        if 'use enhanced' in user_lower and not enhanced_draft:
            return AgentResponse(
                content="❌ **No enhanced version available.** Please type `enhance` first to create an enhanced version of your draft.",
                metadata={"current_act": current_act, "error": "no_enhanced_draft"},
                requires_user_input=True
            )
        
        if enhanced_draft:
            if 'use enhanced' in user_lower:
                # Ensure acts_content is initialized
                if 'acts_content' not in state.story.metadata:
                    state.story.metadata['acts_content'] = {}
                
                # Validate enhanced draft exists and has content
                if not enhanced_draft or enhanced_draft.strip() == '':
                    return AgentResponse(
                        content="❌ **Enhanced draft is empty or invalid.** Please try enhancing again.",
                        metadata={"current_act": current_act, "error": "empty_enhanced_draft"},
                        requires_user_input=True
                    )
                
                # Replace the draft
                state.story.metadata['acts_content'][f'act_{current_act}'] = enhanced_draft
                del state.story.metadata['enhanced_draft']
                
                # Show the updated draft for confirmation
                duration = state.story.metadata.get('video_duration', '2-3 minutes')
                act_duration = EnhancedStoryArchitect.calculate_act_duration(duration, current_act)
                
                response_content = f"""✅ **Enhanced version is now your Act {current_act} draft!**

**📝 Your updated Act {current_act} ({act_duration}):**
```
{enhanced_draft}
```

**Next steps:**
• Continue editing this act (just keep typing)
• Type `research: [topic]` for data
• Type `example: [concept]` for cases  
• Type `next act` to move to Act {current_act + 1}
• Type `show script` to see everything

Great improvement! What would you like to do next?"""
                
                return AgentResponse(
                    content=response_content,
                    metadata={"current_act": current_act, "draft_replaced": True},
                    requires_user_input=True
                )
            elif 'keep original' in user_lower:
                # Ensure acts_content is initialized
                if 'acts_content' not in state.story.metadata:
                    state.story.metadata['acts_content'] = {}
                
                # Get original draft (may be empty)
                original_draft = state.story.metadata['acts_content'].get(f'act_{current_act}', '')
                del state.story.metadata['enhanced_draft']
                
                duration = state.story.metadata.get('video_duration', '2-3 minutes')
                act_duration = EnhancedStoryArchitect.calculate_act_duration(duration, current_act)
                
                response_content = f"""✅ **Keeping your original draft for Act {current_act}**

**📝 Your Act {current_act} ({act_duration}):**
```
{original_draft if original_draft else '[No draft yet - start writing!]'}
```

**Next steps:**
• Continue editing this act (just keep typing)
• Type `enhance` to try enhancing again
• Type `research: [topic]` for data
• Type `example: [concept]` for cases
• Type `next act` when ready to move on
• Type `show script` to see everything

Continue developing Act {current_act} or move to the next when ready!"""
                
                return AgentResponse(
                    content=response_content,
                    metadata={"current_act": current_act, "kept_original": True},
                    requires_user_input=True
                )
        
        # Handle draft command FIRST (before enhancement keywords)
        draft_with_colon = user_lower.startswith('draft:')
        draft_with_space = user_lower.startswith('draft ') and len(user_input.strip()) > 6
        
        if draft_with_colon or draft_with_space:
            # Extract draft content after "draft:" or "draft "
            if draft_with_colon:
                draft_content = user_input[6:].strip()  # Remove "draft:"
            else:
                draft_content = user_input[6:].strip()  # Remove "draft "
            
            if not draft_content:
                return AgentResponse(
                    content="**Please provide your draft content after 'draft:'**\n\nExample: `draft: Your script content here...`",
                    metadata={"current_act": current_act, "error": "empty_draft"},
                    requires_user_input=True
                )
            
            return await EnhancedStoryArchitect.review_draft(agent, state, draft_content, current_act, False)
        
        # Enhancement command - improve existing draft (after draft command)
        enhance_keywords = ['enhance', 'improve', 'make better', 'refine', 'polish', 'upgrade', 'strengthen', 'optimize']
        # Only trigger enhance if it's a standalone command, not part of draft content
        if any(keyword in user_lower for keyword in enhance_keywords) and not draft_with_colon and not draft_with_space:
            # Additional check: only if it's a short command (not a long draft)
            if len(user_input) < 100:  # Enhance commands are typically short
                return await EnhancedStoryArchitect.enhance_draft(agent, state, current_act)
        
        if 'next act' in user_input.lower():
            return await EnhancedStoryArchitect.move_to_next_act(agent, state)
        
        if 'show script' in user_input.lower():
            return EnhancedStoryArchitect.show_full_script(state)
        
        # Check if user is adding to existing draft (starts with common additions)
        add_keywords = ['also', 'additionally', 'plus', 'and', 'furthermore', 'moreover', 'in addition']
        is_addition = any(user_lower.startswith(word) for word in add_keywords)
        
        # Check if it's a question or request (not content)
        question_keywords = ['can you', 'could you', 'would you', 'please', 'help me', 'what if', 'how about']
        is_request = any(user_lower.startswith(word) for word in question_keywords)
        
        # If it's a request but not a recognized command, treat as feedback request
        if is_request:
            return await EnhancedStoryArchitect.provide_feedback(agent, state, user_input, current_act)
        
        # Default: treat as draft content (without "draft:" prefix)
        return await EnhancedStoryArchitect.review_draft(agent, state, user_input, current_act, is_addition)
    
    @staticmethod
    async def research_topic(agent, state: VideoScriptState, topic: str, act_num: int) -> AgentResponse:
        """Research a topic for the user."""
        research_prompt = f"""Research the following topic for a video script about {state.topic}:
Topic to research: {topic}
Context: This is for Act {act_num} of the video
Audience: {state.target_audience}

Provide:
1. 2-3 relevant statistics with sources
2. Current trends or insights
3. How to incorporate this into Act {act_num}

Keep it concise and actionable."""
        
        research = await agent.invoke_llm(research_prompt)
        
        # Get existing draft
        existing_draft = state.story.metadata.get('acts_content', {}).get(f'act_{act_num}', '')
        
        response_content = f"""**📊 Research Results for Act {act_num}**

{research}

**How to use this:**
• Pick the most compelling stat for your opening
• Use examples to illustrate your points
• Save sources for credibility

**📝 Your current Act {act_num} draft:**
```
{existing_draft if existing_draft else '[No draft yet - start writing!]'}
```

Continue writing or type `next act` when ready!"""
        
        return AgentResponse(
            content=response_content,
            metadata={"current_act": act_num, "research_topic": topic},
            requires_user_input=True
        )
    
    @staticmethod
    async def suggest_examples(agent, state: VideoScriptState, concept: str, act_num: int) -> AgentResponse:
        """Suggest examples or case studies."""
        example_prompt = f"""Suggest examples or case studies for:
Concept: {concept}
Video topic: {state.topic}
Act {act_num} context
Audience: {state.target_audience}

Provide:
1. 2-3 specific examples or case studies
2. Key takeaways from each
3. How to present them visually

Make them relevant and engaging."""
        
        examples = await agent.invoke_llm(example_prompt)
        
        # Get existing draft to show context
        existing_draft = state.story.metadata.get('acts_content', {}).get(f'act_{act_num}', '')
        
        response_content = f"""**💡 Example Ideas for Act {act_num}**

{examples}

**Integration tips:**
• Choose the most relatable example for your audience
• Keep examples brief but impactful
• Use visuals to reinforce the story

**📝 Your current Act {act_num} draft:**
```
{existing_draft if existing_draft else '[No draft yet - start writing!]'}
```

**How to use these examples:**
• Copy and paste relevant examples into your draft
• Modify them to fit your specific context
• Continue writing to add these examples

Continue developing Act {act_num} or type `next act` when ready!"""
        
        return AgentResponse(
            content=response_content,
            metadata={"current_act": act_num, "examples_for": concept},
            requires_user_input=True
        )
    
    @staticmethod
    async def review_draft(agent, state: VideoScriptState, draft: str, act_num: int, is_addition: bool = False) -> AgentResponse:
        """Review and provide feedback on user's draft."""
        # Handle draft storage - preserve existing content if it's an addition
        existing_draft = state.story.metadata['acts_content'].get(f'act_{act_num}', '')
        
        if is_addition and existing_draft:
            # Append to existing draft
            combined_draft = f"{existing_draft}\n\n{draft}"
            state.story.metadata['acts_content'][f'act_{act_num}'] = combined_draft
            draft_to_review = combined_draft
        else:
            # Replace or set new draft
            state.story.metadata['acts_content'][f'act_{act_num}'] = draft
            draft_to_review = draft
        
        feedback_prompt = f"""Review this Act {act_num} draft for a video about {state.topic}:

Draft:
{draft}

Provide:
1. 3 specific things that work well (be encouraging!)
2. 1-2 gentle suggestions for improvement
3. Motivation to continue

Be supportive and constructive. Use enthusiastic, positive language."""
        
        feedback = await agent.invoke_llm(feedback_prompt)
        
        # Use the appropriate draft for display
        draft = draft_to_review
        
        duration = state.story.metadata.get('video_duration', '2-3 minutes')
        act_duration = EnhancedStoryArchitect.calculate_act_duration(duration, act_num)
        
        response_content = f"""**🌟 Feedback on Act {act_num}**

{feedback}

**📝 Your Act {act_num} ({act_duration}):**
```
{draft}
```

**Progress:** Act {act_num} ✅

**Next steps:**
• Refine this act more (just keep typing)
• Type `enhance` to improve your draft
• Type `research: [topic]` for data
• Type `example: [concept]` for cases
• Type `next act` to move to Act {act_num + 1}
• Type `show script` to see everything

You're doing great! What would you like to do next?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"current_act": act_num, "act_content": draft},
            requires_user_input=True
        )
    
    @staticmethod
    async def move_to_next_act(agent, state: VideoScriptState) -> AgentResponse:
        """Move to the next act."""
        current_act = state.story.metadata.get('current_act', 1)
        
        if current_act >= 3:
            return EnhancedStoryArchitect.complete_script(state)
        
        next_act = current_act + 1
        state.story.metadata['current_act'] = next_act
        
        duration = state.story.metadata.get('video_duration', '2-3 minutes')
        
        # Get act focus based on act number
        act_focuses = {
            1: "Setup and hook - grab attention",
            2: "Main content - deliver value",
            3: "Resolution and CTA - drive action"
        }
        
        response_content = f"""**✅ Act {current_act} Complete!**

Great work on Act {current_act}! Let's move to Act {next_act}.

{EnhancedStoryArchitect.create_act_development_prompt(state, duration, next_act)}

**Act {next_act} Focus:** {act_focuses.get(next_act, "Continue the story")}

What ideas do you have for Act {next_act}?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"current_act": next_act},
            requires_user_input=True
        )
    
    @staticmethod
    def show_full_script(state: VideoScriptState) -> AgentResponse:
        """Show the complete script so far."""
        acts_content = state.story.metadata.get('acts_content', {})
        duration = state.story.metadata.get('video_duration', 'Unknown duration')
        
        script_parts = []
        for i in range(1, 4):
            act_content = acts_content.get(f'act_{i}', f'[Act {i} not written yet]')
            if act_content and act_content != f'[Act {i} not written yet]':
                act_duration = EnhancedStoryArchitect.calculate_act_duration(duration, i)
                script_parts.append(f"**Act {i} ({act_duration}):**\n{act_content}")
        
        full_script = "\n\n---\n\n".join(script_parts) if script_parts else "No acts written yet."
        
        current_act = state.story.metadata.get('current_act', 1)
        
        response_content = f"""**📜 Your Complete Script So Far**
**Video Duration:** {duration}
**Topic:** {state.topic}

---

{full_script}

---

**Current Status:** Working on Act {current_act}

Continue with Act {current_act} or type `next act` to proceed."""
        
        return AgentResponse(
            content=response_content,
            metadata={"showing_script": True, "current_act": current_act},
            requires_user_input=True
        )
    
    @staticmethod
    def complete_script(state: VideoScriptState) -> AgentResponse:
        """Complete the script and show final version."""
        acts_content = state.story.metadata.get('acts_content', {})
        duration = state.story.metadata.get('video_duration', 'Unknown duration')
        
        script_parts = []
        for i in range(1, 4):
            act_content = acts_content.get(f'act_{i}', '')
            if act_content:
                act_duration = EnhancedStoryArchitect.calculate_act_duration(duration, i)
                script_parts.append(f"**Act {i} ({act_duration}):**\n{act_content}")
        
        full_script = "\n\n---\n\n".join(script_parts)
        
        response_content = f"""**🎉 Script Complete!**

Fantastic work! You've completed all three acts of your video script.

**📜 Final Script ({duration})**
**Topic:** {state.topic}

---

{full_script}

---

**✨ Great job!** Your script has:
• Strong opening hook (Act 1)
• Engaging main content (Act 2)
• Clear resolution (Act 3)

**Next steps:**
• Type `cta` to create your call-to-action
• Type `review` to see everything together
• Type `export` to save your script

What would you like to do next?"""
        
        state.story.finalized = True
        
        return AgentResponse(
            content=response_content,
            metadata={"script_complete": True},
            requires_user_input=True
        )
    
    @staticmethod
    async def enhance_draft(agent, state: VideoScriptState, act_num: int) -> AgentResponse:
        """Enhance the existing draft for the current act."""
        existing_draft = state.story.metadata.get('acts_content', {}).get(f'act_{act_num}', '')
        
        if not existing_draft:
            return AgentResponse(
                content="**No draft to enhance yet!** Please write your initial draft first, then I can help enhance it.",
                metadata={"current_act": act_num},
                requires_user_input=True
            )
        
        enhance_prompt = f"""Enhance this Act {act_num} draft for a video about {state.topic}.
        
Original draft:
{existing_draft}

Provide an enhanced version that:
1. Keeps the core message and structure
2. Improves clarity and impact
3. Adds vivid details or examples where appropriate
4. Strengthens emotional connections
5. Improves flow and transitions

Provide the complete enhanced draft, not just suggestions."""
        
        enhanced_draft = await agent.invoke_llm(enhance_prompt)
        
        response_content = f"""**✨ Enhanced Version of Act {act_num}**

**Original Draft:**
```
{existing_draft}
```

**Enhanced Version:**
```
{enhanced_draft}
```

**Options:**
• Type `use enhanced` to replace your draft with this version
• Type `keep original` to stick with your version
• Continue editing either version
• Type `next act` when ready to move on

What would you like to do?"""
        
        # Store the enhanced version temporarily
        state.story.metadata['enhanced_draft'] = enhanced_draft
        
        return AgentResponse(
            content=response_content,
            metadata={"current_act": act_num, "enhancement_provided": True},
            requires_user_input=True
        )
    
    @staticmethod
    async def provide_feedback(agent, state: VideoScriptState, user_input: str, act_num: int) -> AgentResponse:
        """Provide feedback or help based on user's request."""
        existing_draft = state.story.metadata.get('acts_content', {}).get(f'act_{act_num}', '')
        
        feedback_prompt = f"""The user is asking for help with Act {act_num} of their video about {state.topic}.
        
User's request: {user_input}
Current draft: {existing_draft if existing_draft else 'No draft yet'}

Provide helpful, specific guidance. Be encouraging and constructive."""
        
        feedback = await agent.invoke_llm(feedback_prompt)
        
        response_content = f"""**💭 Response to Your Request**

{feedback}

**📝 Your current Act {act_num} draft:**
```
{existing_draft if existing_draft else '[No draft yet - start writing!]'}
```

**Next steps:**
• Continue writing to develop this act
• Type `enhance` to improve your draft
• Type `example: [concept]` for examples
• Type `research: [topic]` for data
• Type `next act` when ready
• Type `show script` to see everything

What would you like to do?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"current_act": act_num, "feedback_provided": True},
            requires_user_input=True
        )
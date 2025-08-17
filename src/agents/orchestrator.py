"""Orchestrator agent that manages the workflow and coordinates other agents."""

from typing import Optional, Dict, Any, List, Literal
from enum import Enum

from .base_agent import BaseAgent, AgentResponse
from ..models.config import VideoScriptState, ScriptComponent


class WorkflowIntent(str, Enum):
    """User intents that can be detected."""
    START_HOOK = "start_hook"
    START_STORY = "start_story"
    START_CTA = "start_cta"
    REVIEW_SCRIPT = "review_script"
    PROVIDE_CONTEXT = "provide_context"
    ADD_TONE_SAMPLE = "add_tone_sample"
    REQUEST_FEEDBACK = "request_feedback"
    FINALIZE_COMPONENT = "finalize_component"
    UNCLEAR = "unclear"


class OrchestratorAgent(BaseAgent):
    """
    The Orchestrator manages the entire workflow, routing between agents,
    tracking state, and providing high-level guidance.
    """
    
    def _create_system_prompt(self) -> str:
        """Create specialized system prompt for the Orchestrator."""
        base_prompt = super()._create_system_prompt()
        return f"""{base_prompt}

As the Orchestrator, you have additional responsibilities:
1. Guide users through the video script creation process
2. Detect user intent and route to appropriate specialist agents
3. Maintain project coherence across all components
4. Provide constructive feedback using the 5:1 positive-to-constructive ratio
5. Challenge assumptions when necessary to improve quality
6. Ensure smooth transitions between different workflow stages

Interaction Protocol:
- Be direct and professional - NO theatrical behaviors (no clearing throat, no stage directions, no physical actions)
- When a user provides a new idea or draft, follow this protocol:
  1. Acknowledge and validate the strengths of the idea
  2. Ask 1-2 probing, open-ended questions to encourage deeper reflection
  3. If the idea is conventional, propose 2-3 distinct alternatives framed as "What if we explored..." or "Another interesting angle could be..."

IMPORTANT: Communicate clearly and directly. Do not include any roleplay elements, theatrical descriptions, or physical actions in your responses.
  
Remember: You are not just coordinating, but actively collaborating to produce the best possible script."""
    
    async def process(self, state: VideoScriptState, 
                     user_input: Optional[str] = None) -> AgentResponse:
        """
        Process user input and current state to determine next action.
        
        Args:
            state: Current video script state
            user_input: User's input message
            
        Returns:
            Orchestrator's response with routing information
        """
        # Detect user intent
        intent = await self._detect_intent(state, user_input)
        
        # Generate appropriate response based on intent
        if intent == WorkflowIntent.START_HOOK:
            return await self._handle_start_hook(state, user_input)
        elif intent == WorkflowIntent.START_STORY:
            return await self._handle_start_story(state, user_input)
        elif intent == WorkflowIntent.START_CTA:
            return await self._handle_start_cta(state, user_input)
        elif intent == WorkflowIntent.REVIEW_SCRIPT:
            return await self._handle_review_script(state)
        elif intent == WorkflowIntent.PROVIDE_CONTEXT:
            return await self._handle_provide_context(state, user_input)
        elif intent == WorkflowIntent.ADD_TONE_SAMPLE:
            return await self._handle_add_tone_sample(state, user_input)
        elif intent == WorkflowIntent.REQUEST_FEEDBACK:
            return await self._handle_request_feedback(state, user_input)
        elif intent == WorkflowIntent.FINALIZE_COMPONENT:
            return await self._handle_finalize_component(state, user_input)
        else:
            return await self._handle_unclear_intent(state, user_input)
    
    async def _detect_intent(self, state: VideoScriptState, 
                            user_input: Optional[str]) -> WorkflowIntent:
        """
        Detect user's intent from their input.
        
        Args:
            state: Current state
            user_input: User's message
            
        Returns:
            Detected workflow intent
        """
        if not user_input:
            return WorkflowIntent.UNCLEAR
        
        input_lower = user_input.lower()
        
        # Quick pattern matching for common intents
        # Check for option selection patterns first
        import re
        option_patterns = [
            r'choose option \d',
            r'option \d',
            r'use option \d',
            r'select option \d',
            r'go with option \d',
            r'^[123]$',
            r'first|second|third'
        ]
        
        for pattern in option_patterns:
            if re.search(pattern, input_lower):
                # This is an option selection, not a new intent
                # Return UNCLEAR so it gets handled by main loop's option selection
                return WorkflowIntent.UNCLEAR
        
        # Direct command detection
        if any(word in input_lower for word in ['hook', 'opening', 'start of video']):
            return WorkflowIntent.START_HOOK
        elif any(word in input_lower for word in ['story', 'narrative', 'structure', 'body']):
            return WorkflowIntent.START_STORY
        elif any(word in input_lower for word in ['cta', 'call to action', 'ending']):
            return WorkflowIntent.START_CTA
        elif any(word in input_lower for word in ['review', 'check', 'see script']):
            return WorkflowIntent.REVIEW_SCRIPT
        elif any(word in input_lower for word in ['finalize', 'lock', 'confirm']):
            return WorkflowIntent.FINALIZE_COMPONENT
        
        # For more complex intents, use LLM
        intent_prompt = f"""Analyze the following user input and determine their intent.
        
Current project state:
- Topic: {state.topic}
- Hook finalized: {state.hook.finalized if state.hook else False}
- Story finalized: {state.story.finalized if state.story else False}
- CTA finalized: {state.cta.finalized if state.cta else False}
- Active module: {state.active_module}

User input: "{user_input}"

Possible intents:
- START_HOOK: User wants to work on the hook/opening
- START_STORY: User wants to work on the main story/body
- START_CTA: User wants to work on the call-to-action
- REVIEW_SCRIPT: User wants to review the complete script
- PROVIDE_CONTEXT: User is providing background information
- ADD_TONE_SAMPLE: User is providing writing samples for tone matching
- REQUEST_FEEDBACK: User wants feedback on existing content
- FINALIZE_COMPONENT: User wants to finalize/lock a component
- UNCLEAR: Intent is not clear

Return only the intent name, nothing else."""
        
        response = await self.invoke_llm(intent_prompt)
        
        # Parse the response to get intent
        intent_str = response.strip().upper()
        try:
            return WorkflowIntent[intent_str]
        except KeyError:
            return WorkflowIntent.UNCLEAR
    
    async def _handle_start_hook(self, state: VideoScriptState, 
                                user_input: Optional[str]) -> AgentResponse:
        """Handle request to work on the hook."""
        # Update state
        state.active_module = "hook"
        
        # Create or update hook component
        if not state.hook:
            state.hook = ScriptComponent(type="hook", content="", finalized=False)
        
        response_content = f"""Excellent! Let's create a compelling hook for your video about "{state.topic}".

A strong hook is crucial - it determines whether viewers stay or scroll. The first 3-8 seconds must:
1. Capture immediate attention
2. Clearly communicate the video's value
3. Create curiosity or emotional connection

I'll connect you with our Hook Specialist who will help craft multiple options."""
        
        suggestions = [
            "Consider starting with a surprising statistic or fact",
            "Use a visual hook - something unexpected on screen",
            "Try the 'problem-agitation' approach to create urgency",
            "Reference something familiar to reduce cognitive load"
        ]
        
        return AgentResponse(
            content=response_content,
            suggestions=suggestions,
            metadata={"next_agent": "hook_specialist", "intent": "start_hook"},
            requires_user_input=False
        )
    
    async def _handle_start_story(self, state: VideoScriptState, 
                                 user_input: Optional[str]) -> AgentResponse:
        """Handle request to work on the story structure."""
        state.active_module = "story"
        
        if not state.story:
            state.story = ScriptComponent(type="story", content="", finalized=False)
        
        hook_status = "completed" if state.hook and state.hook.finalized else "pending"
        
        response_content = f"""Let's structure the narrative for your video about "{state.topic}".

Hook status: {hook_status}

A well-structured story ensures viewers stay engaged throughout. We'll focus on:
1. Clear beginning, middle, and end
2. Logical flow of information
3. Maintaining viewer interest with re-hooking moments
4. Building toward your desired outcome

Our Story Architect will help you create a compelling narrative structure."""
        
        suggestions = [
            "Think about the transformation you want viewers to experience",
            "Consider using the problem-solution framework",
            "Plan for 'But & So' moments to maintain engagement",
            "Keep the core message focused and clear"
        ]
        
        return AgentResponse(
            content=response_content,
            suggestions=suggestions,
            metadata={"next_agent": "story_architect", "intent": "start_story"},
            requires_user_input=False
        )
    
    async def _handle_start_cta(self, state: VideoScriptState, 
                               user_input: Optional[str]) -> AgentResponse:
        """Handle request to work on the CTA."""
        state.active_module = "cta"
        
        if not state.cta:
            state.cta = ScriptComponent(type="cta", content="", finalized=False)
        
        response_content = f"""Smart move! Let's design a compelling call-to-action for your video about "{state.topic}".

Having the CTA in mind early helps ensure the entire script builds toward this moment. A strong CTA should:
1. Be crystal clear about the desired action
2. Create urgency or exclusivity
3. Make the next step easy and obvious
4. Align with the video's value proposition

Our CTA Strategist will help craft an action-driving conclusion."""
        
        suggestions = [
            "Define the ONE primary action you want viewers to take",
            "Consider platform-specific CTA placements",
            "Use strong action verbs (Get, Start, Join, Discover)",
            "Add urgency with time-limited offers or exclusive access"
        ]
        
        return AgentResponse(
            content=response_content,
            suggestions=suggestions,
            metadata={"next_agent": "cta_strategist", "intent": "start_cta"},
            requires_user_input=False
        )
    
    async def _handle_review_script(self, state: VideoScriptState) -> AgentResponse:
        """Handle request to review the complete script."""
        components_status = {
            "Hook": "✅" if state.hook and state.hook.finalized else "⏳" if state.hook else "❌",
            "Story": "✅" if state.story and state.story.finalized else "⏳" if state.story else "❌",
            "CTA": "✅" if state.cta and state.cta.finalized else "⏳" if state.cta else "❌"
        }
        
        script_parts = []
        if state.hook and state.hook.content:
            script_parts.append(f"**HOOK:**\n{state.hook.content}")
        if state.story and state.story.content:
            script_parts.append(f"**STORY:**\n{state.story.content}")
        if state.cta and state.cta.content:
            script_parts.append(f"**CTA:**\n{state.cta.content}")
        
        full_script = "\n\n".join(script_parts) if script_parts else "No content created yet."
        
        response_content = f"""## Script Review for "{state.topic}"

**Component Status:**
- Hook: {components_status['Hook']}
- Story: {components_status['Story']}
- CTA: {components_status['CTA']}

**Current Script:**
{full_script}

What would you like to work on next?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"intent": "review_script", "components_status": components_status},
            requires_user_input=True
        )
    
    async def _handle_provide_context(self, state: VideoScriptState, 
                                     user_input: Optional[str]) -> AgentResponse:
        """Handle when user provides context or background information."""
        # Add context to state
        if user_input:
            state.context_documents.append(user_input)
        
        response_content = """Thank you for providing that context! This background information will help all our specialists create more targeted and relevant content.

I've stored this information and will ensure it's considered throughout the script creation process.

What aspect of the script would you like to focus on now?"""
        
        return AgentResponse(
            content=response_content,
            metadata={"intent": "provide_context"},
            requires_user_input=True
        )
    
    async def _handle_add_tone_sample(self, state: VideoScriptState, 
                                     user_input: Optional[str]) -> AgentResponse:
        """Handle when user provides tone/voice samples."""
        if user_input:
            state.user_tone_samples.append(user_input)
        
        sample_count = len(state.user_tone_samples)
        
        response_content = f"""Perfect! I've captured your writing sample (sample {sample_count} of ideally 2-5).

{"Would you like to add another sample, or shall we proceed with script creation?" if sample_count < 5 else "We have enough samples to accurately match your voice. Let's proceed with script creation!"}

Your unique voice will be maintained throughout the script by our Stylist agent."""
        
        return AgentResponse(
            content=response_content,
            metadata={"intent": "add_tone_sample", "sample_count": sample_count},
            requires_user_input=True
        )
    
    async def _handle_request_feedback(self, state: VideoScriptState, 
                                      user_input: Optional[str]) -> AgentResponse:
        """Handle request for feedback on content."""
        # Determine which component needs feedback
        component_prompt = f"""The user is requesting feedback. Based on the current state and their input, determine which component they want feedback on.

User input: "{user_input}"
Active module: {state.active_module}

Provide constructive feedback following the 5:1 positive-to-constructive ratio."""
        
        feedback = await self.invoke_llm(component_prompt)
        
        return AgentResponse(
            content=feedback,
            metadata={"intent": "request_feedback", "next_agent": "challenger"},
            requires_user_input=True
        )
    
    async def _handle_finalize_component(self, state: VideoScriptState, 
                                        user_input: Optional[str]) -> AgentResponse:
        """Handle request to finalize a component."""
        # Determine which component to finalize
        if state.active_module == "hook" and state.hook:
            state.hook.finalized = True
            component_name = "hook"
        elif state.active_module == "story" and state.story:
            state.story.finalized = True
            component_name = "story"
        elif state.active_module == "cta" and state.cta:
            state.cta.finalized = True
            component_name = "call-to-action"
        else:
            component_name = None
        
        if component_name:
            response_content = f"""Excellent! I've finalized the {component_name}. This component is now locked in.

What would you like to work on next?"""
        else:
            response_content = """I couldn't determine which component to finalize. Please specify which part you'd like to lock in: hook, story, or CTA."""
        
        return AgentResponse(
            content=response_content,
            metadata={"intent": "finalize_component", "finalized": component_name},
            requires_user_input=True
        )
    
    async def _handle_unclear_intent(self, state: VideoScriptState, 
                                    user_input: Optional[str]) -> AgentResponse:
        """Handle unclear user intent."""
        # Check what's already completed to provide contextual message
        has_hook = state.hook and state.hook.content
        has_story = state.story and state.story.content  
        has_cta = state.cta and state.cta.content
        
        # If everything is complete, suggest review
        if has_hook and has_story and has_cta:
            response_content = f"""Welcome back! Your script for "{state.topic}" is complete.

📊 **Current Status:**
✅ Hook: Complete
✅ Story: Complete  
✅ CTA: Complete

🎯 **What would you like to do?**
• Type `review` → See your complete script and get feedback
• Type `status` → Check detailed progress
• Type `export` → Export your final script
• Type `humanize` → Make your script sound more natural
• Type `edit hook/story/cta` → Revise any component

💡 **Tip:** Since your script is complete, consider using `review` to get comprehensive feedback from our Challenger agent."""
        
        # If partially complete, suggest continuing
        elif has_hook or has_story or has_cta:
            completed = []
            todo = []
            
            if has_hook:
                completed.append("✅ Hook")
            else:
                todo.append("hook")
                
            if has_story:
                completed.append("✅ Story")
            else:
                todo.append("story")
                
            if has_cta:
                completed.append("✅ CTA")
            else:
                todo.append("cta")
            
            next_suggestion = todo[0] if todo else "review"
            
            response_content = f"""Welcome back! Let's continue your script for "{state.topic}".

📊 **Current Progress:**
{chr(10).join(completed)}
{chr(10).join(['⏳ ' + t.title() for t in todo])}

🎯 **Continue where you left off:**
• Type `{next_suggestion}` → {f"Create your {next_suggestion}" if next_suggestion != "review" else "Review your complete script"}
• Type `status` → See detailed progress
• Type `review` → See what you have so far

💡 **Next step:** Based on your progress, I recommend working on `{next_suggestion}` next."""
        
        # If nothing started, show welcome for new project
        else:
            response_content = f"""Welcome! Let's create an engaging video script for "{state.topic}".

Here are your options with the commands to use:

📝 **Generate Content:**
• Type `hook` → Create 3 attention-grabbing video openings
• Type `story` → Develop your narrative structure
• Type `cta` → Design compelling calls-to-action

📊 **Review & Manage:**
• Type `status` → Check what's been completed
• Type `review` → See your complete script
• Type `help` → Show all available commands

🎯 **Quick Start Suggestion:**
Start with `hook` to create your opening, then `story` for structure, and finally `cta` for your ending.

What would you like to do? Just type one of the commands above."""
        
        return AgentResponse(
            content=response_content,
            metadata={"intent": "unclear"},
            requires_user_input=True
        )
    
    async def provide_feedback(self, content: str, component_type: str) -> str:
        """
        Provide constructive feedback on content following the 5:1 ratio.
        
        Args:
            content: Content to review
            component_type: Type of component (hook/story/cta)
            
        Returns:
            Constructive feedback
        """
        feedback_prompt = f"""Review this {component_type} and provide feedback following these rules:
1. Start with 2-3 specific positive observations
2. Ask 1-2 probing questions to encourage deeper thinking
3. Offer 1 constructive suggestion for improvement
4. End with encouragement

Content to review:
{content}"""
        
        return await self.invoke_llm(feedback_prompt)
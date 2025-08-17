"""Story Architect agent for creating compelling video narratives."""

from typing import Optional, Dict, List
import json

from .base_agent import SpecializedAgent, AgentResponse
from ..models.config import VideoScriptState, ScriptComponent


class StoryArchitectAgent(SpecializedAgent):
    """
    Specializes in crafting compelling story structures and narrative arcs
    for video scripts using proven storytelling frameworks.
    """
    
    def _load_expertise_prompts(self) -> Dict[str, str]:
        """Load specialized prompts for story creation."""
        return {
            "generate_story": """Based on the video details:
Topic: {topic}
Target audience: {audience}
Platform: {platform}
Hook: {hook}
Context: {context}

Create a compelling story structure using the 3-Act Framework:

**Act 1: Setup (20% of script)**
- Bridge from hook to main content
- Establish the problem/opportunity
- Set stakes and expectations

**Act 2: Development (60% of script)**
- Present main points/solutions
- Build tension or intrigue
- Include examples, data, or demonstrations
- Create emotional connection

**Act 3: Resolution (20% of script)**
- Climax or key revelation
- Clear takeaway or transformation
- Smooth transition to CTA

Provide:
1. Story arc outline with timing
2. Key narrative beats
3. Emotional journey map
4. Specific examples or case studies to include
5. Transition phrases between sections""",
            
            "adapt_framework": """Current story: {story}
Adapt this narrative to the {framework} framework:

Available frameworks:
- Problem-Solution: Clear pain point → systematic solution
- Hero's Journey: Transformation through challenge
- Before-After-Bridge: Current state → desired state → path
- STAR: Situation → Task → Action → Result
- Nested Loops: Multiple open stories that resolve in reverse
- Converging Ideas: Multiple concepts leading to one insight

Restructure the content to fit the chosen framework while maintaining the core message.""",
            
            "enhance_narrative": """Story structure: {story}
Enhancement focus: {focus}

Enhance the narrative with:
1. Specific sensory details
2. Emotional touchpoints
3. Relatable analogies
4. Tension and release moments
5. Micro-stories or examples

Make it feel authentic and human, not AI-generated.""",
            
            "story_types": """Create a {video_type} story structure for:
Topic: {topic}

Video types:
- Explainer: Complex topic made simple
- How-to: Step-by-step transformation
- Brand story: Company/personal narrative
- Case study: Real-world application
- Thought leadership: Industry insights
- Entertainment: Engaging narrative
- Educational: Teaching concept

Provide structure optimized for {video_type} format."""
        }
    
    async def process(self, state: VideoScriptState, 
                     user_input: Optional[str] = None) -> AgentResponse:
        """
        Generate or improve story structure based on the current state.
        
        Args:
            state: Current video script state
            user_input: Optional user input
            
        Returns:
            Response with story structure
        """
        if not state.story:
            state.story = ScriptComponent(type="story", content="", finalized=False)
        
        # Check what action to take
        if not state.story.content or (user_input and "new" in user_input.lower()):
            return await self._generate_new_story(state, user_input)
        elif user_input and any(word in user_input.lower() for word in ["framework", "structure", "adapt"]):
            return await self._adapt_framework(state, user_input)
        else:
            return await self._enhance_story(state, user_input)
    
    async def _generate_new_story(self, state: VideoScriptState, 
                                 user_input: Optional[str]) -> AgentResponse:
        """Generate new story structure."""
        # Store duration in story metadata if it exists in state
        if hasattr(state, 'video_duration') and state.video_duration:
            state.story.metadata['video_duration'] = state.video_duration
        
        # Prepare context
        context = self._prepare_context(state)
        hook_content = state.hook.content if state.hook else "No hook yet"
        
        # Determine video type
        video_type = self._determine_video_type(state, user_input)
        
        # Generate story structure
        prompt = self.get_expertise_prompt(
            "generate_story",
            topic=state.topic,
            audience=state.target_audience or "general audience",
            platform=state.platform,
            hook=hook_content,
            context=context
        )
        
        story_response = await self.invoke_llm(prompt)
        
        # Parse and structure the story
        story_structure = self._parse_story_structure(story_response)
        
        # Store the story
        state.story.content = story_response
        state.story.iterations += 1
        state.story.metadata["structure"] = story_structure
        state.story.metadata["video_type"] = video_type
        
        response_content = f"""## Story Architecture for Your {video_type.title()} Video

I've crafted a narrative structure for "{state.topic}" that will keep your {state.target_audience} engaged from start to finish.

{story_response}

**Narrative Flow:**
"""
        
        for i, beat in enumerate(story_structure.get("beats", []), 1):
            response_content += f"{i}. {beat}\n"
        
        response_content += """
**Next Steps:**
- Review the story arc and pacing
- Add specific examples or case studies
- Consider alternative frameworks (Hero's Journey, Problem-Solution, etc.)
- Ensure smooth transitions between sections

Would you like me to:
1. Adjust the pacing or emphasis
2. Add more specific examples
3. Try a different storytelling framework
4. Enhance emotional elements"""
        
        suggestions = [
            "Consider your audience's attention span for optimal pacing",
            "Include 1-2 powerful examples or case studies",
            f"For {state.platform}, keep the energy high in Act 2",
            "End Act 2 with a mini-cliffhanger before resolution"
        ]
        
        return AgentResponse(
            content=response_content,
            suggestions=suggestions,
            metadata={"story_structure": story_structure, "action": "generated", "video_type": video_type},
            requires_user_input=True
        )
    
    async def _adapt_framework(self, state: VideoScriptState, 
                              user_input: str) -> AgentResponse:
        """Adapt story to a different framework."""
        # Identify requested framework
        framework = self._identify_framework(user_input)
        
        prompt = self.get_expertise_prompt(
            "adapt_framework",
            story=state.story.content,
            framework=framework
        )
        
        adapted_story = await self.invoke_llm(prompt)
        
        # Update story
        old_content = state.story.content
        state.story.content = adapted_story
        state.story.iterations += 1
        state.story.metadata["framework"] = framework
        state.story.feedback_history.append(f"Adapted to {framework} framework")
        
        response_content = f"""## Story Restructured: {framework} Framework

**Original Structure:**
{old_content[:300]}...

**New {framework} Structure:**
{adapted_story}

This framework is particularly effective for:
- {self._get_framework_benefits(framework)}

The new structure maintains your core message while creating a more compelling narrative arc.

Would you like to:
1. Keep this new structure
2. Try another framework
3. Blend elements from both versions
4. Add more specific details"""
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "adapted", "framework": framework},
            requires_user_input=True
        )
    
    async def _enhance_story(self, state: VideoScriptState, 
                            user_input: Optional[str]) -> AgentResponse:
        """Enhance existing story with details and emotion."""
        focus = user_input or "emotional connection and authenticity"
        
        prompt = self.get_expertise_prompt(
            "enhance_narrative",
            story=state.story.content,
            focus=focus
        )
        
        enhanced_story = await self.invoke_llm(prompt)
        
        # Update story
        state.story.content = enhanced_story
        state.story.iterations += 1
        if user_input:
            state.story.feedback_history.append(user_input)
        
        response_content = f"""## Enhanced Story Structure

{enhanced_story}

**Enhancements Added:**
- Sensory details for immersion
- Emotional anchor points
- Relatable examples
- Authentic voice and tone
- Natural transitions

The story now has stronger:
✨ Emotional resonance
📊 Concrete examples
🎭 Human authenticity
🔄 Narrative flow

Ready to move forward or would you like to:
1. Add more specific examples
2. Adjust the emotional tone
3. Strengthen any particular section
4. Finalize this structure"""
        
        return AgentResponse(
            content=response_content,
            metadata={"action": "enhanced", "focus": focus},
            requires_user_input=True
        )
    
    def _prepare_context(self, state: VideoScriptState) -> str:
        """Prepare context from state for story generation."""
        context_parts = []
        
        if state.context_documents:
            context_parts.append(f"Background: {' '.join(state.context_documents[:2])}")
        
        if state.user_tone_samples:
            context_parts.append(f"Tone reference: {state.user_tone_samples[0][:200]}")
        
        if state.cta and state.cta.content:
            context_parts.append(f"Building toward CTA: {state.cta.content}")
        
        return " | ".join(context_parts) if context_parts else "No additional context"
    
    def _determine_video_type(self, state: VideoScriptState, user_input: Optional[str]) -> str:
        """Determine the type of video based on context."""
        video_types = {
            "how": "how-to",
            "explain": "explainer",
            "tutorial": "how-to",
            "story": "brand story",
            "case": "case study",
            "review": "review",
            "teach": "educational",
            "entertain": "entertainment"
        }
        
        # Check user input
        if user_input:
            input_lower = user_input.lower()
            for key, value in video_types.items():
                if key in input_lower:
                    return value
        
        # Check topic
        topic_lower = state.topic.lower()
        for key, value in video_types.items():
            if key in topic_lower:
                return value
        
        # Default based on platform
        platform_defaults = {
            "youtube": "explainer",
            "tiktok": "entertainment",
            "instagram": "brand story",
            "linkedin": "thought leadership"
        }
        
        return platform_defaults.get(state.platform, "general")
    
    def _parse_story_structure(self, story_response: str) -> Dict:
        """Parse the story response into structured data."""
        structure = {
            "acts": [],
            "beats": [],
            "transitions": [],
            "examples": []
        }
        
        current_section = None
        
        for line in story_response.split('\n'):
            line = line.strip()
            
            # Identify acts
            if 'Act 1' in line or 'Setup' in line:
                current_section = "act1"
                structure["acts"].append({"name": "Setup", "content": []})
            elif 'Act 2' in line or 'Development' in line:
                current_section = "act2"
                structure["acts"].append({"name": "Development", "content": []})
            elif 'Act 3' in line or 'Resolution' in line:
                current_section = "act3"
                structure["acts"].append({"name": "Resolution", "content": []})
            
            # Extract beats (lines starting with numbers or bullets)
            elif line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                beat = line.lstrip('0123456789.-• ')
                structure["beats"].append(beat)
                
                if current_section and structure["acts"]:
                    structure["acts"][-1]["content"].append(beat)
            
            # Extract transitions
            if 'transition' in line.lower():
                structure["transitions"].append(line)
            
            # Extract examples
            if 'example' in line.lower() or 'case' in line.lower():
                structure["examples"].append(line)
        
        return structure
    
    def _identify_framework(self, user_input: str) -> str:
        """Identify which framework the user wants."""
        frameworks = {
            "problem": "Problem-Solution",
            "hero": "Hero's Journey",
            "before": "Before-After-Bridge",
            "star": "STAR",
            "nested": "Nested Loops",
            "converging": "Converging Ideas"
        }
        
        input_lower = user_input.lower()
        for key, value in frameworks.items():
            if key in input_lower:
                return value
        
        return "Problem-Solution"  # Default
    
    def _get_framework_benefits(self, framework: str) -> str:
        """Get benefits of specific framework."""
        benefits = {
            "Problem-Solution": "Clear value proposition and logical flow",
            "Hero's Journey": "Emotional engagement and transformation",
            "Before-After-Bridge": "Clear contrast and actionable path",
            "STAR": "Concrete results and credibility",
            "Nested Loops": "Sustained curiosity and engagement",
            "Converging Ideas": "Building to powerful insight"
        }
        
        return benefits.get(framework, "Enhanced narrative structure")
    
    async def generate_video_type_structure(self, state: VideoScriptState, 
                                           video_type: str) -> Dict:
        """
        Generate structure for specific video type.
        
        Args:
            state: Current state
            video_type: Type of video
            
        Returns:
            Video-type specific structure
        """
        prompt = self.get_expertise_prompt(
            "story_types",
            topic=state.topic,
            video_type=video_type
        )
        
        response = await self.invoke_llm(prompt)
        
        return {
            "type": video_type,
            "structure": response,
            "timing": self._get_video_type_timing(video_type)
        }
    
    def _get_video_type_timing(self, video_type: str) -> Dict[str, int]:
        """Get typical timing for video type."""
        timings = {
            "explainer": {"intro": 15, "body": 120, "conclusion": 25},
            "how-to": {"intro": 10, "steps": 150, "recap": 20},
            "brand story": {"setup": 20, "journey": 100, "vision": 40},
            "case study": {"problem": 30, "solution": 90, "results": 40},
            "thought leadership": {"hook": 20, "insights": 140, "cta": 20},
            "entertainment": {"hook": 5, "content": 110, "punchline": 15},
            "educational": {"intro": 20, "lesson": 130, "summary": 30}
        }
        
        return timings.get(video_type, {"intro": 20, "body": 120, "conclusion": 20})
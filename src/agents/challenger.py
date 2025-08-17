"""Challenger agent for constructive criticism and quality improvement."""

from typing import Optional, Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from ..models.config import VideoScriptState


class ChallengerAgent(BaseAgent):
    """Challenger agent specialized in constructive criticism and improvement suggestions."""
    
    def __init__(self, config, llm):
        """Initialize the Challenger agent."""
        super().__init__(config, llm)
        self.critique_framework = self._initialize_critique_framework()
        self.probing_questions = self._initialize_probing_questions()
        self.improvement_areas = self._initialize_improvement_areas()
    
    def _initialize_critique_framework(self) -> Dict[str, List[str]]:
        """Initialize the 5:1 positive-to-constructive criticism framework."""
        return {
            'positive_aspects': [
                'Strong hook that captures attention',
                'Clear value proposition', 
                'Good emotional connection',
                'Effective use of statistics',
                'Compelling storytelling',
                'Strong call-to-action',
                'Good pacing and flow',
                'Authentic voice',
                'Platform-appropriate content',
                'Audience-focused messaging'
            ],
            'constructive_areas': [
                'Hook could be more specific',
                'Value proposition needs clarity',
                'Emotional journey could be stronger',
                'Statistics need verification',
                'Story structure could improve',
                'CTA could be more compelling',
                'Pacing feels rushed or slow',
                'Voice consistency issues',
                'Platform optimization needed',
                'Audience connection unclear'
            ]
        }
    
    def _initialize_probing_questions(self) -> Dict[str, List[str]]:
        """Initialize probing questions for different aspects."""
        return {
            'hook': [
                "What makes this hook different from hundreds of similar videos?",
                "Would this stop someone mid-scroll? Why or why not?",
                "Is the promise clear within the first 3 seconds?",
                "Does it create genuine curiosity or just clickbait?",
                "Would your target audience relate to this instantly?"
            ],
            'story': [
                "Is the narrative arc compelling enough to maintain attention?",
                "Are there any logical gaps in your argument?",
                "Have you considered counterarguments?",
                "Does each point build on the previous one?",
                "Is the emotional journey intentional and effective?"
            ],
            'cta': [
                "Is the ask proportional to the value provided?",
                "What specific action do you want viewers to take?",
                "Have you created enough urgency without being pushy?",
                "Does the CTA flow naturally from your content?",
                "What objections might prevent action?"
            ],
            'overall': [
                "Who specifically is your ideal viewer?",
                "What transformation are you promising?",
                "Why should viewers trust you on this topic?",
                "What makes your perspective unique?",
                "How will viewers feel after watching?"
            ]
        }
    
    def _initialize_improvement_areas(self) -> List[str]:
        """Initialize key areas for improvement analysis."""
        return [
            'clarity', 'engagement', 'credibility', 'uniqueness',
            'emotional_impact', 'value_delivery', 'structure',
            'pacing', 'authenticity', 'actionability'
        ]
    
    async def process(self, state: VideoScriptState, user_input: Optional[str] = None) -> AgentResponse:
        """Process critique and improvement requests."""
        
        if user_input:
            if 'critique' in user_input.lower() or 'review' in user_input.lower():
                return await self._provide_critique(state, user_input)
            elif 'alternative' in user_input.lower():
                return await self._suggest_alternatives(state, user_input)
            elif 'devil' in user_input.lower() or 'advocate' in user_input.lower():
                return await self._play_devils_advocate(state, user_input)
            elif 'improve' in user_input.lower():
                return await self._suggest_improvements(state, user_input)
            else:
                return await self._comprehensive_review(state)
        else:
            return await self._comprehensive_review(state)
    
    async def _provide_critique(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Provide constructive critique following 5:1 ratio."""
        
        content = self._get_content_to_critique(state, user_input)
        
        if not content:
            return self._no_content_response()
        
        critique_prompt = f"""As a constructive critic, review this video script content:

{content}

Topic: {state.topic}
Platform: {state.platform}
Audience: {state.target_audience}

Provide critique following the 5:1 rule (5 positives for every 1 constructive criticism):

1. Five Strengths (be specific and genuine)
2. One Key Area for Improvement (be constructive and specific)
3. Actionable Suggestion for Improvement
4. Overall Assessment

Be honest but encouraging. Focus on helping, not just criticizing."""

        critique = await self.invoke_llm(critique_prompt)
        
        # Generate probing questions
        questions = self._generate_probing_questions(content, state)
        
        response_content = f"""## 🎯 Constructive Critique

{critique}

### 🤔 Questions to Consider:
{questions}

### 💡 Quick Wins:
• Strengthen your opening line
• Add more specific examples
• Clarify your main value prop
• Tighten transitions between points
• End with a clear next step

### 📈 Impact Potential:
Making these improvements could increase:
• Completion rate by 15-20%
• Engagement by 25-30%
• Conversion by 10-15%

**Remember:** Great content comes from iteration. Every critique is a step toward excellence!

**Next Actions:**
• Type `alternatives` for different approaches
• Type `improve: [specific area]` for targeted help
• Type `devil's advocate` for challenging perspectives"""

        return AgentResponse(
            content=response_content,
            metadata={
                "critique_provided": True,
                "content_reviewed": len(content)
            },
            requires_user_input=True
        )
    
    async def _suggest_alternatives(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Suggest alternative approaches."""
        
        content = self._get_content_to_critique(state, user_input)
        
        alternatives_prompt = f"""Suggest 3 completely different approaches for this content:

Current Approach: {content[:500]}...

Topic: {state.topic}
Platform: {state.platform}
Audience: {state.target_audience}

For each alternative:
1. Different angle/perspective
2. Why it might work better
3. Potential risks
4. Quick example

Be creative but practical."""

        alternatives = await self.invoke_llm(alternatives_prompt)
        
        response_content = f"""## 🔄 Alternative Approaches

{alternatives}

### 🎨 Mix & Match Strategy:
• Take the best element from each approach
• Combine different angles for uniqueness
• Test different versions with your audience
• Keep what resonates, discard what doesn't

### 🚀 Innovation Framework:
1. **Reverse:** What if you argued the opposite?
2. **Extreme:** What if you took it to the limit?
3. **Combine:** What if you merged two ideas?
4. **Simplify:** What if you cut 50%?
5. **Personalize:** What if you made it about them?

### 💭 Decision Criteria:
• Which excites you most to create?
• Which serves your audience best?
• Which fits the platform norms?
• Which is most authentic to you?

**Pro Tip:** Sometimes the "safe" approach isn't the best. Calculated risks can lead to breakthrough content!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "alternatives_provided": True
            },
            requires_user_input=True
        )
    
    async def _play_devils_advocate(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Challenge assumptions and play devil's advocate."""
        
        content = self._get_content_to_critique(state, user_input)
        
        if not content:
            return self._no_content_response()
        
        challenge_prompt = f"""Play devil's advocate for this video script:

{content}

Challenge:
1. Core assumptions
2. Logic and arguments
3. Evidence and claims
4. Audience assumptions
5. Effectiveness claims

Be rigorous but fair. Point out:
- Weak arguments
- Unsupported claims
- Logical fallacies
- Missing perspectives
- Potential objections

Also suggest how to address each challenge."""

        challenges = await self.invoke_llm(challenge_prompt)
        
        response_content = f"""## 😈 Devil's Advocate Challenge

{challenges}

### 🛡️ Strengthening Your Position:

**Address Objections Preemptively:**
• "You might be thinking..."
• "I know what you're wondering..."
• "The skeptics will say..."

**Build Credibility:**
• Acknowledge limitations
• Cite credible sources
• Share balanced views
• Include counter-evidence

**Use Strategic Concessions:**
• "While it's true that..."
• "Critics have a point when..."
• "This isn't perfect, but..."

### 🎯 Common Viewer Objections:
1. "This won't work for me because..."
2. "I've tried this before and..."
3. "This is too good to be true..."
4. "You don't understand my situation..."
5. "This is just another..."

### 💪 Making It Bulletproof:
• Anticipate top 3 objections
• Address them directly
• Provide evidence/examples
• Show understanding
• Offer alternatives

**Remember:** The best content acknowledges complexity while maintaining clarity!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "devils_advocate": True
            },
            requires_user_input=True
        )
    
    async def _suggest_improvements(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Suggest specific improvements."""
        
        # Extract specific area if mentioned
        area = user_input.replace('improve:', '').replace('improve', '').strip()
        
        content = self._get_content_to_critique(state, user_input)
        
        if not content:
            return self._no_content_response()
        
        improvement_prompt = f"""Suggest specific improvements for this content:

{content}

Focus Area: {area if area else 'Overall enhancement'}
Platform: {state.platform}
Audience: {state.target_audience}

Provide:
1. Current State Analysis
2. Specific Improvements (with examples)
3. Implementation Steps
4. Expected Impact
5. Before/After Comparison

Be detailed and actionable."""

        improvements = await self.invoke_llm(improvement_prompt)
        
        response_content = f"""## 📈 Improvement Roadmap

{improvements}

### 🎯 Priority Matrix:

**Quick Wins** (High Impact, Low Effort):
• Stronger opening hook
• Clearer value proposition
• Better transitions
• Specific examples

**Strategic Improvements** (High Impact, High Effort):
• Complete restructuring
• Deep research addition
• Style overhaul
• Platform optimization

### 🔧 Implementation Checklist:
- [ ] Make hook more specific
- [ ] Add emotional triggers
- [ ] Include social proof
- [ ] Clarify the transformation
- [ ] Strengthen CTA
- [ ] Add urgency elements
- [ ] Improve flow/pacing
- [ ] Enhance authenticity

### 📊 Success Metrics:
• Hook: 3-second stop rate
• Story: 50%+ completion
• CTA: 5%+ conversion

**Action Step:** Pick one improvement and implement it now. Perfect is the enemy of done!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "improvements_suggested": True,
                "focus_area": area if area else "overall"
            },
            requires_user_input=True
        )
    
    async def _comprehensive_review(self, state: VideoScriptState) -> AgentResponse:
        """Provide comprehensive review of the entire script."""
        
        has_content = any([
            state.hook and state.hook.content,
            state.story and state.story.content,
            state.cta and state.cta.content
        ])
        
        if not has_content:
            return AgentResponse(
                content="""## 🎬 Challenger Ready

I'm here to make your content stronger through constructive criticism!

**My Approach:**
• 5:1 positive-to-constructive ratio
• Specific, actionable feedback
• Alternative perspectives
• Challenge assumptions
• Combat AI sycophancy

**Available Services:**
• `critique` - Constructive review
• `alternatives` - Different approaches
• `devil's advocate` - Challenge assumptions
• `improve: [area]` - Specific improvements
• `review` - Comprehensive analysis

**My Promise:**
I'll be honest but encouraging. My goal is to help you create content that truly resonates.

What would you like me to review or challenge?""",
                metadata={"service": "ready"},
                requires_user_input=True
            )
        
        # Compile full script
        script_parts = []
        if state.hook and state.hook.content:
            script_parts.append(f"HOOK:\n{state.hook.content}")
        if state.story and state.story.content:
            script_parts.append(f"STORY:\n{state.story.content}")
        if state.cta and state.cta.content:
            script_parts.append(f"CTA:\n{state.cta.content}")
        
        full_script = "\n\n".join(script_parts)
        
        review_prompt = f"""Provide a comprehensive review of this video script:

{full_script}

Topic: {state.topic}
Platform: {state.platform}
Audience: {state.target_audience}

Review Structure:
1. Overall Effectiveness (1-10 score)
2. Five Strengths (specific examples)
3. One Critical Improvement Area
4. Platform Optimization Assessment
5. Audience Resonance Prediction
6. Competitive Differentiation
7. Specific Next Steps

Be thorough, honest, and constructive."""

        review = await self.invoke_llm(review_prompt)
        
        # Calculate completion
        completion = sum([
            33 if state.hook and state.hook.finalized else 0,
            34 if state.story and state.story.finalized else 0,
            33 if state.cta and state.cta.finalized else 0
        ])
        
        response_content = f"""## 📊 Comprehensive Script Review

**Completion:** {completion}%
**Components:** {'✅ Hook' if state.hook and state.hook.content else '❌ Hook'} | {'✅ Story' if state.story and state.story.content else '❌ Story'} | {'✅ CTA' if state.cta and state.cta.content else '❌ CTA'}

{review}

### 🎯 Action Priority:
1. **Immediate:** Fix the critical improvement area
2. **Next:** Enhance platform optimization
3. **Then:** Polish for audience resonance
4. **Finally:** Add differentiation elements

### 💡 Pro Tips:
• Test with 3-5 target viewers
• Get feedback on specific elements
• Iterate based on data, not opinions
• Keep what works, change what doesn't

### 🚀 Next Level Tactics:
• A/B test different hooks
• Add pattern interrupts
• Include micro-commitments
• Create curiosity loops
• End with cliffhangers

**Your script has potential. With these improvements, it could be exceptional!**

## 📝 What would you like to do next?

**Improve your script:**
• Type **humanize** - Make the script sound more natural and conversational
• Type **edit hook** - Update your hook based on feedback
• Type **edit story** - Revise your story structure  
• Type **edit cta** - Improve your call-to-action

**Polish and refine:**
• Type **style** - Adjust tone and voice
• Type **research** - Add data and facts
• Type **improve: [specific area]** - Get targeted suggestions

**Finalize:**
• Type **export** - Save your final script
• Type **status** - See current progress"""

        return AgentResponse(
            content=response_content,
            metadata={
                "comprehensive_review": True,
                "completion_percentage": completion,
                "review_complete": True
            },
            requires_user_input=True
        )
    
    def _get_content_to_critique(self, state: VideoScriptState, user_input: str) -> str:
        """Get content to critique from state or user input."""
        # Check if user specified what to critique
        if 'hook' in user_input.lower() and state.hook:
            return state.hook.content
        elif 'story' in user_input.lower() and state.story:
            return state.story.content
        elif 'cta' in user_input.lower() and state.cta:
            return state.cta.content
        
        # Get all available content
        parts = []
        if state.hook and state.hook.content:
            parts.append(f"HOOK: {state.hook.content}")
        if state.story and state.story.content:
            parts.append(f"STORY: {state.story.content}")
        if state.cta and state.cta.content:
            parts.append(f"CTA: {state.cta.content}")
        
        return "\n\n".join(parts)
    
    def _generate_probing_questions(self, content: str, state: VideoScriptState) -> str:
        """Generate relevant probing questions."""
        questions = []
        
        # Determine which component we're reviewing
        if 'hook' in content.lower()[:50]:
            questions = self.probing_questions['hook'][:3]
        elif 'story' in content.lower()[:50]:
            questions = self.probing_questions['story'][:3]
        elif 'cta' in content.lower()[:50]:
            questions = self.probing_questions['cta'][:3]
        else:
            questions = self.probing_questions['overall'][:3]
        
        return "\n".join([f"• {q}" for q in questions])
    
    def _no_content_response(self) -> AgentResponse:
        """Response when there's no content to critique."""
        return AgentResponse(
            content="""## 🎬 No Content to Review Yet

Create some content first, then I'll help you make it exceptional!

**Quick Start:**
1. Type `hook` to create opening
2. Type `story` to develop narrative  
3. Type `cta` to add call-to-action

Then I can provide:
• Constructive critique
• Alternative approaches
• Devil's advocate perspective
• Specific improvements

I'm ready to help you level up your content!""",
            metadata={"error": "no_content"},
            requires_user_input=True
        )
"""Research Analyst agent for fact-checking and credibility verification."""

from typing import Optional, Dict, Any, List
import re
import json
from datetime import datetime
from .base_agent import BaseAgent, AgentResponse
from ..models.config import VideoScriptState


class ResearchAnalystAgent(BaseAgent):
    """Research Analyst agent specialized in fact-checking and source verification."""
    
    def __init__(self, config, llm):
        """Initialize the Research Analyst agent."""
        super().__init__(config, llm)
        self.fact_patterns = self._initialize_fact_patterns()
        self.credibility_indicators = self._initialize_credibility_indicators()
    
    def _initialize_fact_patterns(self) -> Dict[str, str]:
        """Initialize patterns for fact detection."""
        return {
            'statistic': r'\d+(?:\.\d+)?%|\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|thousand))?',
            'comparison': r'(?:more|less|better|worse|higher|lower|faster|slower)\s+than',
            'claim': r'(?:studies show|research indicates|experts say|according to|data reveals)',
            'absolute': r'(?:always|never|every|all|none|only|guaranteed)',
            'trending': r'(?:viral|trending|breaking|exclusive|revolutionary)',
        }
    
    def _initialize_credibility_indicators(self) -> Dict[str, List[str]]:
        """Initialize credibility indicators."""
        return {
            'high_credibility': [
                'peer-reviewed', 'published study', 'research paper', 'official data',
                'government report', 'academic journal', 'systematic review'
            ],
            'medium_credibility': [
                'industry report', 'survey', 'case study', 'white paper',
                'expert opinion', 'market research', 'statistical analysis'
            ],
            'low_credibility': [
                'social media', 'blog post', 'opinion piece', 'anecdotal',
                'rumor', 'speculation', 'unverified claim'
            ],
            'red_flags': [
                'no source', 'anonymous', 'allegedly', 'reportedly', 
                'some say', 'people are saying', 'everyone knows'
            ]
        }
    
    async def process(self, state: VideoScriptState, user_input: Optional[str] = None) -> AgentResponse:
        """Process research and fact-checking requests."""
        
        # Determine what needs to be researched or verified
        if user_input and 'verify' in user_input.lower():
            return await self._verify_claims(state, user_input)
        elif user_input and 'research' in user_input.lower():
            return await self._conduct_research(state, user_input)
        elif user_input and 'source' in user_input.lower():
            return await self._find_sources(state, user_input)
        else:
            return await self._analyze_script_credibility(state)
    
    async def _verify_claims(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Verify specific claims in the script."""
        
        # Extract the claim to verify
        claim = user_input.replace('verify', '').strip()
        if not claim:
            # Analyze all claims in the current script
            claims = self._extract_claims_from_script(state)
            verification_prompt = self._create_verification_prompt(claims, state)
        else:
            verification_prompt = f"""As a research analyst, verify the following claim for a video about {state.topic}:

Claim: {claim}

Provide:
1. Verification status (Verified/Unverified/Partially Verified)
2. Supporting evidence or lack thereof
3. Credibility assessment
4. Suggested improvements for accuracy
5. Alternative phrasing if needed

Be thorough but concise."""

        verification = await self.invoke_llm(verification_prompt)
        
        response_content = f"""## 🔍 Fact Verification Report

{verification}

### 💡 Research Tips:
• Always cite credible sources when making claims
• Use specific numbers rather than vague terms
• Qualify statements appropriately (e.g., "studies suggest" vs "proven")
• Consider your audience's fact-checking tendencies

**Next steps:**
• Type `research: [topic]` to find supporting data
• Type `source: [claim]` to find credible sources
• Type `verify: [another claim]` to check more facts"""

        return AgentResponse(
            content=response_content,
            metadata={
                "verification_complete": True,
                "claim_analyzed": claim if claim else "all_claims"
            },
            requires_user_input=True
        )
    
    async def _conduct_research(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Conduct research on a specific topic."""
        
        # Extract research topic
        topic = user_input.replace('research', '').replace(':', '').strip()
        if not topic:
            topic = state.topic
        
        research_prompt = f"""As a research analyst, provide comprehensive research on the following topic:

Topic: {topic}
Context: Video script about {state.topic}
Audience: {state.target_audience}
Platform: {state.platform}

Provide:
1. Key Statistics (with implied sources)
2. Current Trends
3. Common Misconceptions
4. Compelling Data Points
5. Expert Consensus
6. Controversial Aspects (if any)

Format the research to be immediately usable in a video script.
Focus on credible, recent information."""

        research = await self.invoke_llm(research_prompt)
        
        # Analyze credibility of research
        credibility_score = self._calculate_credibility_score(research)
        
        response_content = f"""## 📊 Research Report: {topic}

{research}

### 📈 Credibility Assessment
**Score: {credibility_score}/10**
{self._get_credibility_feedback(credibility_score)}

### 📝 How to Use This Research:
• Pick 2-3 most compelling statistics for your hook
• Use trend data to establish relevance
• Address misconceptions to build trust
• Save expert consensus for authority

**Quick Integration:**
• Copy relevant stats directly into your script
• Paraphrase findings in your voice
• Use data to support your key messages"""

        return AgentResponse(
            content=response_content,
            metadata={
                "research_topic": topic,
                "credibility_score": credibility_score,
                "research_complete": True
            },
            requires_user_input=True
        )
    
    async def _find_sources(self, state: VideoScriptState, user_input: str) -> AgentResponse:
        """Find credible sources for claims."""
        
        claim = user_input.replace('source', '').replace(':', '').strip()
        
        source_prompt = f"""As a research analyst, suggest credible sources for the following claim:

Claim: {claim if claim else f"General sources for {state.topic}"}
Context: Video about {state.topic}

Provide:
1. Primary Sources (most credible)
   - Academic papers
   - Government data
   - Original research
   
2. Secondary Sources (credible)
   - Industry reports
   - Expert interviews
   - Reputable news outlets
   
3. Supporting Sources
   - Case studies
   - Statistics databases
   - Professional organizations

For each source type, provide:
- Where to find it
- Why it's credible
- How to cite it properly"""

        sources = await self.invoke_llm(source_prompt)
        
        response_content = f"""## 📚 Source Recommendations

{sources}

### 🎯 Source Selection Tips:
• Prioritize recent sources (last 2-3 years)
• Cross-reference multiple sources
• Look for peer-reviewed content
• Check author credentials
• Verify publication reputation

### ⚠️ Avoid These Sources:
• Unverified social media claims
• Outdated statistics (>5 years old)
• Biased or sponsored content
• Anonymous sources
• Clickbait articles

**Remember:** Your credibility depends on your sources!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "sources_found": True,
                "claim": claim if claim else "general"
            },
            requires_user_input=True
        )
    
    async def _analyze_script_credibility(self, state: VideoScriptState) -> AgentResponse:
        """Analyze overall script credibility."""
        
        # Gather all script components
        script_parts = []
        if state.hook and state.hook.content:
            script_parts.append(f"Hook: {state.hook.content}")
        if state.story and state.story.content:
            script_parts.append(f"Story: {state.story.content}")
        if state.cta and state.cta.content:
            script_parts.append(f"CTA: {state.cta.content}")
        
        if not script_parts:
            return AgentResponse(
                content="""## 🔍 Research Analyst Ready

I'm here to help ensure your script is accurate and credible!

**Available Services:**
• `research: [topic]` - Deep dive into any subject
• `verify: [claim]` - Fact-check specific statements
• `source: [claim]` - Find credible sources
• `analyze` - Review script credibility

**Pro Tips:**
• Credible scripts build trust
• Specific data beats vague claims
• Recent sources matter most
• Always verify surprising statistics

What would you like me to research or verify?""",
                metadata={"service": "ready"},
                requires_user_input=True
            )
        
        full_script = "\n\n".join(script_parts)
        
        analysis_prompt = f"""As a research analyst, analyze the credibility of this video script:

{full_script}

Provide:
1. Overall Credibility Score (1-10)
2. Claims Requiring Verification
3. Unsupported Statements
4. Credibility Strengths
5. Areas for Improvement
6. Specific Recommendations

Be constructive and specific."""

        analysis = await self.invoke_llm(analysis_prompt)
        
        response_content = f"""## 🔬 Script Credibility Analysis

{analysis}

### 🎯 Quick Improvements:
• Add specific statistics where possible
• Cite sources for major claims
• Qualify absolute statements
• Update any outdated information
• Cross-check surprising facts

**Next Actions:**
• Type `verify: [specific claim]` to fact-check
• Type `research: [topic]` for supporting data
• Type `source: [claim]` for citations

Building credibility builds trust with your audience!"""

        return AgentResponse(
            content=response_content,
            metadata={
                "analysis_complete": True,
                "script_analyzed": True
            },
            requires_user_input=True
        )
    
    def _extract_claims_from_script(self, state: VideoScriptState) -> List[str]:
        """Extract claims that need verification from the script."""
        claims = []
        
        # Combine all script content
        content = ""
        if state.hook and state.hook.content:
            content += state.hook.content + " "
        if state.story and state.story.content:
            content += state.story.content + " "
        if state.cta and state.cta.content:
            content += state.cta.content
        
        # Find statistical claims
        for match in re.finditer(self.fact_patterns['statistic'], content):
            context_start = max(0, match.start() - 50)
            context_end = min(len(content), match.end() + 50)
            claims.append(content[context_start:context_end].strip())
        
        # Find comparison claims
        for match in re.finditer(self.fact_patterns['comparison'], content):
            context_start = max(0, match.start() - 30)
            context_end = min(len(content), match.end() + 30)
            claims.append(content[context_start:context_end].strip())
        
        return claims[:5]  # Limit to top 5 claims
    
    def _create_verification_prompt(self, claims: List[str], state: VideoScriptState) -> str:
        """Create a prompt for verifying multiple claims."""
        if not claims:
            return f"No specific claims found in the script about {state.topic}. Provide general fact-checking guidance."
        
        claims_text = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])
        
        return f"""As a research analyst, verify these claims from a video script about {state.topic}:

{claims_text}

For each claim:
1. Verification status
2. Credibility assessment
3. Suggested improvement

Be thorough but concise."""
    
    def _calculate_credibility_score(self, text: str) -> int:
        """Calculate credibility score based on content analysis."""
        score = 5  # Start with neutral score
        
        text_lower = text.lower()
        
        # Check for high credibility indicators
        for indicator in self.credibility_indicators['high_credibility']:
            if indicator in text_lower:
                score += 0.5
        
        # Check for medium credibility indicators
        for indicator in self.credibility_indicators['medium_credibility']:
            if indicator in text_lower:
                score += 0.3
        
        # Check for red flags
        for flag in self.credibility_indicators['red_flags']:
            if flag in text_lower:
                score -= 0.5
        
        # Check for specific data
        if re.search(self.fact_patterns['statistic'], text):
            score += 0.5
        
        # Check for absolute claims (usually less credible)
        if re.search(self.fact_patterns['absolute'], text):
            score -= 0.3
        
        return max(1, min(10, round(score)))
    
    def _get_credibility_feedback(self, score: int) -> str:
        """Get feedback based on credibility score."""
        if score >= 8:
            return "✅ Excellent credibility! Well-researched with strong sources."
        elif score >= 6:
            return "👍 Good credibility. Consider adding more specific sources."
        elif score >= 4:
            return "⚠️ Moderate credibility. Needs more verification and sources."
        else:
            return "❌ Low credibility. Requires significant fact-checking and sourcing."
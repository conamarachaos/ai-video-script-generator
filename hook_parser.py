"""
Advanced hook parser for extracting actual script content from agent responses
"""
import re
from typing import List, Dict, Any

def parse_hooks_advanced(content: str) -> List[str]:
    """
    Advanced parser that extracts actual hook scripts from complex agent responses
    including those with visual descriptions and metadata
    """
    # First try to extract with full metadata
    metadata = extract_hook_metadata(content)
    hooks = [item['script'] for item in metadata if 'script' in item and item['script']]
    
    if hooks:
        return hooks[:3]
    
    # Method 2: Extract from structured options with empty scripts
    # Pattern: "Option N: Type\n📝 Script: [empty or missing]\n"
    # In this case, generate from the type
    option_pattern = r'Option\s+(\d+):\s*([^\n]+)'
    option_matches = re.findall(option_pattern, content)
    
    for num, option_type in option_matches:
        # Check if this option has an empty script section
        script_section = re.search(
            rf'Option\s+{num}:.*?📝\s*Script:\s*\n\s*(?:🎬|⏱️|Option|$)',
            content,
            re.DOTALL
        )
        
        if script_section:
            # Script is empty, generate based on type
            hook_type = option_type.strip()
            if 'Problem' in hook_type or 'Agitation' in hook_type:
                hooks.append("Are you tired of struggling with manual tasks that eat up your valuable time?")
            elif 'Curiosity' in hook_type:
                hooks.append("What if I told you there's a way to automate 80% of your repetitive work?")
            elif 'Statistical' in hook_type or 'Shock' in hook_type:
                hooks.append("90% of businesses fail because they can't scale efficiently. Here's how to be in the 10%.")
            elif 'Question' in hook_type:
                hooks.append("Have you ever wondered how successful companies handle their growth?")
            elif 'Story' in hook_type:
                hooks.append("Last year, I was drowning in busywork. Then I discovered this game-changing approach.")
    
    if hooks:
        return hooks[:3]
    
    # Method 3: Look for quoted text that seems like hooks
    quoted_pattern = r'[""]([^""]{30,300})[""]'
    quoted_matches = re.findall(quoted_pattern, content)
    
    for match in quoted_matches:
        cleaned = match.strip()
        if not any(word in cleaned.lower() for word in ['visual:', 'duration:', 'type']):
            hooks.append(cleaned)
    
    if hooks:
        return hooks[:3]
    
    # Method 4: Extract numbered items that look like actual hooks
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip meta information
        if any(marker in line for marker in ['Visual:', '🎬', '⏱️', 'Duration:', 'Type:']):
            continue
            
        # Look for numbered items
        if re.match(r'^\d+[\.\):]', line):
            cleaned = re.sub(r'^\d+[\.\):]\s*', '', line).strip()
            if cleaned and len(cleaned) > 20 and not cleaned.endswith(':'):
                hooks.append(cleaned)
    
    return hooks[:3]

def extract_hook_metadata(content: str) -> List[Dict[str, Any]]:
    """
    Extract complete hook information including visuals and duration
    """
    hooks_data = []
    
    # Split by Option markers
    options = re.split(r'(?=Option\s+\d+:)', content)
    
    for option in options:
        if not option.strip() or not option.startswith('Option'):
            continue
            
        hook_info = {}
        
        # Extract option number and type
        header_match = re.match(r'Option\s+(\d+):\s*([^\n]+)', option)
        if header_match:
            hook_info['number'] = int(header_match.group(1))
            hook_info['type'] = header_match.group(2).strip()
        
        # Extract script
        script_match = re.search(r'📝\s*Script:\s*([^\n]*?)(?:\n(?:🎬|⏱️)|$)', option)
        if script_match:
            script_content = script_match.group(1).strip().strip('"')
            # Check if script is empty or just whitespace
            if script_content and not script_content.startswith('🎬'):
                hook_info['script'] = script_content
            elif 'type' in hook_info:
                # Generate fallback based on type
                hook_info['script'] = generate_fallback_hook(hook_info['type'])
        elif 'type' in hook_info:
            # Generate fallback based on type
            hook_info['script'] = generate_fallback_hook(hook_info['type'])
        
        # Extract visual description
        visual_match = re.search(r'🎬\s*Visual:\s*([^\n]+(?:\n(?!⏱️|📝|Option)[^\n]+)*)', option)
        if visual_match:
            hook_info['visual'] = visual_match.group(1).strip()
        
        # Extract duration
        duration_match = re.search(r'⏱️\s*Duration:\s*([^\n]+)', option)
        if duration_match:
            hook_info['duration'] = duration_match.group(1).strip()
        
        if 'script' in hook_info and hook_info['script']:
            hooks_data.append(hook_info)
    
    return hooks_data

def generate_fallback_hook(hook_type: str) -> str:
    """
    Generate a fallback hook based on the type when script is empty
    """
    hook_type_lower = hook_type.lower()
    
    if 'problem' in hook_type_lower or 'agitation' in hook_type_lower:
        return "Stop wasting hours on repetitive tasks that drain your energy and kill your productivity."
    elif 'curiosity' in hook_type_lower:
        return "There's a secret that top performers use to get 10x more done in half the time..."
    elif 'statistical' in hook_type_lower or 'shock' in hook_type_lower:
        return "Studies show that 87% of people are doing this completely wrong. Are you one of them?"
    elif 'question' in hook_type_lower:
        return "What if you could transform your workflow in just 5 minutes a day?"
    elif 'story' in hook_type_lower:
        return "Six months ago, I was overwhelmed. Today, I run my business on autopilot. Here's how..."
    elif 'benefit' in hook_type_lower:
        return "Discover the simple technique that's helping thousands achieve their goals faster."
    else:
        return "This one simple change transformed everything for me. Let me show you how."

if __name__ == "__main__":
    # Test with the problematic response
    test_content = """
Option 1: Problem/Agitation
📝 Script:
🎬 Visual: Quick montage of frustrated founder looking at a laptop, overflowing spreadsheets on screen, followed by a shot of a rocket launching.
⏱️ Duration: 5 seconds

Option 2: Curiosity Gap
📝 Script:
🎬 Visual: Close-up of a smartphone, then transitions to a graph showing exponential growth.
⏱️ Duration: 6 seconds

Option 3: Statistical Shock
📝 Script:
🎬 Visual: Split screen showing manual work vs automated processes.
⏱️ Duration: 7 seconds
"""
    
    hooks = parse_hooks_advanced(test_content)
    print("Extracted hooks:")
    for i, hook in enumerate(hooks, 1):
        print(f"{i}. {hook}")
    
    print("\nDetailed metadata:")
    metadata = extract_hook_metadata(test_content)
    for data in metadata:
        print(f"\nOption {data.get('number', '?')}:")
        print(f"  Type: {data.get('type', 'Unknown')}")
        print(f"  Script: {data.get('script', 'N/A')}")
        if 'visual' in data:
            print(f"  Visual: {data['visual']}")
        if 'duration' in data:
            print(f"  Duration: {data['duration']}")
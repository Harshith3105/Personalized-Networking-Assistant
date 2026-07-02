import logging
import re
from typing import List
from transformers import pipeline

logger = logging.getLogger(__name__)

# Global cache for the generator pipeline
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        logger.info("Loading GPT-2 generation model...")
        # Use gpt2 (small) model
        _generator = pipeline(
            "text-generation",
            model="gpt2"
        )
        logger.info("GPT-2 model loaded successfully.")
    return _generator

def generate_starters(event_description: str, themes: List[str], interests: List[str]) -> List[str]:
    """
    Generates 2-3 conversation starters using GPT-2 based on themes and interests.
    """
    themes_str = ", ".join(themes) if themes else "Networking"
    interests_str = ", ".join(interests) if interests else "Professional Growth"

    # Few-shot prompt to guide GPT-2 completion
    prompt = (
        "Event: Artificial Intelligence and Sustainable Development\n"
        "Themes: AI, Sustainability\n"
        "Interests: climate change, urban planning\n"
        "Conversation Starters:\n"
        "1. \"Given your interest in urban planning, how do you see AI optimizing transit systems to combat climate change?\"\n"
        "2. \"I'm curious: are there any specific AI tools you've seen successfully applied to sustainable energy challenges?\"\n"
        "3. \"It seems AI and climate change are closely linked now. What's your take on the carbon footprint of training large AI models?\"\n"
        "\n"
        "Event: Fintech Revolution 2026\n"
        "Themes: Fintech, Blockchain\n"
        "Interests: cryptocurrency, decentralized finance\n"
        "Conversation Starters:\n"
        "1. \"With decentralized finance growing rapidly, do you think traditional banks will adopt cryptocurrency or create their own solutions?\"\n"
        "2. \"I'm interested in fintech. What blockchain architectures do you find most promising for high-volume transactions?\"\n"
        "3. \"Do you think regulators will eventually stabilize cryptocurrency markets, or will DeFi remain largely independent?\"\n"
        "\n"
        f"Event: {event_description}\n"
        f"Themes: {themes_str}\n"
        f"Interests: {interests_str}\n"
        "Conversation Starters:\n"
        "1. \""
    )

    try:
        generator = get_generator()
        # Generate with parameters that balance creativity and structure
        outputs = generator(
            prompt,
            max_new_tokens=150,
            num_return_sequences=1,
            temperature=0.75,
            top_k=40,
            top_p=0.9,
            pad_token_id=50256,
            clean_up_tokenization_spaces=True
        )
        
        generated_text = outputs[0]['generated_text']
        # Extract the portion generated after our prompt (starting with the '1. "')
        new_text = generated_text[len(prompt) - 4:] # keep "1. \"" for parsing
        
        # Parse conversation starters by looking for numbered list items
        starters = []
        # Match lines like: 1. "Starter text" or 1. Starter text
        pattern = r'\d+\.\s*["\']?(.*?)["\']?$'
        
        for line in new_text.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                starter = match.group(1).strip()
                if starter and len(starter) > 10:  # avoid trivial sentences
                    # Ensure it has a question mark or period at the end
                    if not starter.endswith(('?', '.', '!')):
                        starter += "?"
                    starters.append(starter)
            
            if len(starters) >= 3:
                break
                
        # Clean up any trailing unclosed quotes
        starters = [s.rstrip('"').rstrip("'").strip() for s in starters]
        
        # Fallback if parsing failed or model didn't produce enough output
        if len(starters) < 2:
            raise ValueError("Failed to generate sufficient starters from model output")
            
        return starters

    except Exception as e:
        logger.error(f"Error during GPT-2 generation: {e}")
        # Return elegant template-based fallback starters tailored to user inputs
        fallback = []
        if interests:
            primary_interest = interests[0]
            fallback.append(f"Hi! I noticed we both have an interest in {primary_interest}. What do you think is the biggest trend in this area at this event?")
        else:
            fallback.append("Hi there! What aspect of this event are you most looking forward to today?")
            
        if themes:
            primary_theme = themes[0]
            fallback.append(f"This event covers some fascinating themes, especially {primary_theme}. How does your current work align with that?")
        else:
            fallback.append("I'd love to hear your thoughts on the keynote presentation. Did anything stand out to you?")
            
        fallback.append(f"With all the talks on {themes_str} and {interests_str}, where do you see the industry heading in the next few years?")
        
        return fallback[:3]

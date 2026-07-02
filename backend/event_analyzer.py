import logging
from typing import List
from transformers import pipeline

logger = logging.getLogger(__name__)

# Global cache for the classifier pipeline
_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        logger.info("Loading DistilBERT zero-shot classification model...")
        # Use typeform/distilbert-base-uncased-mnli for DistilBERT-based zero-shot classification
        _classifier = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli"
        )
        logger.info("DistilBERT zero-shot classification model loaded successfully.")
    return _classifier

def extract_themes(event_description: str, candidate_labels: List[str], threshold: float = 0.2) -> List[str]:
    """
    Extracts relevant themes from the event description using zero-shot classification.
    """
    if not event_description or not candidate_labels:
        return []
    
    try:
        classifier = get_classifier()
        # Clean labels to remove empty strings
        labels = [label.strip() for label in candidate_labels if label.strip()]
        if not labels:
            return []
            
        result = classifier(event_description, candidate_labels=labels)
        
        # Filter labels based on classification score threshold
        extracted = [
            label for label, score in zip(result['labels'], result['scores'])
            if score >= threshold
        ]
        
        # If nothing matches the threshold, take the top 1
        if not extracted and result['labels']:
            extracted = [result['labels'][0]]
            
        return extracted
    except Exception as e:
        logger.error(f"Error extracting themes: {e}")
        # Fallback to simple keyword matching if model fails
        fallback_themes = []
        for label in candidate_labels:
            if label.lower() in event_description.lower():
                fallback_themes.append(label)
        return fallback_themes if fallback_themes else [candidate_labels[0]]

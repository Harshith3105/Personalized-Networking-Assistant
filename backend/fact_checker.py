import logging
import httpx
import wikipediaapi
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Initialize Wikipedia API wrapper with user agent as required by Wikimedia policy
# User-agent must be descriptive and follow Wikimedia guidelines
USER_AGENT = "PersonalizedNetworkingAssistant/1.0 (networking.assistant@example.com)"

wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent=USER_AGENT
)

def search_wikipedia_title(query: str) -> str:
    """
    Uses the Wikimedia opensearch API to find the most relevant Wikipedia page title for a query.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 3,
        "namespace": 0,
        "format": "json"
    }
    headers = {
        "User-Agent": USER_AGENT
    }
    try:
        response = httpx.get(url, params=params, headers=headers, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            # OpenSearch response structure: [query, [titles], [descriptions], [links]]
            titles = data[1]
            if titles:
                return titles[0]  # Return the best match title
    except Exception as e:
        logger.error(f"Error searching Wikipedia for query '{query}': {e}")
    return query

def get_fact_check(query: str) -> Dict[str, Any]:
    """
    Retrieves a summary and URL for the specified query from Wikipedia.
    Supports fallback to the primary keyword if the exact multi-word concept page is not found.
    """
    if not query or not query.strip():
        return {
            "query": query,
            "success": False,
            "error": "Query cannot be empty"
        }

    search_query = query.strip()
    try:
        # Step 1: Find the most relevant page title for the full query
        best_title = search_wikipedia_title(search_query)
        logger.info(f"Fact check search for '{search_query}' resolved to title: '{best_title}'")
        
        page = wiki.page(best_title)
        
        # Step 2: Fallback to the first word (primary keyword) if the page doesn't exist
        if not page.exists():
            words = [w for w in search_query.split() if len(w) > 2]  # ignore small words like "in", "of", "and"
            if words:
                fallback_query = words[0]
                logger.info(f"Page '{best_title}' does not exist. Falling back to primary keyword: '{fallback_query}'")
                best_title = search_wikipedia_title(fallback_query)
                page = wiki.page(best_title)
        
        if page.exists():
            # Get summary and limit length for concise reading
            summary = page.summary
            if len(summary) > 600:
                summary = summary[:600] + "..."
                
            return {
                "query": query,
                "title": page.title,
                "summary": summary,
                "url": page.fullurl,
                "success": True
            }
        else:
            return {
                "query": query,
                "success": False,
                "error": f"Could not find a Wikipedia page matching '{search_query}' or its keywords."
            }
    except Exception as e:
        logger.error(f"Wikipedia fact check failed for '{query}': {e}")
        return {
            "query": query,
            "success": False,
            "error": f"An error occurred while fetching information: {str(e)}"
        }

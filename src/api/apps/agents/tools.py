import textwrap
import json
import os
import requests
from agents import function_tool, Runner

from apify_client import ApifyClient

# Initialize Apify client with your API token
client = ApifyClient("apify_api_365MlxHyMWaX9JRG22msK3gHtN6hYs3hhGvW")

def get_meta_ads(niche: str):
    ads_run = client.actor("apify/facebook-ads-scraper").call(run_input={
        "startUrls": [{
            "url": f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=DZ&is_targeted_country=false&media_type=video&q={niche}&search_type=keyword_unordered"
        }],
        "resultsLimit": 10,
    })

    return list(client.dataset(ads_run["defaultDatasetId"]).iterate_items())


@function_tool
def generate_description(
    product_name: str,
    product_description: str,
    marketing_perspective: str,
    prompt_lang: str
) -> str:
    """
    Generates an HTML snippet (<h2> title + <p> description) tailored
    for a single marketing perspective.
    """
    # We’ll send a prompt to the LLM using the pattern you provided:
    base_prompt = textwrap.dedent(f"""
        Generate in {prompt_lang} an HTML snippet for {product_name} that:
        - Starts with a <h2> heading as a catchy title
        - Then a <p> formatted description:
            * Use at least 300 words
            * Capture attention with a compelling intro
            * Explain features & benefits using bullet points and emojis
            * Use persuasive power‑words
            * Include a clear, strong call‑to‑action
        Tailor the entire copy with the '{marketing_perspective}' marketing angle.
        Product brief: "{product_description}"
    """).strip()

    # Here you'd normally call the LLM with `openai.chat.completions.create(...)`
    # For now we just return the prompt so you can hook it up:
    return base_prompt


def send_post_request(
    endpoint_url: str,
    payload: dict,
    headers: dict[str, str] | None = None
) -> requests.Response:
    """
    Send a blocking POST request with the given JSON payload to the specified endpoint.

    Args:
        endpoint_url: The full URL to send the POST to.
        payload_json: The JSON string to post as the request body.
        headers: Optional HTTP headers to include.

    Returns:
        The requests.Response object.
    """
    response = requests.post(endpoint_url, json=payload, headers=headers)
    return response

async def generate_marketing_versions(
    marketing_agent,
    product_name: str,
    marketing_perspectives: list[str],
    prompt_lang: str = "en"
) -> str:
    """
    Generate marketing versions for a product using the Marketing Copy Agent.

    Args:
        product_name: Name of the product.
        product_description: Short factual description of the product.
        marketing_perspectives: List of marketing angles (e.g., ["urgency", "social proof"]).
        prompt_lang: Language code for generation (e.g., "en").

    Returns:
        A JSON string output from the agent containing versions per perspective.
    """
    
    prompt = (
        f"Generate marketing copy for the product “{product_name}”:\n"
        f"- Product Name: {product_name}\n"
        
        f"- Language: {prompt_lang}\n\n"
        "For each of the three perspectives, return a JSON object with:\n"
        "  • perspective: the marketing angle (e.g. “urgency”)\n"
        "  • title: a compelling headline\n"
        "  • description: an HTML <p>…</p> block of at least 300 words, using headings, bullet points with emojis, persuasive power words, and ending with a clear call to action.\n\n"
        "Output ONLY valid JSON."
    )
    
    result = await Runner.run(marketing_agent, input=prompt, max_turns=20)
    base_url = os.getenv("API_BASE_URL", "https://example.com/api")
    endpoint = f"{base_url.rstrip('/')}/agent-create-lps/"
    headers = {"Content-Type": "application/json", "Authorization": f"Token {os.getenv('API_KEY')}"}

    # Send the blocking POST request (will block the event loop)

    # jsonfiy the final output
    final_output_dict = result.final_output.dict()
    
    response = send_post_request(endpoint, final_output_dict, headers)
    
    return response
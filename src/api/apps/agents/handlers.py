from agents import Agent, Runner

from openai import OpenAI

from typing import Annotated, List
from fastapi import APIRouter, Body, Request, status
from core.dependencies import AsyncSessionDependency
from core.schemas.responses import JSENDResponseSchema

from src.api.apps.agents.schemas import (
    WinningProductRequestSchema,
    WinningProductResponseSchema,
    DummyOkaddoProduct,
    AgentResponseSchema,
    ProductInfo,
)
from src.api.apps.agents.tools import get_meta_ads, generate_description, generate_marketing_versions

wp_agent = Agent(
    name="WPAgent", 
    instructions=
    "You are a product research agent. Your task is to find the winning product for a given niche"
    "Make sure the provided information is related to Algeria"
    "Make sure the score is between 0 and 100",
    output_type=WinningProductResponseSchema,
)

product_agent = Agent(
    name="ProductAgent", 
    instructions=
    "You are a product suggestion agent. Your task is to generate products for a given niche"
    "Make sure the location is of this format: 'city, country'"
    "Make sure the provided information is related to Algeria",
    output_type=List[DummyOkaddoProduct]
)

marketing_agent = Agent(
    name="Marketing Copy Agent",
    instructions=(
        "You are an expert e‑commerce copywriter.  \n"
        "**Inputs** (as a JSON object):\n"
        "- `product_name`: the name of the product (string)\n"
        "- `product_description`: a short factual description (string)\n"
        "- `marketing_perspectives`: a list of angles to write from, e.g. [\"urgency\",\"social proof\",\"self‑care\"]\n"
        "- `prompt_lang`: language code for generation, e.g. \"en\" or \"fr\"\n\n"
        "**Task**: For _each_ marketing perspective, produce:\n"
        "  1. A `<h2>` headline that captures attention and reflects that perspective.\n"
        "  2. A `<p>` block of **at least 300 words** that:\n"
        "     - Opens with a compelling introduction tying the product to the perspective.\n"
        "     - Uses bullet‑style points (e.g. `•`) and emojis to highlight **features** and **benefits**.\n"
        "     - Incorporates persuasive “power words” (e.g. “limited”, “exclusive”, “guaranteed”).\n"
        "     - Concludes with a **strong call‑to‑action** inviting immediate purchase or sign‑up.\n"
        "  3. A `buy_button_message`: a concise, action‑oriented call‑to‑action button label (e.g. “Buy Now – Limited Stock!”).\n"
        "  4. An `announcement_bar`: a short announcement text suitable for a site banner (e.g. “Hurry! 20% off today only”).\n\n"
        "**Generation details**:\n"
        "- Tailor tone & vocabulary to the `prompt_lang` locale.\n"
        "- Vary structure & examples per perspective.\n"
        "- Avoid any markdown; output _only_ valid HTML for `html` and plain text for other fields.\n"
        "- Do not include any extra commentary or code blocks.\n\n"
        "**Workflow**:\n"
        "1. For each string in `marketing_perspectives`:\n"
        "   - Call `generate_description(product_name, product_description, perspective, prompt_lang)` to get the HTML snippet.\n"
        "   - Have the agent itself generate `buy_button_message` and `announcement_bar` based on the same perspective.\n"
        "2. Assemble a JSON object with this exact schema (no extra fields):\n\n"
        "```json\n"
        "{\n"
        "  \"name\": \"<same as input name>\",\n"
        "  \"price\": <input price or propose a reasonable price based on the knowledge about that product you can get, make sure to return it as a string containing the price in a decimal form, no more>,\n"
        "  \"photos\": [<input photos list>],\n"
        "  \"versions\": [\n"
        "    {\n"
        "      \"perspective\": \"urgency\",\n"
        "      \"html\": \"<h2>…</h2><p>…</p>\",\n"
        "      \"buy_button_message\": \"…\",\n"
        "      \"announcement_bar\": \"…\"\n"
        "    },\n"
        "    …\n"
        "  ]\n"
        "}```\n"
        "**OUTPUT REQUIREMENT**: your final output must be _only_ the JSON object above—no explanatory text, no code fences.\n"
    ),
    tools=[generate_description],
    output_type=ProductInfo,
)

client = OpenAI()


async def find_wining_product(
    request: Request,
    data: Annotated[
        WinningProductRequestSchema,
        Body(
            openapi_examples={
                "Simple Example": {
                    "value": {
                        "niche": "fitness",
                        "source": "meta",
                    },
                },
            },
        ),
    ],
    session: AsyncSessionDependency,
):
    """API endpoint to find the winning product."""

    meta_ads = get_meta_ads(data.niche)
    
    scored_ads = []
    
    for ad in meta_ads:
        user_prompt = f"""Score this ad for the niche "{data.niche}". 
                    Ad details: {ad}
                    Return a dictionary with:
                    - 'title': ad page name
                    - 'description': short ad text or caption
                    - 'score': relevance score from 0 to 100
                    """

        result = await Runner.run(
            wp_agent,
            user_prompt,
        )

        # You may need to parse the result here depending on your runner setup
        try:
            scored_ads.append(result.final_output)
        except Exception as e:
            print(f"Error processing ad: {e}")  
            continue  # skip bad ads

    # Step 3: Select highest score
    winning_ad = max(scored_ads, key=lambda x: x.score, default=None)

    suggested_products = await Runner.run(
        product_agent,
        f"Suggest me 4 products for the niche {data.niche} and description {winning_ad}",
    )

    winning_product_image = client.images.generate(
        model="dall-e-3",
        prompt=f"Create a product image for the winning product: {winning_ad}",
        size="1024x1024",
        quality="standard",
        n=1,
    )

    winning_ad.image_url = winning_product_image.data[0].url

    sugested_products_images = client.images.generate(
        model="dall-e-2",
        prompt=f"Create a product image for the winning product: {winning_ad}",
        size="256x256",
        quality="standard",
        n=4,
    )

    for i, product in enumerate(suggested_products.final_output):
        product.image_url = sugested_products_images.data[i].url

    return JSENDResponseSchema[AgentResponseSchema](
        data=AgentResponseSchema(winning_product=winning_ad, suggestions=suggested_products.final_output),
        message="Winning product found.",
        code=status.HTTP_200_OK,
    )

async def generate_landing_page(
    request: Request,
    data: Annotated[
        ProductInfo,
        Body(
            openapi_examples={
                "Simple Example": {
                    "value": {
                        "name": "Product Name",
                        "description": "Product Description",
                        "price": 19.99,
                        "photos": ["url1", "url2"],
                    },
                },
            },
        ),
    ],
    session: AsyncSessionDependency,
):
    """API endpoint to generate a landing page."""

    res = await generate_marketing_versions(
        marketing_agent,
        product_name=data.name,
        marketing_perspectives=data.versions,
        prompt_lang="en",
    )

    if res.status_code == 201:
        return JSENDResponseSchema(
            data=None,
            message="Landing page generated.",
            code=status.HTTP_200_OK,
        )
    else:
        return JSENDResponseSchema(
            data=None,
            message="Failed to generate landing page.",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
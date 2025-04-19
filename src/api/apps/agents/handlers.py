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
)
from src.api.apps.agents.tools import get_meta_ads

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
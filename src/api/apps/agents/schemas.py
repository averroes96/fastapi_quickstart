from enum import Enum

from pydantic import Field, BaseModel

from typing_extensions import TypedDict
from typing import List

from core.schemas.requests import BaseRequestSchema
from core.schemas.responses import BaseResponseSchema


class Source(str, Enum):
    META = "meta"
    TIKTOK = "tiktok"

class Niche(str, Enum):
    FITNESS = "Fitness"
    BEAUTY = "Beauté"
    FASHION = "Mode"
    HOME = "Maison"
    PETS = "Animaux"
    KITCHEN = "Cuisine"
    GADGETS = "Gadgets"
    ELECTRONICS = "Électronique"
    SPORTS = "Sports"
    TOYS = "Jouets"
    TRAVEL = "Voyage"
    AUTOMOTIVE = "Automobile"
    HEALTH = "Santé"
    GARDEN = "Jardin"
    OUTDOORS = "Extérieur"


class WinningProductRequestSchema(BaseRequestSchema):
    """Request schema for finding the winning product."""

    niche: Niche = Field(
        title="Niche",
        description="The niche for which to find the winning product.",
    )
    source: Source = Field(
        default=Source.META,
        title="Source",
        description="The source of the product information.",
    )

class DummyOkaddoProduct(BaseResponseSchema):
    name: str
    description: str
    price: float
    supplier: str
    location: str
    image_url: str


class WinningProductResponseSchema(BaseResponseSchema):
    """Response schema for finding the winning product."""
    title: str 
    description: str 
    score: float
    image_url: str

class AgentResponseSchema(BaseResponseSchema):
    winning_product: WinningProductResponseSchema
    suggestions: list[DummyOkaddoProduct]


class MarketingVariation(BaseModel):
    perspective: str
    html: str
    buy_button_message: str
    announcement_bar: str

class ProductInfo(BaseModel):
    name: str
    price: str
    photos: List[str]
    versions: List[MarketingVariation] | None
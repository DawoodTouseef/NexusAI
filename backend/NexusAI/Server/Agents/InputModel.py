from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

class Phi3_Input(BaseModel):
    """Inputs to the wikipedia tool."""

    query: str= Field(
        description="query to Microsoft Phi3 Model"
    )
    max_tokens:int=Field(description="Maximum number of tokens to predict when generating text. (Default: 128, -1 = infinite generation, -2 = fill context)",default=5000)

class HuggingGpt_Input(BaseModel):
    """Inputs to the wikipedia tool."""

    query: str= Field(
        description="query to HuggingLlama"
    )






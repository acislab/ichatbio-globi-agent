from enum import Enum
from typing import Type

import httpx
from pydantic import BaseModel, create_model
from pydantic import Field

InteractionTypes: Type[Enum]
InteractionSearchParameters: Type[BaseModel]

def get_interaction_types() -> Type[Enum]:
    with httpx.Client() as client:
        response = client.get("https://api.globalbioticinteractions.org/interactionTypes")
        interaction_types = list(response.json())
        as_enum = Enum("InteractionType", {t: t for t in interaction_types})
        return as_enum

def init_models():
    global InteractionTypes, InteractionSearchParameters
    InteractionTypes = get_interaction_types()

    InteractionSearchParameters = create_model(
        "InteractionSearchParameters",
        subject_taxon=(str, Field(description="The taxonomic group that will be interacting with other groups")),
        interaction_type=(InteractionTypes, Field(description="The query will match other taxonomic groups that have this type of interaction with the subject taxon"))
    )

init_models()

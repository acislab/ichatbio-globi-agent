import json
from typing import override, Optional

import dotenv
import httpx
from ichatbio.agent import IChatBioAgent
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.server import build_agent_app
from ichatbio.types import AgentCard, AgentEntrypoint
from instructor import from_openai, AsyncInstructor
from instructor.core.retry import InstructorRetryException
from openai import AsyncOpenAI
from pydantic import BaseModel
from starlette.applications import Starlette

from schema import InteractionSearchParameters
from src.util import csv_to_json

dotenv.load_dotenv()

class GlobiAgent(IChatBioAgent):
    @override
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="GloBI (Global Biotic Interactions)",
            description="Finds recorded interactions between organisms of different taxonomic groups.",
            icon="https://raw.githubusercontent.com/globalbioticinteractions/logo/refs/heads/main/globi_256x256.png",
            url="http://localhost:9999",
            entrypoints=[
                AgentEntrypoint(
                    id="find_interactions",
                    description="Generates a list of taxonomic groups that have a certain type of interaction with a"
                                " taxonomic group of interest. For example, this entrypoint can list organisms that"
                                " prey on Rattus rattus.",
                    parameters=None
                )
            ]
        )

    @override
    async def run(self, context: ResponseContext, request: str, entrypoint: str, params: Optional[BaseModel]):
        async with context.begin_process(summary="Searching GloBI") as process:
            process: IChatBioAgentProcess

            async with httpx.AsyncClient() as client:
                await process.log("Generating search parameters for the iDigBio's media records API")
                p = await _get_interactions_api_parameters(request)
                await process.log(f"Generated search parameters", data=p.model_dump(mode="json"))

                csv_api_query_url = f"https://api.globalbioticinteractions.org/taxon/{p.subject_taxon}/{p.interaction_type.value}?type=csv"
                await process.log(f"Sending a GET request to the GloBI API at {csv_api_query_url}")
                response = await client.get(csv_api_query_url)
                csv_interactions = response.text

            interactions = csv_to_json(csv_interactions)
            num_interactions = len(interactions)
            num_interaction_types = len({entry.get("interaction_type") for entry in interactions})
            await process.log(f"Found {num_interactions} distinct interaction(s) across {num_interaction_types} interaction type(s)")

            await process.create_artifact(
                mimetype="application/json",
                description=f"List of taxa that \"{p.subject_taxon}\" relates to as \"{p.interaction_type.value}\" or similar",
                content=json.dumps(interactions).encode(),
                metadata={
                    "derived_from": csv_api_query_url,
                    "source": "GloBI"
                }
            )


SEARCH_PARAMETER_GENERATION_PROMPT = """\
Your task is to turn user requests into search parameters for use with Global Biotic Interactions' interactions search
API.
"""

async def _get_interactions_api_parameters(request: str) -> InteractionSearchParameters:
    try:
        client: AsyncInstructor = from_openai(AsyncOpenAI())
        result = await client.chat.completions.create(
            model="gpt-4.1-unfiltered",
            temperature=0,
            response_model=InteractionSearchParameters,
            messages=[
                {"role": "system", "content": SEARCH_PARAMETER_GENERATION_PROMPT},
                {"role": "user", "content": request}
            ],
            max_retries=3
        )
    except InstructorRetryException as e:
        raise ValueError("Failed to generate valid search parameters") from e

    return result

def create_app() -> Starlette:
    agent = GlobiAgent()
    app = build_agent_app(agent)
    return app

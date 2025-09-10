import importlib.resources
import json
import os

import dotenv
import pytest
from agent import GlobiAgent
from ichatbio.agent_response import ProcessBeginResponse, ProcessLogResponse, ArtifactResponse

from src.util import csv_to_json

dotenv.load_dotenv()

def all_traffic_except_llm(request):
    return not str(request.url).startswith(os.getenv("OPENAI_BASE_URL"))

@pytest.mark.asyncio
@pytest.mark.httpx_mock(should_mock=all_traffic_except_llm)
async def test_globi_agent(context, messages, httpx_mock):
    mock_csv_data = importlib.resources.files("resources").joinpath("naja_naja_eaten_by.csv").read_text()
    mock_json_data = csv_to_json(mock_csv_data)
    httpx_mock.add_response(url="https://api.globalbioticinteractions.org/taxon/Naja naja/eatenBy?type=csv",
                            text=mock_csv_data)

    await GlobiAgent().run(context, "What eats Naja naja?", "find_interactions", None)

    assert messages == [
        ProcessBeginResponse(summary='Searching GloBI'),
        ProcessLogResponse(text="Generating search parameters for the iDigBio's media records API"),
        ProcessLogResponse(text='Generated search parameters',
                           data={'subject_taxon': 'Naja naja', 'interaction_type': 'eatenBy'}),
        ProcessLogResponse(text='Sending a GET request to the GloBI API at https://api.globalbioticinteractions.org/taxon/Naja naja/eatenBy?type=csv'),
        ProcessLogResponse(text='Found 4 distinct interaction(s) across 3 interaction type(s)'),
        ArtifactResponse(mimetype='application/json',
                         description='List of taxa that "Naja naja" relates to as "eatenBy" or similar',
                         content=json.dumps(mock_json_data).encode(),
                         metadata={
                             'derived_from': 'https://api.globalbioticinteractions.org/taxon/Naja naja/eatenBy?type=csv',
                             'source': 'GloBI'
                         })
    ]

import pytest

from src.schema import InteractionTypes, InteractionSearchParameters



def test_valid_interaction_type():
    InteractionTypes("eats")

def test_invalid_interaction_type():
    with pytest.raises(ValueError):
        InteractionTypes("pets")

def test_list_interaction_types():
    interaction_types = [t.value for t in InteractionTypes]
    known_types = {"eats", "eatenBy", "preysOn"}
    assert set(interaction_types) & known_types == known_types

def test_interaction_search_parameters():
    InteractionSearchParameters(subject_taxon="Rattus", interaction_type="eats")
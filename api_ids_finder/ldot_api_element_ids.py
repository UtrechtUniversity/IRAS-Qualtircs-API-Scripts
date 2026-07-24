# ============================================================
#  ldot_api_element_ids.py
# ------------------------------------------------------------
#  A helpful script with functions for finding API element IDs for the LDOT API.
#  Not meant for production — just to help the developer find the IDs needed for
#  populating studies and work units in the study_configs yaml. Should
#  only be needed once per study, when setting up the study_configs.yaml file.
#  
#  Intentionally requires some manual input from the developer in filling in some variables.
#
#
#  Author:  Carmel Suchard
#  Date:    2026-07-24
# ============================================================

import requests
from dotenv import dotenv_values


###### Set up the Qualtrics API base URL and headers

LDOT_API_URL = "https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1"
LDOT_TOKEN_URL = (
    "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token"
)


# Put the path to the .env file for the study you are working on here.
# This is where the LDOT client ID and secret are stored.
study_env_path = "app-secrets/piama-sandbox.env"
study_env = dotenv_values(study_env_path)

# LDOT_STUDY_ID goes here. It can be found only by the Ldot developers.
LDOT_STUDY_ID = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"

# The custom variable used to store the survey linked can be found in Ldot in the Study Builder environment,
# by clicking on Entities -> Deelnemer -> OTHER (CUSTOM VARIABLES) EDIT VARIABLES


############

def get_headers() -> dict:
    """Get the access token for the LDOT API using client credentials."""
    response = requests.post(
        LDOT_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": study_env.get("LDOT_client_id"),
            "client_secret": study_env.get("LDOT_client_secret"),
        },
    )
    response.raise_for_status()
    token = response.json()["access_token"]

    headers={"accept": "application/json",
            "Authorization": f"Bearer {token}"
            }

    return headers


def get_deelnemer_entity_id(study_id: str):
    """Get the entity ID for the Ldot API study element 'Deelnemer'"""
    headers = get_headers()
    response = requests.get(
        f"{LDOT_API_URL}/{study_id}/Entity/",
        headers=headers,
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise Exception(f"Failed to get entity IDs, status code: {response.status_code}, message: {response.text}")

    else:
        entities = response.json().get("Data", {}).get("StudyEntities", [])
        entity_ids = {entity["Description"]: entity["Guid"] for entity in entities if entity["Description"] == "Deelnemer"}

        return entity_ids

def get_study_location_id(study_id: str):
    """Get the entity ID for the Ldot API study element 'Location'"""
    headers = get_headers()
    response = requests.get(
        f"{LDOT_API_URL}/{study_id}/Location/",
        headers=headers,
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise Exception(f"Failed to get entity IDs, status code: {response.status_code}, message: {response.text}")

    else:
        location_id = response.json().get("Data", {}).get("StudyLocations", [])

        return location_id

def get_eaids_of_all_event_actions(study_id: str):
    """Get the EAIDs of all event actions for a given study ID"""
    headers = get_headers()
    response = requests.get(
        f"{LDOT_API_URL}/{study_id}/Action/",
        headers=headers,
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise Exception(f"Failed to get event action IDs, status code: {response.status_code}, message: {response.text}")

    else:
        actions_list = response.json().get("Data", {}).get("StudyEventActions", [])
        actions_list = {action["Description"]: action["EventActionGuid"] for action in actions_list}
        return actions_list


if __name__ == "__main__":
    ### Get the entity IDs for the study ###
    # deelnemer_entity_id = get_deelnemer_entity_id(LDOT_STUDY_ID)
    # print(deelnemer_entity_id)

    ### Get the StudyLocation Ids for the study ###
    # location_entity_id = get_study_location_id(LDOT_STUDY_ID)
    # print(location_entity_id)


    ### Get the EAIDs of all event actions for the study, so you can find the trigger and resolution EAIDs for the work units ###
    # event_action_ids = get_eaids_of_all_event_actions(LDOT_STUDY_ID)
    # for description, eaid in event_action_ids.items():
    #     print(f"Description: {description}, EAID: {eaid}", "\n \n")

    pass
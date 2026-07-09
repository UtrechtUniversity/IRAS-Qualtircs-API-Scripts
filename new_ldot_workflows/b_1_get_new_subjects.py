import json
import requests

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]

def get_new_subjects(study_id: str, eaid_qualtrics_survey_link_creation_to_do_date: str, eaid_qualtrics_survey_link_completed: str) -> list:
    """Get subjects that have not yet been added to Qualtrics by checking their event actions"""

    response = requests.post(
        "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )

    token = response.json()["access_token"]

    headers={"accept": "application/json",
            "Authorization": f"Bearer {token}"
            }

    # Get subjects that have link creation to do date
    response = requests.get(
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action/{eaid_qualtrics_survey_link_creation_to_do_date}",
        headers=headers
    )

    response.raise_for_status()
    payload = response.json()
    study_event_actions = payload.get("Data", {}).get("StudyEventActions", [])

    subjects_link_creation_to_do = set([
        action["SubjectGuid"]
        for action in study_event_actions
        if action.get("SubjectGuid")
    ])

    # print(f"Subjects with link creation to do: {subjects_link_creation_to_do}")

    # Get subjects that have link completed date
    response = requests.get(
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action/{eaid_qualtrics_survey_link_completed}",
        headers=headers
    )
    response.raise_for_status()
    payload = response.json()
    study_event_actions_completed = payload.get("Data", {}).get("StudyEventActions", [])
    subjects_link_completed = set([
        action["SubjectGuid"]
        for action in study_event_actions_completed
        if action.get("SubjectGuid")
    ])

    # print(f"Subjects with link completed: {subjects_link_completed}")

    # Filter out subjects that have already completed the link
    new_subjects = subjects_link_creation_to_do - subjects_link_completed

    # print(f"New subjects: {new_subjects}")
    return list(new_subjects)



if __name__ == "__main__":
    # For testing purposes
    print(get_new_subjects("5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b", "5d31129c-d814-5d4b-a96f-048cadc150ce", "31599192-8e9b-4341-b7f4-8b8967dd846a"))

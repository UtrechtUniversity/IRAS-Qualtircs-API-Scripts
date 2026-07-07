import json
import requests

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]


def get_incomplete_subjects(study_id: str, eaid_survey_invitation_completed: str = None, eaid_survey_progress_completed: str = None) -> list:
    """Get subjects that have not yet completed the survey by checking their event actions"""

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

    # actions = requests.get(
    #     f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action",
    #     headers=headers
    # )

    # actions.raise_for_status()
    # payload = actions.json()
    # # print(payload)
    # action_guids = []
    # for action in payload.get("Data", {}).get("StudyEventActions", []):
    #     action_guids.append((action["EventActionGuid"], action["Description"]))

    # for guid, description in action_guids:
    #     people_with_this_action = requests.get(
    #         f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action/{guid}",
    #         headers=headers
    #     )
    #     people_with_this_action.raise_for_status()
    #     if "Data" in people_with_this_action.json():
    #         print (people_with_this_action.json()["Data"]["StudyEventActions"])


    # # Get SubjectIDs where survey invitation has been completed but survey progress has not been completed
    result = requests.get(
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action/{eaid_survey_invitation_completed}",
        headers=headers
    )
    result.raise_for_status()

    subjects_with_survey_invitation_completed = set()
    for action in result.json().get("Data", {}).get("StudyEventActions", []):
        subjects_with_survey_invitation_completed.add(action["SubjectGuid"])

    print(f"Subjects with survey invitation completed: {subjects_with_survey_invitation_completed}")

    result = requests.get(
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action/{eaid_survey_progress_completed}",
        headers=headers
    )
    result.raise_for_status()

    subjects_with_survey_progress_completed = set()
    for action in result.json().get("Data", {}).get("StudyEventActions", []):
        subjects_with_survey_progress_completed.add(action["SubjectGuid"])

    print(f"Subjects with survey progress completed: {subjects_with_survey_progress_completed}")

    incomplete_subjects = subjects_with_survey_invitation_completed - subjects_with_survey_progress_completed
    return list(incomplete_subjects)

if __name__ == "__main__":
    print(get_incomplete_subjects("5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b", "9f09f2cf-32cc-844d-9a41-7a44accd3dfd", '120d298d-9aa9-084b-abc6-432148db0e10'))

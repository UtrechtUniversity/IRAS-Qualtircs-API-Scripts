import json
import requests

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]


def send_progress_to_ldot(ldot_study_id: str, eaid_survey_progress_completed: str, participant_to_progress_dict: dict) -> list:
    """If percent is 100, change the event action for the subject to indicate that the survey has been completed"""

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

    for subject_id, progress in participant_to_progress_dict.items():
        if progress != '100':
            print(f"Subject {subject_id} has not completed the survey (progress: {progress}%). Skipping.")
            continue

        # Add Qualtrics survey link completed event action for the subject
        response = requests.post(
            f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{ldot_study_id}/Action/{eaid_survey_progress_completed}/",
            headers=headers,
            params = {
                "subjectGuid": subject_id,
            }
        )

        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        response_data = response.json()
        print(f"Successfully sent link for subject {subject_id} to Ldot. Response: {response_data}")


if __name__ == "__main__":
    ldot_study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    id_deelnemer_entity = "7f61b810-00ed-1d41-8a33-4164f25ebad0"
    id_location = "427f304f-9d95-44f5-8f7b-d6a1ce1db293"
    participant_to_progress_dict = {'352fb9d8-962f-4735-9fc7-7b4e18109a51': '100'}
    custom_var_qualtrics_link = "customVar01"
    link_completed_eaid = "31599192-8e9b-4341-b7f4-8b8967dd846a"
    eaid_survey_progress_completed = "120d298d-9aa9-084b-abc6-432148db0e10"

    send_progress_to_ldot(ldot_study_id, eaid_survey_progress_completed, participant_to_progress_dict)
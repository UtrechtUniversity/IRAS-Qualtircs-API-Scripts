import json
import requests

from new_ldot_workflows.logging_utils import logged_request

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]


def _response_snippet(response: requests.Response, limit: int = 300) -> str:
    text = response.text.strip().replace("\n", " ")
    return text[:limit]


def _format_response_error(prefix: str, response: requests.Response) -> str:
    return f"{prefix} (status {response.status_code}): {_response_snippet(response)}"

def get_new_subjects(study_id: str, eaid_qualtrics_survey_link_creation_to_do_date: str, eaid_qualtrics_survey_link_completed: str) -> list:
    """Get subjects that have not yet been added to Qualtrics by checking their event actions"""

    print(f"Inputs into get_new_subjects: study_id={study_id}, eaid_qualtrics_survey_link_creation_to_do_date={eaid_qualtrics_survey_link_creation_to_do_date}, eaid_qualtrics_survey_link_completed={eaid_qualtrics_survey_link_completed}")

    response = logged_request(
        "POST",
        "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token",
        function_name="get_new_subjects",
        service="Ldot",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        },
        raise_for_status=True,
    )

    try:
        token_payload = response.json()
    except ValueError as e:
        raise ValueError(_format_response_error("LDOT token endpoint returned invalid JSON", response)) from e

    token = token_payload.get("access_token")
    if not token:
        raise ValueError(_format_response_error("LDOT token endpoint did not include an access_token", response))

    headers={"accept": "application/json",
            "Authorization": f"Bearer {token}"
            }

    # Get subjects that have link creation to do date
    response = logged_request(
        "GET",
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action/{eaid_qualtrics_survey_link_creation_to_do_date}",
        function_name="get_new_subjects",
        service="Ldot",
        headers=headers,
        raise_for_status=True,
    )

    try:
        payload = response.json()
    except ValueError as e:
        raise ValueError(_format_response_error("LDOT creation-to-do lookup returned invalid JSON", response)) from e
    study_event_actions = payload.get("Data", {}).get("StudyEventActions", [])

    subjects_link_creation_to_do = set([
        action["SubjectGuid"]
        for action in study_event_actions
        if action.get("SubjectGuid")
    ])

    print(f"Subjects with link creation to do: {subjects_link_creation_to_do}")

    # Get subjects that have link completed date
    response = logged_request(
        "GET",
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Action/{eaid_qualtrics_survey_link_completed}",
        function_name="get_new_subjects",
        service="Ldot",
        headers=headers,
        raise_for_status=True,
    )

    try:
        payload = response.json()
    except ValueError as e:
        raise ValueError(_format_response_error("LDOT completed lookup returned invalid JSON", response)) from e
    study_event_actions_completed = payload.get("Data", {}).get("StudyEventActions", [])
    subjects_link_completed = set([
        action["SubjectGuid"]
        for action in study_event_actions_completed
        if action.get("SubjectGuid")
    ])

    print(f"Subjects with link completed: {subjects_link_completed}")

    # Filter out subjects that have already completed the link
    new_subjects = subjects_link_creation_to_do - subjects_link_completed

    print(f"New subjects: {new_subjects}")
    return list(new_subjects) if new_subjects else []



if __name__ == "__main__":
    # For testing purposes
    print(get_new_subjects("5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b", "5d31129c-d814-5d4b-a96f-048cadc150ce", "31599192-8e9b-4341-b7f4-8b8967dd846a"))

from new_ldot_workflows.logging_utils import logged_request

def get_new_subjects(ldot_client, study_id: str, eaid_qualtrics_survey_link_creation_to_do_date: str, eaid_qualtrics_survey_link_completed: str) -> list:
    """Get subjects that have not yet been added to Qualtrics by checking their event actions"""

    # Get subjects that have link creation to do date
    response = logged_request(
        "GET",
        f"{ldot_client.api_url}/{study_id}/Action/{eaid_qualtrics_survey_link_creation_to_do_date}",
        function_name="get_new_subjects",
        service="Ldot",
        headers=ldot_client.headers,
        raise_for_status=True,
    )

    try:
        payload = response.json()
    except ValueError as e:
        raise ValueError("Ldot lookup to find subjects with link creation to do date returned invalid JSON", response) from e
    study_event_actions = payload.get("Data", {}).get("StudyEventActions", [])

    subjects_link_creation_to_do = set([
        action["SubjectGuid"]
        for action in study_event_actions
        if action.get("SubjectGuid")
    ])

    # Get subjects that have link completed date
    response = logged_request(
        "GET",
        f"{ldot_client.api_url}/{study_id}/Action/{eaid_qualtrics_survey_link_completed}",
        function_name="get_new_subjects",
        service="Ldot",
        headers=ldot_client.headers,
        raise_for_status=True,
    )

    try:
        payload = response.json()
    except ValueError as e:
        raise ValueError("Ldot lookup to find subjects with link creation completed returned invalid JSON", response) from e
    study_event_actions_completed = payload.get("Data", {}).get("StudyEventActions", [])
    subjects_link_completed = set([
        action["SubjectGuid"]
        for action in study_event_actions_completed
        if action.get("SubjectGuid")
    ])

    # Filter out subjects that have already completed the link
    new_subjects = subjects_link_creation_to_do - subjects_link_completed

    return list(new_subjects) if new_subjects else []


if __name__ == "__main__":
    # For testing purposes
    print(get_new_subjects("5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b", "5d31129c-d814-5d4b-a96f-048cadc150ce", "31599192-8e9b-4341-b7f4-8b8967dd846a"))

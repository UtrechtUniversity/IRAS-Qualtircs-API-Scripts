from new_ldot_workflows.logging_utils import logged_request

def get_incomplete_subjects(ldot_client, study_id: str, eaid_survey_invitation_completed: str = None, eaid_survey_progress_completed: str = None) -> list:
    """Get subjects that have not yet completed the survey by checking their event actions"""

    print("Inputs to get_incomplete_subjects: study_id={}, eaid_survey_invitation_completed={}, eaid_survey_progress_completed={}".format(study_id, eaid_survey_invitation_completed, eaid_survey_progress_completed))

    # Get SubjectIDs where survey invitation has been completed but survey progress has not been completed
    result = logged_request(
        "GET",
        f"{ldot_client.api_url}/{study_id}/Action/{eaid_survey_invitation_completed}",
        function_name="get_incomplete_subjects",
        service="Ldot",
        headers=ldot_client.headers,
        raise_for_status=True,
    )

    subjects_with_survey_invitation_completed = set()

    # print(result.json())
    # for action in result.json().get("Data", {}).get("StudyEventActions", []):
    #     subjects_with_survey_invitation_completed.add(action["SubjectGuid"])

    # print(f"Subjects with survey invitation completed: {subjects_with_survey_invitation_completed}")

    result = logged_request(
        "GET",
        f"{ldot_client.api_url}/{study_id}/Action/{eaid_survey_progress_completed}",
        function_name="get_incomplete_subjects",
        service="Ldot",
        headers=ldot_client.headers,
        raise_for_status=True,
    )
    print(result.json())

    # subjects_with_survey_progress_completed = set()
    # for action in result.json().get("Data", {}).get("StudyEventActions", []):
    #     subjects_with_survey_progress_completed.add(action["SubjectGuid"])

    # print(f"Subjects with survey progress completed: {subjects_with_survey_progress_completed}")

    # incomplete_subjects = subjects_with_survey_invitation_completed - subjects_with_survey_progress_completed
    # return list(incomplete_subjects)

if __name__ == "__main__":
    # This would typically be initialized with the actual Ldot client
    ldot_client = None  # Replace with actual Ldot client initialization
    ldot_study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    eaid_survey_invitation_completed = "337ecba2-3dd3-1141-8c38-6cffdcfbd7eb"
    eaid_survey_progress_completed = "120d298d-9aa9-084b-abc6-432148db0e10"
    print(get_incomplete_subjects(ldot_study_id, eaid_survey_invitation_completed, eaid_survey_progress_completed))

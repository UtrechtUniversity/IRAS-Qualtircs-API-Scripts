from new_ldot_workflows.logging_utils import logged_request


def send_progress_to_ldot(
    ldot_client,
    ldot_study_id: str,
    eaid_survey_progress_completed: str,
    participant_to_progress_dict: dict,
) -> list:
    """If percent is 100, change the event action for the subject to indicate that the survey has been completed"""

    for subject_id, progress in participant_to_progress_dict.items():
        if progress != "100":
            continue

        # Add Qualtrics survey link completed event action for the subject
        _ = logged_request(
            "POST",
            f"{ldot_client.api_url}/{ldot_study_id}/Action/{eaid_survey_progress_completed}/",
            function_name="send_progress_to_ldot",
            service="Ldot",
            headers=ldot_client.headers,
            params={
                "subjectGuid": subject_id,
            },
            raise_for_status=True,
        )


if __name__ == "__main__":
    ldot_study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    id_deelnemer_entity = "7f61b810-00ed-1d41-8a33-4164f25ebad0"
    id_location = "427f304f-9d95-44f5-8f7b-d6a1ce1db293"
    participant_to_progress_dict = {"352fb9d8-962f-4735-9fc7-7b4e18109a51": "100"}
    custom_var_qualtrics_link = "customVar01"
    link_completed_eaid = "31599192-8e9b-4341-b7f4-8b8967dd846a"
    eaid_survey_progress_completed = "120d298d-9aa9-084b-abc6-432148db0e10"

    # send_progress_to_ldot(
    #     ldot_client,
    #     ldot_study_id,
    #     eaid_survey_progress_completed,
    #     participant_to_progress_dict,
    # )

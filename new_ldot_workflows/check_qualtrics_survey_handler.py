def handle_check_qualtrics_survey_module(ldot_client, qualtrics_client, study_variables, unit):
    v = unit.boolean_action.get("variables", {})
    ldot_study_id = study_variables.ldot_variables.get("ldot_study_id")

    subject_ids = get_incomplete_subjects(
        ldot_client, ldot_study_id, unit.trigger, unit.resolution
    )
    if not subject_ids:
        return {"message": "No incomplete subjects found"}

    participant_to_progress_dict = get_individual_progress(
        ldot_client, qualtrics_client, ldot_study_id,
        study_variables.ldot_variables.get("id_deelnemer_entity"),
        study_variables.ldot_variables.get("id_location"),
        subject_ids,
        v.get("embedded_data_field"),
        v.get("qualtrics_survey_id"),
    )
    send_progress_to_ldot(
        ldot_client, ldot_study_id, unit.resolution, participant_to_progress_dict
    )
    return {
        "message": f"Retrieved progress for {len(participant_to_progress_dict)} subjects",
        "progress_results": participant_to_progress_dict,
    }

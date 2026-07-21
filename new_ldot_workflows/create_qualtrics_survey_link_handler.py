def handle_create_qualtrics_survey_link(ldot_client, qualtrics_client, study_variables, unit):
    print("ldot_client:", ldot_client)
    print("qualtrics_client:", qualtrics_client)
    print("study_variables:", study_variables)
    print("unit:", unit)
    # v = unit.boolean_action.get("variables", {})
    # ldot_study_id = study_variables.ldot_variables.get("ldot_study_id")

    # new_subject_ids = get_new_subjects(
    #     ldot_client, ldot_study_id, unit.trigger, unit.resolution
    # )
    # if not new_subject_ids:
    #     return {"message": "No new subjects to process"}

    # subject_id_to_link_dict = add_individuals_to_survey(
    #     ldot_client, qualtrics_client, new_subject_ids,
    #     ldot_study_id,
    #     study_variables.ldot_variables.get("id_deelnemer_entity"),
    #     v.get("embedded_data_field"),
    #     v.get("distribution_id"),
    #     v.get("qualtrics_survey_id"),
    #     v.get("mailing_list_id"),
    #     v.get("directory_id"),
    # )
    # send_links_to_ldot(
    #     ldot_client, ldot_study_id,
    #     study_variables.ldot_variables.get("id_deelnemer_entity"),
    #     study_variables.ldot_variables.get("id_location"),
    #     v.get("ldot_custom_var_qualtrics_link"),
    #     unit.resolution,
    #     subject_id_to_link_dict,
    # )
    # return {
    #     "message": f"Processed {len(new_subject_ids)} subject IDs",
    #     "subject_id_to_link_dict": subject_id_to_link_dict,
    # }
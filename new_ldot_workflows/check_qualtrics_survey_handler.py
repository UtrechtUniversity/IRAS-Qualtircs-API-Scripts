class SurveyLinkWorkflow:
    def __init__(self, ldot_client, qualtrics_client, ldot_study_id, id_deelnemer_entity, id_location):
        self.ldot_client = ldot_client
        self.qualtrics_client = qualtrics_client
        self.ldot_study_id = ldot_study_id
        self.id_deelnemer_entity = id_deelnemer_entity
        self.id_location = id_location
    
    def run(self, trigger, resolution, qualtrics_survey_id, embedded_data_field):
        pass

def handle_check_qualtrics_survey_module(ldot_client, qualtrics_client, study_variables, unit):
    ldot_variables = study_variables.ldot_variables
    ldot_study_id = ldot_variables.get("ldot_study_id")
    id_deelnemer_entity = ldot_variables.get("id_deelnemer_entity")
    id_location = ldot_variables.get("id_location")

    workflow = SurveyLinkWorkflow(ldot_client, qualtrics_client, ldot_study_id, id_deelnemer_entity, id_location)
    v = unit.boolean_action.get("variables", {})

    return workflow.run(
        trigger=unit.trigger,
        resolution=unit.resolution,
        qualtrics_survey_id=v.get("qualtrics_survey_id"),
        embedded_data_field=v.get("embedded_data_field"),
    )

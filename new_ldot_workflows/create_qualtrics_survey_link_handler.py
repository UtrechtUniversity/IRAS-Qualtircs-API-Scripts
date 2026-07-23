from new_ldot_workflows.logging_utils import logged_request


class SurveyLinkWorkflow:
    def __init__(self, ldot_client, qualtrics_client, ldot_study_id, id_deelnemer_entity, id_location):
        self.ldot_client = ldot_client
        self.qualtrics_client = qualtrics_client
        self.ldot_study_id = ldot_study_id
        self.id_deelnemer_entity = id_deelnemer_entity
        self.id_location = id_location

    def run(self, trigger, resolution, mailing_list_id, directory_id, embedded_data_field, qualtrics_survey_id, distribution_id, ldot_custom_var_qualtrics_link):
        ready_subject_ids = self._get_ready_subjects(
            eaid_qualtrics_survey_link_creation_to_do_date=trigger,
        )

        subjectID_to_link_dict = {}
        for subject_id in ready_subject_ids:
            individual_study_identifier = self._convert_api_subject_id_to_study_identifier(subject_id)
            contact_exists = self._check_contact_in_mailing_list(individual_study_identifier, mailing_list_id, directory_id)

            if not contact_exists:
                self._add_contact_to_mailing_list(individual_study_identifier, embedded_data_field, mailing_list_id, directory_id)
            
            personal_link = self._get_personal_link(
                qualtrics_survey_id, distribution_id, individual_study_identifier
            )
            subjectID_to_link_dict[subject_id] = personal_link


        for subject_id, link in subjectID_to_link_dict.items():
            self._send_links_to_ldot(subject_id, link, ldot_custom_var_qualtrics_link)
            
            self._add_link_completed_action(subject_id, resolution)

        return {
            "message": f"Processed {len(subjectID_to_link_dict)} subject IDs",
        }


    def _send_links_to_ldot(self, subject_id, link, custom_var_qualtrics_link):
            response = logged_request(
                "POST",
                f"{self.ldot_client.api_url}/{self.ldot_study_id}/Subject/",
                function_name="send_links_to_ldot",
                service="Ldot",
                headers=self.ldot_client.headers,
                json = {
                    "subjectGuid": subject_id,
                    "entityId": self.id_deelnemer_entity,
                    "locationSubjectId": self.id_location,
                    custom_var_qualtrics_link: link, # Custom var that corresponds to the Qualtrics link in Ldot
                    "doOverwriteNulls": False,
                },
                raise_for_status=True,
            )

    def _add_link_completed_action(self, subject_id, resolution):
        # Add Qualtrics survey link completed event action for the subject
        response = logged_request(
            "POST",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Action/{resolution}/",
            function_name="add_link_completed_action",
            service="Ldot",
            headers=self.ldot_client.headers,
            params = {
                "subjectGuid": subject_id,
            },
            raise_for_status=True,
        )


    def _get_personal_link(self, qualtrics_survey_id: str, distribution_id: str, individual_study_identifier: str) -> str:
        """ Get the person link of an individual for a specified survey. Returns personal link for the participant, looks like
            https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHLqe2Pdrma&_g_=g
        """
        parameters = {
            "surveyId": str(qualtrics_survey_id)
        }
        response = logged_request(
            "GET",
            f"{self.qualtrics_client.api_url}/distributions/{distribution_id}/links",
            function_name="get_personal_link",
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            params=parameters,
            raise_for_status=True,
        )
        data = response.json()
        personal_link = [item["link"] for item in data["result"]["elements"] if ("externalDataReference" in item) and (item["externalDataReference"] == individual_study_identifier)][0]        
        return personal_link
    

    def _add_contact_to_mailing_list(self, individual_study_identifier, embedded_data_field, mailing_list_id, directory_id):
        contact_information_payload ={
            "extRef": individual_study_identifier,
            "embeddedData": {
                embedded_data_field: individual_study_identifier
            }
        }
        response = logged_request(
            "POST",
            f"{self.qualtrics_client.api_url}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts",
            function_name="add_contact_to_mailing_list",
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            json=contact_information_payload,
            raise_for_status=True,
        )


    def _get_ready_subjects(self, eaid_qualtrics_survey_link_creation_to_do_date: str) -> list:
        """Get subjects that have not yet been added to Qualtrics by checking their event actions"""

        # Get subjects that have link creation to do date
        response = logged_request(
            "GET",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Action/{eaid_qualtrics_survey_link_creation_to_do_date}",
            function_name="get_ready_subjects",
            service="Ldot",
            headers=self.ldot_client.headers,
            raise_for_status=True,
        )
        try:
            payload = response.json()
        except ValueError as e:
            raise ValueError("Ldot lookup to find subjects with Qualtricslink creation to do date returned invalid JSON", response) from e
        study_event_actions = payload.get("Data", {}).get("StudyEventActions", [])

        subjects_link_creation_to_do = set([
            action["SubjectGuid"]
            for action in study_event_actions
            if action.get("SubjectGuid")
        ])

        return subjects_link_creation_to_do      

    def _convert_api_subject_id_to_study_identifier(self, api_subject_id):
        """Convert subject ID used by the Ldot API to study identifier that can be used in Qualtrics surveys"""

        response = logged_request(
            "GET",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Entity/{self.id_deelnemer_entity}",
            function_name="convert_api_subject_id_to_study_identifier",
            service="Ldot",
            headers=self.ldot_client.headers,
            raise_for_status=True,
        )
        
        subject_ids = response.json().get("Data", {}).get("SubjectIds")
        guid_to_registration_id = {subject["Guid"]: subject["RegistrationId"] for subject in subject_ids if "Guid" in subject and "RegistrationId" in subject}

        individual_study_identifier = guid_to_registration_id.get(api_subject_id)
        return individual_study_identifier


    def _check_contact_in_mailing_list(self, individual_study_identifier: str, mailing_list_id: str, directory_id: str) -> bool:
        """Find who is already in that mailing list, check if the participant's ID is already there."""

        response = logged_request(
            "GET",
            f"{self.qualtrics_client.api_url}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts",
            function_name="check_contact_in_mailing_list",
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            raise_for_status=True,
        )
        contacts =  response.json()["result"]["elements"]
        contact_external_data_references = [contact["extRef"] for contact in contacts if "extRef" in contact]

        if individual_study_identifier not in contact_external_data_references:
            return False
        return True

def handle_create_qualtrics_survey_link(ldot_client, qualtrics_client, study_variables, unit):
    ldot_variables = study_variables.ldot_variables
    ldot_study_id = ldot_variables.get("ldot_study_id")
    id_deelnemer_entity = ldot_variables.get("id_deelnemer_entity")
    id_location = ldot_variables.get("id_location")

    workflow = SurveyLinkWorkflow(ldot_client, qualtrics_client, ldot_study_id, id_deelnemer_entity, id_location)
    v = unit.boolean_action.get("variables", {})

    return workflow.run(
        trigger=unit.trigger,
        resolution=unit.resolution,
        mailing_list_id=v.get("mailing_list_id"),
        directory_id=v.get("directory_id"),
        embedded_data_field=v.get("embedded_data_field"),
        ldot_custom_var_qualtrics_link=v.get("ldot_custom_var_qualtrics_link"),
        qualtrics_survey_id=v.get("qualtrics_survey_id"),
        distribution_id=v.get("distribution_id")
    )

from new_ldot_workflows.logging_utils import logged_request


class TwoSurveyLinksWorkflow:
    def __init__(
        self,
        work_unit_name: str,
        ldot_client,
        qualtrics_client,
        ldot_study_id,
        id_deelnemer_entity,
        id_location,
    ):
        self.work_unit_name = work_unit_name
        self.ldot_client = ldot_client
        self.qualtrics_client = qualtrics_client
        self.ldot_study_id = ldot_study_id
        self.id_deelnemer_entity = id_deelnemer_entity
        self.id_location = id_location

    def run(
        self,
        trigger,
        resolution,
        mailing_list_id_1,
        mailing_list_id_2,
        directory_id,
        embedded_data_field_1,
        embedded_data_field_2,
        qualtrics_survey_id_1,
        qualtrics_survey_id_2,
        distribution_id_1,
        distribution_id_2,
        ldot_custom_var_qualtrics_link_1,
        ldot_custom_var_qualtrics_link_2,
    ):
        yield {
            "type": "progress",
            "message": "Looking for subjects ready for a survey links...",
        }

        ready_subject_ids = self._get_ready_subjects(
            eaid_qualtrics_survey_link_creation_to_do_date=trigger,
        )

        yield {
            "type": "progress",
            "message": f"Found {len(ready_subject_ids)} subjects ready for survey links...",
        }

        if len(ready_subject_ids) == 0:
            yield {"type": "done", "message": "Done."}
            return

        subject_guid_to_registration_id = self._get_subject_id_mapping()

        yield {
            "type": "progress",
            "message": "Checking if any of the ready subjects are already in the mailing list...",
        }

        existing_contacts_1 = self._get_mailing_list_contacts(
            mailing_list_id_1, directory_id
        )

        existing_contacts_2 = self._get_mailing_list_contacts(
            mailing_list_id_2, directory_id
        )

        subjectID_to_link_dict_1 = {}
        subjectID_to_link_dict_2 = {}
        skipped_subject_ids_1 = []
        skipped_subject_ids_2 = []

        yield {
            "type": "progress",
            "message": "Adding new contacts to the mailing list...",
        }

        yield {
            "type": "progress",
            "message": "Getting personal links for ready subjects...",
        }

        for subject_id in ready_subject_ids:
            individual_study_identifier = subject_guid_to_registration_id.get(
                subject_id
            )
            contact_exists_1 = individual_study_identifier in existing_contacts_1
            contact_exists_2 = individual_study_identifier in existing_contacts_2

            if not contact_exists_1:
                self._add_contact_to_mailing_list(
                    individual_study_identifier,
                    embedded_data_field_1,
                    mailing_list_id_1,
                    directory_id,
                )

            if not contact_exists_2:
                self._add_contact_to_mailing_list(
                    individual_study_identifier,
                    embedded_data_field_2,
                    mailing_list_id_2,
                    directory_id,
                )

            personal_link_1 = self._get_personal_link(
                qualtrics_survey_id_1, distribution_id_1, individual_study_identifier
            )

            if personal_link_1 is None:
                skipped_subject_ids_1.append(subject_id)
                continue

            subjectID_to_link_dict_1[subject_id] = personal_link_1

            personal_link_2 = self._get_personal_link(
                qualtrics_survey_id_2, distribution_id_2, individual_study_identifier
            )

            if personal_link_2 is None:
                skipped_subject_ids_2.append(subject_id)
                continue

            subjectID_to_link_dict_2[subject_id] = personal_link_2

        yield {
            "type": "progress",
            "message": "Sending the survey links back to Ldot...",
        }
        yield {
            "type": "progress",
            "message": "Marking link completion action in Ldot...",
        }

        for subject_id, link in subjectID_to_link_dict_1.items():
            self._send_links_to_ldot(subject_id, link, ldot_custom_var_qualtrics_link_1)

        for subject_id, link in subjectID_to_link_dict_2.items():
            self._send_links_to_ldot(subject_id, link, ldot_custom_var_qualtrics_link_2)

        # Add link completed action only after both links were created
        for subject_id in set(subjectID_to_link_dict_1.keys()).intersection(
            set(subjectID_to_link_dict_2.keys())
        ):
            self._add_link_completed_action(subject_id, resolution)

        yield {
            "type": "done",
            "message": "Done.",
            "skipped_subject_ids": sorted(
                set(skipped_subject_ids_1 + skipped_subject_ids_2)
            ),
        }

    def _send_links_to_ldot(self, subject_id, link, custom_var_qualtrics_link):
        _ = logged_request(
            "POST",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Subject/",
            function_name="send_links_to_ldot",
            work_unit_name=self.work_unit_name,
            service="Ldot",
            headers=self.ldot_client.headers,
            json={
                "subjectGuid": subject_id,
                "entityId": self.id_deelnemer_entity,
                "locationSubjectId": self.id_location,
                custom_var_qualtrics_link: link,  # Custom var that corresponds to the Qualtrics link in Ldot
                "doOverwriteNulls": False,
            },
            raise_for_status=True,
        )

    def _add_link_completed_action(self, subject_id, resolution):
        # Add Qualtrics survey link completed event action for the subject
        _ = logged_request(
            "POST",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Action/{resolution}/",
            function_name="add_link_completed_action",
            work_unit_name=self.work_unit_name,
            service="Ldot",
            headers=self.ldot_client.headers,
            params={
                "subjectGuid": subject_id,
            },
            raise_for_status=True,
        )

    def _get_personal_link(
        self,
        qualtrics_survey_id: str,
        distribution_id: str,
        individual_study_identifier: str,
    ) -> str:
        """Get the person link of an individual for a specified survey. Returns personal link for the participant, looks like
        https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHLqe2Pdrma&_g_=g
        """
        parameters = {"surveyId": str(qualtrics_survey_id)}
        response = logged_request(
            "GET",
            f"{self.qualtrics_client.api_url}/distributions/{distribution_id}/links",
            function_name="get_personal_link",
            work_unit_name=self.work_unit_name,
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            params=parameters,
            raise_for_status=True,
        )
        data = response.json()
        personal_link = next(
            (
                item["link"]
                for item in data["result"]["elements"]
                if item.get("externalDataReference") == individual_study_identifier
            ),
            None,
        )

        return personal_link

    def _add_contact_to_mailing_list(
        self,
        individual_study_identifier,
        embedded_data_field,
        mailing_list_id,
        directory_id,
    ):
        contact_information_payload = {
            "extRef": individual_study_identifier,
            "embeddedData": {embedded_data_field: individual_study_identifier},
        }
        _ = logged_request(
            "POST",
            f"{self.qualtrics_client.api_url}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts",
            function_name="add_contact_to_mailing_list",
            work_unit_name=self.work_unit_name,
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            json=contact_information_payload,
            raise_for_status=True,
        )

    def _get_ready_subjects(
        self, eaid_qualtrics_survey_link_creation_to_do_date: str
    ) -> list:
        """Get subjects that have not yet been added to Qualtrics by checking their event actions"""

        # Get subjects that have link creation to do date
        response = logged_request(
            "GET",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Action/{eaid_qualtrics_survey_link_creation_to_do_date}",
            function_name="get_ready_subjects",
            work_unit_name=self.work_unit_name,
            service="Ldot",
            headers=self.ldot_client.headers,
            raise_for_status=True,
        )
        try:
            payload = response.json()
        except ValueError as e:
            raise ValueError(
                "Ldot lookup to find subjects with Qualtricslink creation to do date returned invalid JSON",
                response,
            ) from e
        study_event_actions = payload.get("Data", {}).get("StudyEventActions", [])

        subjects_link_creation_to_do = set(
            [
                action["SubjectGuid"]
                for action in study_event_actions
                if action.get("SubjectGuid")
            ]
        )

        return subjects_link_creation_to_do

    def _get_subject_id_mapping(self):
        """Convert subject ID used by the Ldot API to study identifier that can be used in Qualtrics surveys"""

        response = logged_request(
            "GET",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Entity/{self.id_deelnemer_entity}",
            function_name="get_subject_id_mapping",
            work_unit_name=self.work_unit_name,
            service="Ldot",
            headers=self.ldot_client.headers,
            raise_for_status=True,
        )

        subject_ids = response.json().get("Data", {}).get("SubjectIds")
        subject_guid_to_registration_id = {
            subject["Guid"]: subject["RegistrationId"]
            for subject in subject_ids
            if "Guid" in subject and "RegistrationId" in subject
        }

        return subject_guid_to_registration_id

    def _get_mailing_list_contacts(
        self, mailing_list_id: str, directory_id: str
    ) -> bool:
        """Find which contacts are already in that mailing list."""

        response = logged_request(
            "GET",
            f"{self.qualtrics_client.api_url}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts",
            function_name="get_mailing_list_contacts",
            work_unit_name=self.work_unit_name,
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            raise_for_status=True,
        )
        contacts = response.json()["result"]["elements"]
        contact_external_data_references = [
            contact["extRef"] for contact in contacts if "extRef" in contact
        ]

        return set(contact_external_data_references)


def handle_create_two_qualtrics_survey_links(
    ldot_client, qualtrics_client, study_variables, unit
):
    ldot_variables = study_variables.ldot_variables
    ldot_study_id = ldot_variables.get("ldot_study_id")
    id_deelnemer_entity = ldot_variables.get("id_deelnemer_entity")
    id_location = ldot_variables.get("id_location")
    work_unit_name = unit.name  # Get the name of the work unit

    workflow = TwoSurveyLinksWorkflow(
        work_unit_name,
        ldot_client,
        qualtrics_client,
        ldot_study_id,
        id_deelnemer_entity,
        id_location,
    )
    v = unit.work_action.get("variables", {})

    yield from workflow.run(
        trigger=unit.trigger,
        resolution=unit.resolution,
        mailing_list_id_1=v.get("mailing_list_id_1"),
        mailing_list_id_2=v.get("mailing_list_id_2"),
        directory_id=v.get("directory_id"),
        qualtrics_survey_id_1=v.get("qualtrics_survey_id_1"),
        qualtrics_survey_id_2=v.get("qualtrics_survey_id_2"),
        distribution_id_1=v.get("distribution_id_1"),
        distribution_id_2=v.get("distribution_id_2"),
        embedded_data_field_1=v.get("embedded_data_field_1"),
        embedded_data_field_2=v.get("embedded_data_field_2"),
        ldot_custom_var_qualtrics_link_1=v.get("ldot_custom_var_qualtrics_link_1"),
        ldot_custom_var_qualtrics_link_2=v.get("ldot_custom_var_qualtrics_link_2"),
    )

from new_ldot_workflows.logging_utils import logged_request
import pandas as pd
from time import sleep
import zipfile
import io


class QualtricsExportService:
    def __init__(self, qualtrics_client, survey_id: str):
        self.qualtrics_client = qualtrics_client
        self.survey_id = survey_id

    def get_full_responses(self) -> pd.DataFrame:
        """Wrapper function that gets the individual progress of a participant in a survey."""
        # Check for invalid inputs

        completed_responses_df = self._get_responses_as_df(incomplete_bool=False)
        incompleted_responses_df = self._get_responses_as_df(incomplete_bool=True)
        df = pd.concat(
            [completed_responses_df, incompleted_responses_df], ignore_index=True
        )

        return df

    def _get_responses_as_df(self, incomplete_bool: bool) -> pd.DataFrame:
        """Wrapper function to request export, wait for it, download it, and convert to DataFrame."""
        # Request a data export
        request_id = self._create_data_export(incomplete_bool=incomplete_bool)

        # Ping the export report repeatedly until it's ready
        export_progress = 0.0
        while export_progress < 100:
            export_progress = self._check_export_progress(
                request_id, returns="percent_complete"
            )
            sleep(2)

        # When export is complete, get the file ID
        file_id = self._check_export_progress(request_id, returns="fileID")
        df = self._download_export(file_id)
        return df

    def _create_data_export(self, incomplete_bool: bool = True) -> str:
        """Create a data export request for a given survey"""

        payload = {"format": "csv", "exportResponsesInProgress": incomplete_bool}
        response = logged_request(
            "POST",
            f"{self.qualtrics_client.api_url}/surveys/{self.survey_id}/export-responses",
            function_name="create_data_export",
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            json=payload,
            raise_for_status=True,
        )
        request_id = response.json()["result"]["progressId"]
        return request_id

    def _check_export_progress(self, request_id: str, returns: str) -> str | float:
        result = logged_request(
            "GET",
            f"{self.qualtrics_client.api_url}/surveys/{self.survey_id}/export-responses/{request_id}",
            function_name="check_export_progress",
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            raise_for_status=True,
        )

        if returns == "percent_complete":
            percent_complete = result.json()["result"]["percentComplete"]
            return percent_complete
        elif returns == "fileID":
            file_id = result.json()["result"]["fileId"]
            return file_id

    def _download_export(self, file_id: str) -> pd.DataFrame:
        """Download the exported survey data and convert to DataFrame"""

        download = logged_request(
            "GET",
            f"{self.qualtrics_client.api_url}/surveys/{self.survey_id}/export-responses/{file_id}/file",
            function_name="download_export",
            service="Qualtrics",
            headers=self.qualtrics_client.headers,
            stream=True,
            raise_for_status=True,
        )

        with zipfile.ZipFile(io.BytesIO(download.content)) as z:
            csv_name = [name for name in z.namelist() if name.endswith(".csv")][0]
            with z.open(csv_name) as f:
                df = pd.read_csv(f)
        return df


class CheckSurveyProgressWorkflow:
    def __init__(
        self,
        ldot_client,
        qualtrics_client,
        ldot_study_id,
        id_deelnemer_entity,
        id_location,
    ):
        self.ldot_client = ldot_client
        self.qualtrics_client = qualtrics_client
        self.ldot_study_id = ldot_study_id
        self.id_deelnemer_entity = id_deelnemer_entity
        self.id_location = id_location

    def run(self, trigger, resolution, qualtrics_survey_id, embedded_data_field):

        ready_subject_ids = self._get_ready_subjects(
            eaid_qualtrics_survey_progress_to_do_date=trigger,
        )

        if not ready_subject_ids:
            return {
                "message": "No subjects found in-progress of this survey",
            }

        subject_id_to_study_identifier_dict = self._subject_id_to_study_identifier(
            ready_subject_ids
        )
        subject_id_to_progress_dict = {}

        qualtrics_export_service = QualtricsExportService(
            self.qualtrics_client, qualtrics_survey_id
        )
        responses_df = qualtrics_export_service.get_full_responses()

        if embedded_data_field not in responses_df.columns:
            raise ValueError(
                f"Embedded data field '{embedded_data_field}' not found in survey data. Please check the field name."
            )

        for subject_id, study_identifier in subject_id_to_study_identifier_dict.items():
            if study_identifier is None:
                subject_id_to_progress_dict[subject_id] = (
                    0  # Indicator that the subject ID was not found in the data
                )
                continue
            individual_progress = responses_df[
                responses_df[embedded_data_field] == study_identifier
            ]
            if not individual_progress.empty:
                # If multiple rows, get the lowest progress value (assuming lower progress means less complete), make sure that is a float
                progress_percentage = (
                    individual_progress["Progress"].astype(float).min()
                )
                subject_id_to_progress_dict[subject_id] = progress_percentage
            else:
                subject_id_to_progress_dict[subject_id] = (
                    0  # Indicator that the subject ID was not found in the data
                )

        self._send_progress_to_ldot(subject_id_to_progress_dict, resolution)

        return {
            "message": f"Checked progress for {len(subject_id_to_progress_dict)} subjects",
            "progress_results": subject_id_to_progress_dict,
        }

    def _subject_id_to_study_identifier(self, ready_subject_ids: list) -> dict:
        subject_id_to_study_identifier_dict = {}
        for subject_id in ready_subject_ids:
            response = logged_request(
                "POST",
                f"{self.ldot_client.api_url}/{self.ldot_study_id}/Subject/",
                function_name="subject_id_to_study_identifier",
                service="Ldot",
                headers=self.ldot_client.headers,
                json={
                    "subjectGuid": subject_id,
                    "entityId": self.id_deelnemer_entity,
                    "locationSubjectId": self.id_location,
                    "doOverwriteNulls": False,
                },
                raise_for_status=True,
            )
            subject_id_to_study_identifier_dict[subject_id] = (
                response.json()
                .get("Data", {})
                .get("Subject", {})
                .get("RegistrationId", None)
            )

        return subject_id_to_study_identifier_dict

    def _get_ready_subjects(
        self, eaid_qualtrics_survey_progress_to_do_date: str
    ) -> list:
        """Get subjects that have not yet been added to Qualtrics by checking their event actions"""

        # Get subjects that have survey progress to do date
        response = logged_request(
            "GET",
            f"{self.ldot_client.api_url}/{self.ldot_study_id}/Action/{eaid_qualtrics_survey_progress_to_do_date}",
            function_name="get_ready_subjects",
            service="Ldot",
            headers=self.ldot_client.headers,
            raise_for_status=True,
        )
        try:
            payload = response.json()
        except ValueError as e:
            raise ValueError(
                "Ldot lookup to find subjects with Qualtrics survey progress to do date returned invalid JSON",
                response,
            ) from e
        study_event_actions = payload.get("Data", {}).get("StudyEventActions", [])

        subjects_survey_progress_to_do = set(
            [
                action["SubjectGuid"]
                for action in study_event_actions
                if action.get("SubjectGuid")
            ]
        )

        return subjects_survey_progress_to_do

    def _send_progress_to_ldot(
        self, subject_id_to_progress_dict: dict, eaid_survey_progress_completed: str
    ) -> list:
        """If percent is 100, change the event action for the subject to indicate that the survey has been completed"""

        for subject_id, progress in subject_id_to_progress_dict.items():
            if float(progress) < 100:
                continue

            # Add Qualtrics survey link completed event action for the subject
            _ = logged_request(
                "POST",
                f"{self.ldot_client.api_url}/{self.ldot_study_id}/Action/{eaid_survey_progress_completed}/",
                function_name="send_progress_to_ldot",
                service="Ldot",
                headers=self.ldot_client.headers,
                params={
                    "subjectGuid": subject_id,
                },
                raise_for_status=True,
            )


def handle_check_qualtrics_survey_module(
    ldot_client, qualtrics_client, study_variables, unit
):
    ldot_variables = study_variables.ldot_variables
    ldot_study_id = ldot_variables.get("ldot_study_id")
    id_deelnemer_entity = ldot_variables.get("id_deelnemer_entity")
    id_location = ldot_variables.get("id_location")

    workflow = CheckSurveyProgressWorkflow(
        ldot_client, qualtrics_client, ldot_study_id, id_deelnemer_entity, id_location
    )
    v = unit.boolean_action.get("variables", {})

    return workflow.run(
        trigger=unit.trigger,
        resolution=unit.resolution,
        qualtrics_survey_id=v.get("qualtrics_survey_id"),
        embedded_data_field=v.get("embedded_data_field"),
    )

import requests
import time
import zipfile
import io
import pandas as pd
import json

with open("new_ldot_workflows/qualtrics_config.json") as f:
    config = json.load(f)
QUALTRICS_BASE_URL = config["QUALTRICS_BASE_URL"]
HEADERS = config["HEADERS"]

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]

class QualtricsAPIError(Exception):
    """Custom exception for Qualtrics API errors"""
    pass

def create_data_export(survey_id: str, incomplete_bool: bool = True) -> str:
    """Create a data export request for a given survey.

    Args:
        survey_id (str): The ID of the survey to export.
        incomplete_bool (bool): Whether to export only responses that are still in progress.
    Raises:
        QualtricsAPIError: If there is an error during the request or unexpected response format.
    Returns:
        str: The ID of the data export request.
    """
    print("Creating data export request... ")
    endpoint = f"{QUALTRICS_BASE_URL}/surveys/{survey_id}/export-responses"
    payload = {
        "format": "csv",
        "exportResponsesInProgress": incomplete_bool
    }
    try:
        response = requests.post(endpoint, headers=HEADERS, json=payload)
        response.raise_for_status()   
        request_id = response.json()['result']["progressId"]
        return request_id
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while creating data export for survey {survey_id}."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when creating data export for survey {survey_id}."
        ) from exc


def check_export_progress(request_id: str, survey_id: str, returns: str) -> str|float:
    """Check if a an export request is complete

    Args:
        request_id (str): The ID of the export request.
        survey_id (str): The ID of the survey that was exported.
        returns (str): The type of information to return ("percent_complete" or "fileID").
    Raises:
        QualtricsAPIError: If there is an error during the request or unexpected response format.

    Returns:
        str: The percent complete if the request is still processing, or the file ID if complete.
    """
    print("Checking on export progress... ")
    endpoint = f"{QUALTRICS_BASE_URL}/surveys/{survey_id}/export-responses/{request_id}"
    try:
        result = requests.get(endpoint, headers=HEADERS)
        result.raise_for_status()
    
        if returns == "percent_complete":
            percent_complete = result.json()["result"]["percentComplete"]
            return percent_complete
        elif returns == "fileID":
            file_id = percent_complete = result.json()["result"]["fileId"]
            return file_id
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while checking the progress {survey_id}."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when checking the progress for survey {survey_id}."
        ) from exc
    

def download_export(file_id: str, survey_id: str) -> pd.DataFrame:
    """Download the exported survey data and convert to DataFrame.

    Args:
        file_id (str): The ID of the file to download.
        survey_id (str): The ID of the survey associated with the file.
    Raises:
        QualtricsAPIError: If there is an error during the request or unexpected response format.
    Returns:
        pd.DataFrame: The survey response data as a DataFrame.
    """
    print("Downloading export file... ")
    endpoint = f"{QUALTRICS_BASE_URL}/surveys/{survey_id}/export-responses/{file_id}/file"
    try:
        download = requests.get(
            endpoint,
            headers=HEADERS,
            stream=True
        )
        download.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(download.content)) as z:
            csv_name = [name for name in z.namelist() if name.endswith(".csv")][0]
            with z.open(csv_name) as f:
                df = pd.read_csv(f)
        return df
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while checking the progress {survey_id}."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when checking the progress for survey {survey_id}."
        ) from exc
    

def check_inputs_validity(participant_study_id: str, embedded_data_field: str, survey_id: str) -> bool:
    """Checks the validaity of arguments.

    Args:
        participant_study_id (str): ID of the participant whose progress you want to check.
        embedded_data_field (str): The field name in Qualtrics where the participant_study_id is stored.
        survey_id (str): The ID of the survey to check progress in.

    Raises:
        ValueError: If any argument is invalid.

    Returns:
        bool: True if all inputs are valid.
    """
    print("Checking input validity... ")
    if not isinstance(survey_id, str) or not survey_id.startswith("SV_"):
        raise ValueError("Invalid survey_id. It should be a string starting with 'SV_'.")
    
    if not isinstance(embedded_data_field, str) or embedded_data_field.strip() == "":
        raise ValueError("Invalid embedded_data_field. It should be a non-empty string.")
    
    if not isinstance(participant_study_id, str) or participant_study_id.strip() == "":
        raise ValueError("Invalid participant_study_id. It should be a non-empty string.")
    return True


def get_responses_as_df(survey_id: str, incomplete_bool: bool) -> pd.DataFrame:
    """Wrapper function to request export, wait for it, download it, and convert to DataFrame.

    Args:
        survey_id (str): The ID of the survey to get responses from.
        incomplete_bool (bool): Whether to get responses that are in progress or completed.

    Returns:
        pd.DataFrame: The survey response data as a DataFrame.
    """
    # Request a data export
    request_id = create_data_export(survey_id, incomplete_bool=incomplete_bool)

    # Ping the export report repeatedly until it's ready
    export_progress = 0.0
    while export_progress < 100:
        export_progress = check_export_progress(request_id, survey_id, returns="percent_complete")
        time.sleep(1.5)
        
    # When export is complete, get the file ID
    file_id = check_export_progress(request_id, survey_id, returns="fileID")
    df = download_export(file_id, survey_id)
    return df


def subject_id_to_study_identifier(ldot_study_id: str, id_deelnemer_entity: str, id_location: str, subject_ids: list) -> str:
    """Post the Qualtrics links back to Ldot for new subjects"""

    response = requests.post(
        "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    token = response.json()["access_token"]
    headers={"accept": "application/json",
            "Authorization": f"Bearer {token}"
            }

    subject_id_to_study_identifier_dict = {}
    for subject_id in subject_ids:
        # Populate the Qualtrics link in Ldot for the subject
        response = requests.post(
            f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{ldot_study_id}/Subject/",
            headers=headers,
            json = {
                "subjectGuid": subject_id,
                "entityId": id_deelnemer_entity,
                "locationSubjectId": id_location,
                "doOverwriteNulls": False,
            }
        )
        subject_id_to_study_identifier_dict[subject_id] = response.json().get("Data", {}).get("Subject").get("RegistrationId")


    return subject_id_to_study_identifier_dict


def get_individual_progress(ldot_study_id: str, id_deelnemer_entity: str, id_location: str, subject_ids: list, embedded_data_field: str, survey_id: str) -> float:
    """Wrapper function that gets the individual progress of a participant in a survey."""
    # Check for invalid inputs
    check_inputs_validity(subject_ids[0], embedded_data_field, survey_id) # TODO: Check this

    participant_to_progress_dict = {}
    subject_id_to_study_identifier_dict = subject_id_to_study_identifier(ldot_study_id, id_deelnemer_entity, id_location, subject_ids)

    completed_responses_df = get_responses_as_df(survey_id, incomplete_bool=False)
    incompleted_responses_df = get_responses_as_df(survey_id, incomplete_bool=True)
    df = pd.concat([completed_responses_df, incompleted_responses_df], ignore_index=True)
    
    if not embedded_data_field in df.columns:
        raise QualtricsAPIError(f"Embedded data field '{embedded_data_field}' not found in survey data. Please check the field name.")

    for subject_id, study_identifier in subject_id_to_study_identifier_dict.items():
        individual_progress = df[df[embedded_data_field] == study_identifier]
        print("This is the individual progress for subject_id {}, study_identifier {}: {}".format(subject_id, study_identifier, individual_progress))
        if not individual_progress.empty:
            individual_progress = individual_progress["Progress"].values[0]
            participant_to_progress_dict[subject_id] = individual_progress
        else:
            participant_to_progress_dict[subject_id] = 0  # Indicator that the subject ID was not found in the data

    return participant_to_progress_dict

if __name__ == "__main__":
    # # Example usage
    survey_id="SV_efCMOg6wHU0T8ii"
    embedded_data_field = "study_id_child"


    ldot_study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    subject_ids = ["352fb9d8-962f-4735-9fc7-7b4e18109a51"]
    id_deelnemer_entity = "7f61b810-00ed-1d41-8a33-4164f25ebad0"
    id_location = "427f304f-9d95-44f5-8f7b-d6a1ce1db293"
    embedded_data_field = "study_id_child"

    participant_to_progress_dict = get_individual_progress(ldot_study_id, id_deelnemer_entity, id_location, subject_ids, embedded_data_field, survey_id)
    print(participant_to_progress_dict)


    # subject_id_to_study_identifier_dict = subject_id_to_study_identifier(ldot_study_id, id_deelnemer_entity, id_location, subject_ids)
import requests
from qualtrics_settings import BASE_URL, HEADERS, SURVEYIDS, QualtricsAPIError
import time
import zipfile
import io
import pandas as pd

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
    endpoint = f"{BASE_URL}/surveys/{survey_id}/export-responses"
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
    endpoint = f"{BASE_URL}/surveys/{survey_id}/export-responses/{request_id}"
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
    endpoint = f"{BASE_URL}/surveys/{survey_id}/export-responses/{file_id}/file"
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

def get_individual_progress(participant_study_id: str, embedded_data_field: str, survey_id: str) -> float:
    """Wrapper function that gets the individual progress of a participant in a survey.

    Args:
        participant_study_id (str): ID of the participant whose progress you want to check.
        embedded_data_field (str): The field name in Qualtrics where the participant_study_id is stored.
        survey_id (str): The ID of the survey to check progress in.
    Raises:
        QualtricsAPIError: If the participant is not found in this survey.
    Returns:
        float: Progress of the participant in the survey (0-100).
    """
    # Check for invalid inputs
    check_inputs_validity(participant_study_id, embedded_data_field, survey_id)

    completed_responses_df = get_responses_as_df(survey_id, incomplete_bool=False)
    incompleted_responses_df = get_responses_as_df(survey_id, incomplete_bool=True)
    df = pd.concat([completed_responses_df, incompleted_responses_df], ignore_index=True)
    
    if not embedded_data_field in df.columns:
        raise QualtricsAPIError(f"Embedded data field '{embedded_data_field}' not found in survey data. Please check the field name.")

    individual_progress = df[df[embedded_data_field] == participant_study_id]
    if not individual_progress.empty:
        individual_progress = individual_progress["Progress"].values[0]
        return individual_progress
    else:
        print(f"No data found for participant_study_id: {participant_study_id} in this survey.")
        raise QualtricsAPIError("Participant not found in survey data.")

if __name__ == "__main__":
    # Example usage
    participant_study_id="11111TEST11111"
    survey_id=SURVEYIDS.my_test_survey_id
    embedded_data_field = "study_id_child"

    result = get_individual_progress(participant_study_id, embedded_data_field, survey_id)
    print(result)
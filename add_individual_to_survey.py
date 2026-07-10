import requests
from new_ldot_workflows.qualtrics_settings import BASE_URL, HEADERS, SURVEYIDS, QualtricsAPIError
from new_ldot_workflows.logging_utils import logged_request

def get_mailing_list_id_of_distribution(survey_id: str, distribution_id: str) -> str:
    """Get the mailing list ID connected to a distribution"""
    
    print("Finding mailing list ID of distribution... ")
    endpoint = f"{BASE_URL}/distributions/{distribution_id}"
    parameters = {
        "surveyId": survey_id
    }
    try:
        response = logged_request(
            "GET",
            endpoint,
            function_name="get_mailing_list_id_of_distribution",
            service="Qualtrics",
            headers=HEADERS,
            params=parameters,
            raise_for_status=True,
        )
        mailing_list_id =  response.json()["result"]["recipients"]["mailingListId"]
        
        return mailing_list_id
    
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while fetching mailing list ID for distribution {distribution_id}."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when fetching mailing list ID for distribution {distribution_id}."
        ) from exc

def get_directory_id() -> str:
    """Get the directory ID for a Qualtrics, assuming there is just one.

    Raises:
        QualtricsAPIError: If there is an error while fetching the directory ID or format is unexpected.

    Returns:
        str: The directory ID for the Qualtrics account.
    """
    print("Getting directory ID... ")
    endpoint = f"{BASE_URL}/directories"
    parameters = {
        "includeCount": False
    }
    try:
        response = logged_request(
            "GET",
            endpoint,
            function_name="get_directory_id",
            service="Qualtrics",
            headers=HEADERS,
            params=parameters,
            raise_for_status=True,
        )
        data = response.json()
        directory_id = data["result"]["elements"][0]["directoryId"]
        
        return directory_id
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while getting the directory ID."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when fetching directory ID."
        ) from exc

def check_contact_in_mailing_list(participant_study_id: str, mailing_list_id: str, directory_id: str) -> bool:
    """Find who is already in that mailing list, check if the participant's ID is already there.

    Args:
        participant_study_id (str): ID of the participant to check if they are in the mailing list.
        mailing_list_id (str): The ID of the mailing list to check.
        directory_id (str): The ID of the directory containing the mailing list.

    Returns:
        bool: True if the participant's ID is already in the mailing list, False otherwise.
    """
    print("Checking for contact in mailing list... ")
    endpoint = f"{BASE_URL}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts"
    try:
        response = logged_request(
            "GET",
            endpoint,
            function_name="check_contact_in_mailing_list",
            service="Qualtrics",
            headers=HEADERS,
            raise_for_status=True,
        )
        contacts =  response.json()["result"]["elements"]
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while checking for contact in mailing list."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when checking for contact in mailing list."
        ) from exc
    
    contact_external_data_references = [contact["extRef"] for contact in contacts if "extRef" in contact]
    

    if participant_study_id not in contact_external_data_references:
        return False
    return True

def add_contact_to_mailing_list(participant_study_id: str, mailing_list_id: str, directory_id: str, embedded_data_field: str) -> None:
    """Add contact to a mailing list

    Args:
        participant_study_id (str): ID of the participant whose progress you want to add.
        mailing_list_id (str): Mailing list to add to.
        directory_id (str): Directory containing the mailing list.
        embedded_data_field (str): The field name in Qualtrics where the participant_study_id is stored.

    Raises:
        QualtricsAPIError: If there is an error while adding the contact or format is unexpected.
    """
    print("Adding contact to mailing list... ")
    endpoint = f"{BASE_URL}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts"
    contact_information_payload ={
        "extRef": participant_study_id,
        "embeddedData": {embedded_data_field: participant_study_id}
        }
    try:
        response = logged_request(
            "POST",
            endpoint,
            function_name="add_contact_to_mailing_list",
            service="Qualtrics",
            headers=HEADERS,
            json=contact_information_payload,
            raise_for_status=True,
        )
        
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while adding contact to mailing list."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when adding contact to mailing list."
        ) from exc

def get_personal_link(survey_id: str, distribution_id: str, participant_study_id: str) -> str:
    """Get the person link of an individual for a specified survey.

    Args:
        survey_id (str): The ID of the survey to get the personal link for.
        distribution_id (str): The ID of the distribution of personal links.
        participant_study_id (str): The ID of the participant whose.

    Returns:
        str: Personal link for the participant, looks like
        https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHLqe2Pdrma&_g_=g
    """
    print("Fetching personal link... ")
    endpoint = f"{BASE_URL}/distributions/{distribution_id}/links"
    parameters = {
        "surveyId": str(survey_id)
    }
    try:
        response = logged_request(
            "GET",
            endpoint,
            function_name="get_personal_link",
            service="Qualtrics",
            headers=HEADERS,
            params=parameters,
            raise_for_status=True,
        )
        data = response.json()
        personal_link = [item["link"] for item in data["result"]["elements"] if ("externalDataReference" in item) and (item["externalDataReference"] == participant_study_id)][0]
        
        return personal_link
    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while fetching personal link of individual {participant_study_id}."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when fetching personal link of individual {participant_study_id}."
        ) from exc    

def check_inputs_validity(participant_study_id: str, embedded_data_field: str, survey_id: str, distribution_id: str) -> bool:
    print("Checking input validity... ")
    if not isinstance(participant_study_id, str) or participant_study_id.strip() == "":
        raise ValueError("Invalid participant_study_id. It should be a non-empty string.")

    if not isinstance(embedded_data_field, str) or embedded_data_field.strip() == "":
        raise ValueError("Invalid embedded_data_field. It should be a non-empty string.")

    if not isinstance(survey_id, str) or not survey_id.startswith("SV_"):
        raise ValueError("Invalid survey_id. It should be a string starting with 'SV_'.")
    
    if not isinstance(distribution_id, str) or distribution_id.strip() == "":
        raise ValueError("Invalid distribution_id. It should be a non-empty string.")
    
    return True


def add_individual_to_survey(participant_study_id, embedded_data_field, survey_id, distribution_id):
    check_inputs_validity(participant_study_id, embedded_data_field, survey_id, distribution_id)
    mailing_list_id = get_mailing_list_id_of_distribution(survey_id, distribution_id)
    print(mailing_list_id)

    # directory_id = get_directory_id()
    # contact_exists = check_contact_in_mailing_list(participant_study_id, mailing_list_id, directory_id)
    
    # if not contact_exists:
    #     add_contact_to_mailing_list(participant_study_id, mailing_list_id, directory_id)
    # else:
    #     print(f"Participant study ID {participant_study_id} already exists in this mailing list")

    # personal_link = get_personal_link(survey_id, distribution_id, participant_study_id)
    # return personal_link

if __name__ == "__main__":
    # # Example usage
    participant_study_id = "11111TEST11111"
    survey_id="SV_efCMOg6wHU0T8ii"
    distribution_id="EMD_SZFeoK7LAJBHU4d"
    embedded_data_field = "study_id_child"

    link = add_individual_to_survey(participant_study_id, embedded_data_field, survey_id, distribution_id)


    # # print(link)
    # print(get_mailing_list_id_of_distribution("SV_efCMOg6wHU0T8ii",  "EMD_SZFeoK7LAJBHU4d"))
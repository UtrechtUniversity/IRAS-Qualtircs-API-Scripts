import requests
from new_ldot_workflows.qualtrics_settings import BASE_URL, HEADERS, QualtricsAPIError
from new_ldot_workflows.logging_utils import logged_request

def get_distributions(survey_id):
    endpoint = f"{BASE_URL}/distributions"
    parameters = {
        "surveyId": survey_id,
        "distributionRequestType": "GeneratedInvite"
    }

    response = logged_request(
        "GET",
        endpoint,
        function_name="get_distributions",
        service="Qualtrics",
        headers=HEADERS,
        params=parameters,
        raise_for_status=False,
    )

    if response.status_code == 200:
        result = response.json()["result"]["elements"]
        distribution_ids = [f'{dist["id"]} created: {dist["createdDate"]}' for dist in result]
        return distribution_ids

    else:
        print(f"Error in get_distributions_of_survey: {response.text}")
        return None
    
if __name__ == "__main__":
    # Example usage
    result = get_distributions("SV_efCMOg6wHU0T8ii")
    for res in result:
        print(res)

def get_mailing_list_id_of_distribution(survey_id: str, distribution_id: str) -> str:
    """Get the mailing list ID connected to a distribution

    Args:
        survey_id (str): The ID of the survey to add someone to.
        distribution_id (str): The ID of the distribution to get the mailing list ID for.

    Raises:
        QualtricsAPIError: If there is an error while fetching the mailing list ID or format is unexpected.

    Returns:
        str: The mailing list ID connected to the distribution.
    """
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

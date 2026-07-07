import requests
import json

with open("new_ldot_workflows/qualtrics_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
QUALTRICS_BASE_URL = config["QUALTRICS_BASE_URL"]



def check_contact_in_mailing_list(participant_study_id: str, mailing_list_id: str, directory_id: str) -> bool:
    """Find who is already in that mailing list, check if the participant's ID is already there."""

    print("Checking for contact in mailing list... ")
    endpoint = f"{QUALTRICS_BASE_URL}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts"
    try:
        response = requests.get(endpoint, headers=HEADERS)
        response.raise_for_status()
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

def add_contact_to_mailing_list(participant_study_id: str, embedded_data_field: str, mailing_list_id: str, directory_id: str) -> None:
    """Add contact to a mailing list"""

    endpoint = f"{QUALTRICS_BASE_URL}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts"
    contact_information_payload ={
        "extRef": participant_study_id,
        "embeddedData": {
            embedded_data_field: participant_study_id
        }
    }
    try:
        response = requests.post(endpoint, headers=HEADERS, json=contact_information_payload)
        response.raise_for_status()

    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while adding contact to mailing list"
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when adding contact to mailing list."
        ) from exc

def get_personal_link(qualtrics_survey_id: str, distribution_id: str, participant_study_id: str) -> str:
    """Get the person link of an individual for a specified survey. Returns personal link for the participant, looks like
        https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHLqe2Pdrma&_g_=g
    """
    print(f"Fetching personal link for {participant_study_id}... ")
    endpoint = f"{QUALTRICS_BASE_URL}/distributions/{distribution_id}/links"
    parameters = {
        "surveyId": str(qualtrics_survey_id)
    }
    try:
        response = requests.get(endpoint, headers=HEADERS, params=parameters)
        response.raise_for_status()
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

def add_individuals_to_survey(participant_ids_list: list, embedded_data_field, distribution_id, qualtrics_survey_id, mailing_list_id, directory_id):
    participant_to_link_dict = {}
    for participant_id in participant_ids_list:
        contact_exists = check_contact_in_mailing_list(participant_id, mailing_list_id, directory_id)

        if not contact_exists:
            add_contact_to_mailing_list(participant_id, embedded_data_field, mailing_list_id, directory_id)
        else:
            print(f"Participant study ID {participant_id} already exists in this mailing list")

        personal_link = get_personal_link(qualtrics_survey_id, distribution_id, participant_id)

        participant_to_link_dict[participant_id] = personal_link

    return participant_to_link_dict

if __name__ == "__main__":
    # # Example usage
    participant_study_id = ["11111TEST11111", "22222TEST22222", "33333TEST33333"]
    embedded_data_field = "study_id_child"
    qualtrics_survey_id="SV_efCMOg6wHU0T8ii"
    mailing_list_id="CG_2dMbO6WUBMnCeIK"
    distribution_id="EMD_7AEa416lRwFhrkF"
    directory_id="POOL_10pyxk9leSUisrT"


    link = add_individuals_to_survey(participant_study_id, embedded_data_field, distribution_id, qualtrics_survey_id, mailing_list_id, directory_id)

    print(link)


    # print(get_mailing_list_id_of_distribution("SV_efCMOg6wHU0T8ii",  "EMD_SZFeoK7LAJBHU4d"))
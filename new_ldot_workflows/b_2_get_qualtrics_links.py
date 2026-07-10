import requests
import json

from new_ldot_workflows.logging_utils import logged_request

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

def check_contact_in_mailing_list(study_identifier: str, mailing_list_id: str, directory_id: str) -> bool:
    """Find who is already in that mailing list, check if the participant's ID is already there."""

    print("Checking for contact in mailing list... ")
    endpoint = f"{QUALTRICS_BASE_URL}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts"
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

    if study_identifier not in contact_external_data_references:
        return False
    return True

def add_contact_to_mailing_list(study_identifier: str, embedded_data_field: str, mailing_list_id: str, directory_id: str) -> None:
    """Add contact to a mailing list"""

    endpoint = f"{QUALTRICS_BASE_URL}/directories/{directory_id}/mailinglists/{mailing_list_id}/contacts"
    contact_information_payload ={
        "extRef": study_identifier,
        "embeddedData": {
            embedded_data_field: study_identifier
        }
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
            f"Error while adding contact to mailing list"
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when adding contact to mailing list."
        ) from exc

def get_personal_link(qualtrics_survey_id: str, distribution_id: str, study_identifier: str) -> str:
    """Get the person link of an individual for a specified survey. Returns personal link for the participant, looks like
        https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHLqe2Pdrma&_g_=g
    """
    print(f"Fetching personal link for {study_identifier}... ")
    endpoint = f"{QUALTRICS_BASE_URL}/distributions/{distribution_id}/links"
    parameters = {
        "surveyId": str(qualtrics_survey_id)
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
        personal_link = [item["link"] for item in data["result"]["elements"] if ("externalDataReference" in item) and (item["externalDataReference"] == study_identifier)][0]        
        return personal_link

    except requests.exceptions.RequestException as exc:
        raise QualtricsAPIError(
            f"Error while fetching personal link of individual {study_identifier}."
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QualtricsAPIError(
            f"Unexpected response format when fetching personal link of individual {study_identifier}."
        ) from exc    

def add_individuals_to_survey(new_subject_ids: list, ldot_study_id: str, id_deelnemer_entity: str, embedded_data_field: str, distribution_id: str, qualtrics_survey_id: str, mailing_list_id: str, directory_id: str):
    def convert_api_subject_id_to_study_identifier(api_subject_id):
        """Convert subject ID used by the Ldot API to study identifier that can be used in Qualtrics surveys"""

        response = logged_request(
            "POST",
            "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token",
            function_name="convert_api_subject_id_to_study_identifier",
            service="Ldot",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            },
            raise_for_status=True,
        )
        token = response.json()["access_token"]
        headers={"accept": "application/json",
                "Authorization": f"Bearer {token}"
                }

        response = logged_request(
            "GET",
            f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{ldot_study_id}/Entity/{id_deelnemer_entity}",
            function_name="convert_api_subject_id_to_study_identifier",
            service="Ldot",
            headers=headers,
            raise_for_status=True,
        )
        
        subject_ids = response.json().get("Data", {}).get("SubjectIds")
        guid_to_registration_id = {subject["Guid"]: subject["RegistrationId"] for subject in subject_ids if "Guid" in subject and "RegistrationId" in subject}

        study_identifier = guid_to_registration_id.get(api_subject_id)
        return study_identifier


    participant_to_link_dict = {}
    for subject_id in new_subject_ids:
        study_identifier = convert_api_subject_id_to_study_identifier(subject_id)
        print(f"Processing subject ID: {subject_id} (Study Identifier: {study_identifier})")

        contact_exists = check_contact_in_mailing_list(study_identifier, mailing_list_id, directory_id)

        if not contact_exists:
            print(f"Adding participant study ID {study_identifier} to mailing list...")
            add_contact_to_mailing_list(study_identifier, embedded_data_field, mailing_list_id, directory_id)
        else:
            print(f"Participant study ID {study_identifier} already exists in this mailing list")

        personal_link = get_personal_link(qualtrics_survey_id, distribution_id, study_identifier)

        participant_to_link_dict[subject_id] = personal_link

    return participant_to_link_dict

if __name__ == "__main__":
    # # Example usage
    participant_study_id = ["a92ff326-ba91-46ed-9cfc-cfcdb71f2817"]
    ldot_study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    id_deelnemer_entity = "7f61b810-00ed-1d41-8a33-4164f25ebad0"
    embedded_data_field = "study_id_child"
    qualtrics_survey_id="SV_efCMOg6wHU0T8ii"
    mailing_list_id="CG_2dMbO6WUBMnCeIK"
    distribution_id="EMD_7AEa416lRwFhrkF"
    directory_id="POOL_10pyxk9leSUisrT"

    link = add_individuals_to_survey(participant_study_id, ldot_study_id, id_deelnemer_entity, embedded_data_field, distribution_id, qualtrics_survey_id, mailing_list_id, directory_id)

    print(link)


    # print(get_mailing_list_id_of_distribution("SV_efCMOg6wHU0T8ii",  "EMD_SZFeoK7LAJBHU4d"))
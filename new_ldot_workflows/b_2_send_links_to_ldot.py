import json
import requests

from new_ldot_workflows.logging_utils import logged_request

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]


def send_links_to_ldot(ldot_study_id: str, id_deelnemer_entity: str, id_location: str, custom_var_qualtrics_link: str, link_completed_eaid: str, subject_id_to_link_dict: dict) -> list:
    """Post the Qualtrics links back to Ldot for new subjects"""

    response = logged_request(
        "POST",
        "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token",
        function_name="send_links_to_ldot",
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

    for subject_id, link in subject_id_to_link_dict.items():

        # Populate the Qualtrics link in Ldot for the subject
        response = logged_request(
            "POST",
            f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{ldot_study_id}/Subject/",
            function_name="send_links_to_ldot",
            service="Ldot",
            headers=headers,
            json = {
                "subjectGuid": subject_id,
                "entityId": id_deelnemer_entity,
                "locationSubjectId": id_location,
                custom_var_qualtrics_link: link, # Custom var that corresponds to the Qualtrics link in Ldot
                "doOverwriteNulls": False,
            },
            raise_for_status=True,
        )

        # Add Qualtrics survey link completed event action for the subject
        response = logged_request(
            "POST",
            f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{ldot_study_id}/Action/{link_completed_eaid}/",
            function_name="send_links_to_ldot",
            service="Ldot",
            headers=headers,
            params = {
                "subjectGuid": subject_id,
            },
            raise_for_status=True,
        )

        response_data = response.json()
        print(f"Successfully sent link for subject {subject_id} to Ldot. Response: {response_data}")


if __name__ == "__main__":
    ldot_study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    id_deelnemer_entity = "7f61b810-00ed-1d41-8a33-4164f25ebad0"
    id_location = "427f304f-9d95-44f5-8f7b-d6a1ce1db293"
    subject_id_to_link_dict = {'a92ff326-ba91-46ed-9cfc-cfcdb71f2817': 'https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHL=gl&Q_DL=EMD_7AEa416lRwFhrkF_efCMOg6wHU0T8ii_CGC_9bNzmVXkZpdfEQ9&_g_=g'}
    custom_var_qualtrics_link = "customVar01"
    link_completed_eaid = "31599192-8e9b-4341-b7f4-8b8967dd846a"

    send_links_to_ldot(ldot_study_id, id_deelnemer_entity, id_location, custom_var_qualtrics_link, link_completed_eaid, subject_id_to_link_dict)
import json
import requests

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]


def send_links_to_ldot(ldot_study_id: str, id_deelnemer_entity: str, id_location: str, custom_var_qualtrics_link: str, subject_id_to_link_dict: dict) -> list:
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

    for subject_id, link in subject_id_to_link_dict.items():
        response = requests.post(
            f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{ldot_study_id}/Subject/",
            headers=headers,
            json = {
                "subjectGuid": subject_id,
                "entityId": id_deelnemer_entity,
                "locationSubjectId": id_location,
                custom_var_qualtrics_link: link, # Custom var that corresponds to the Qualtrics link in Ldot
                "doOverwriteNulls": False,
            }
        )


if __name__ == "__main__":
    ldot_study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    id_deelnemer_entity = "7f61b810-00ed-1d41-8a33-4164f25ebad0"
    id_location = "427f304f-9d95-44f5-8f7b-d6a1ce1db293"
    subject_id_to_link_dict = {'352fb9d8-962f-4735-9fc7-7b4e18109a51': 'https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHL=gl&Q_DL=EMD_7AEa416lRwFhrkF_efCMOg6wHU0T8ii_CGC_4WW2MwOaEB01XsM&_g_=g'}
    custom_var_qualtrics_link = "customVar01"

    send_links_to_ldot(ldot_study_id, id_deelnemer_entity, id_location, custom_var_qualtrics_link, subject_id_to_link_dict)
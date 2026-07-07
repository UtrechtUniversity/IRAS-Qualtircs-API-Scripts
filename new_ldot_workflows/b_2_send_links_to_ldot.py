
# {'11111TEST11111': 'https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHL=gl&Q_DL=EMD_7AEa416lRwFhrkF_efCMOg6wHU0T8ii_CGC_CJK3jAlcohFgRMS&_g_=g', '22222TEST22222': 'https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHL=gl&Q_DL=EMD_7AEa416lRwFhrkF_efCMOg6wHU0T8ii_CGC_M6crsA37s6sSOeE&_g_=g'}

import json
import requests

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]


#### I then need to flip it to the next status

def send_links_to_ldot(study_id: str, eaid_deelnemer_entity, subject_id_to_link_dict: dict) -> list:
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

    subject_alias = "a5335cfd-b96a-4c08-b860-700cc4867ec3"
    response = requests.post(
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Subject/VerifySubject",
        headers=headers
    )

    response.raise_for_status()
    payload = response.json()
    print(payload)
    # study_event_actions = payload.get("Data", {}).get("StudyEventActions", [])
    # return [
    #     action["SubjectGuid"]
    #     for action in study_event_actions
    #     if action.get("SubjectGuid")
    # ]

if __name__ == "__main__":
    study_id = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"
    subject_id_to_link_dict = {'352fb9d8-962f-4735-9fc7-7b4e18109a51': 'https://survey.uu.nl/jfe/form/SV_efCMOg6wHU0T8ii?Q_CHL=gl&Q_DL=EMD_7AEa416lRwFhrkF_efCMOg6wHU0T8ii_CGC_4WW2MwOaEB01XsM&_g_=g'}

    send_links_to_ldot(study_id, subject_id_to_link_dict)
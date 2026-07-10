import json
from urllib import response
import requests

from new_ldot_workflows.logging_utils import logged_request

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]

def get_new_subjects(study_id: str, link_creation_eaid: str) -> list:
    """Get subjects that have not yet been added to Qualtrics by checking their event actions"""

    response = logged_request(
        "POST",
        "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token",
        function_name="get_new_subjects",
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
        "POST",
        f"https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/{study_id}/Subject/VerifySubject",
        function_name="get_new_subjects",
        service="Ldot",
        json={"alias": "", "regID": "DEE5"},
        headers=headers,
        raise_for_status=True,
    )
    payload = response.json()

    print(response.status_code)
    print(response.text)
    print(payload)


if __name__ == "__main__":
    print(get_new_subjects("5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b", "5d31129c-d814-5d4b-a96f-048cadc150ce"))

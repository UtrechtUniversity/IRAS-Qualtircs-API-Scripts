
# 1. First, query Ldot to find new people who need to be added to Qualtrics. This will be done by looking for people who have been added to Ldot in the last 24 hours and checking if they are already in Qualtrics.
# 2. For each new person, add them to the appropriate mailing list in Qualtrics. This will involve using the Qualtrics API to add the person's information to the mailing list.
# 3. After adding the person to the mailing list, send them an email invitation to

# Grab the client ID and secret from the config file new_ldot_workflows\ldot_config.json



import json
import requests

with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
LDOT_API_URL = config["LDOT_API_URL"]


response = requests.post(
    "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
)

token = response.json()["access_token"]
print(token)

headers={"accept": "application/json",
        "Authorization": f"Bearer {token}"
         }

response = requests.get(
    "https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b/Action",
    headers=headers
)

print(response.status_code)
print(response.text)




# Assuming the response contains a list of participants under the key 'participants'




# Client ID for the PIAMA study: piama_api_qualtrics
# Study GUID:  5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b


# 
# 1. First, query Ldot to find new people who need to be added to Qualtrics. This will be done by looking for people who have been added to Ldot in the last 24 hours and checking if they are already in Qualtrics.
# 2. For each new person, add them to the appropriate mailing list in Qualtrics. This will involve using the Qualtrics API to add the person's information to the mailing list.
# 3. After adding the person to the mailing list, send them an email invitation to



# I think it would be nice to make this a little app on openshift
# So let's make everything into sepaate functions and then connect them to buttons in the UI. We can use Flask for the backend and React for the frontend..
# And yes save the reuslts in the meantime

import requests

# I think I ned to get the list of people and their IDs where they are at the state of point where they're ready to be sent a survey invitation


LDOT_API_URL = "https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1/"
STUDY_GUID = "5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b"

study_events_url = f"{LDOT_API_URL}{STUDY_GUID}/Action"

headers={"accept": "application/json"
         }

response = requests.get(
    study_events_url,
    auth=(),
    headers=headers
)

print(response.status_code)
print(response.text)




# Assuming the response contains a list of participants under the key 'participants'




# Client ID for the PIAMA study: piama_api_qualtrics
# Study GUID:  5c9c6a47-c8d7-8142-a8c8-ccdcb8a8044b


# 
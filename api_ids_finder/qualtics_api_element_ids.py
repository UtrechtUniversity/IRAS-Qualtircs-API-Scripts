import requests
from dotenv import dotenv_values

###### Set up the Qualtrics API base URL and headers

LDOT_API_URL = "https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1"
LDOT_TOKEN_URL = (
    "https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token"
)
QUALTRICS_BASE_URL = "https://fra1.qualtrics.com/API/v3"

study_env_path = "app-secrets/piama-sandbox.env"
study_env = dotenv_values(study_env_path)


#### Requests to get the IDs for the Qualtrics survey elements (questions, blocks, etc.) for a given survey ID.
#### SurveyID can be found without in the API, in the URL of the survey. Always looks like SV_9vJRRiJUI1QKmzA.

# Make a global variable for the headers and the survey ID to be used in the functions below. The survey ID can be changed to any other survey ID as needed.
HEADERS = {
    "Content-Type": "application/json",
    "X-API-TOKEN": study_env.get("QUALTRICS_API_TOKEN"),


}# Replace with your survey ID
# SURVEY_ID = "SV_40id5EiKiNtjob4"   # Survey 1
SURVEY_ID = "SV_9vJRRiJUI1QKmzA"  # Survey 2

############

def get_directory_id() -> str:
    """Get the directory ID for a Qualtrics account, there should just be one """
    print("Getting directory ID... ")
    endpoint = f"{QUALTRICS_BASE_URL}/directories"
    parameters = {
        "includeCount": False
    }
    try:
        response = requests.get(endpoint, headers=HEADERS, params=parameters)
        response.raise_for_status()
        data = response.json()
        directory_id = data["result"]["elements"][0]["directoryId"]
        return f"These are the directory IDs for the account: {directory_id}"

    except Exception as e:
        return f"Error: Unable to retrieve directory ID, status code: {response.status_code}, message: {response.text}, exception: {str(e)}"


def get_distributions(survey_id):
    endpoint = f"{QUALTRICS_BASE_URL}/distributions"
    parameters = {
        "surveyId": survey_id,
        "requestType": "GeneratedInvite"
    }

    response = requests.get(endpoint, headers=HEADERS, params=parameters)

    if response.status_code == 200:
        result = response.json()["result"]["elements"]
        distribution_ids = [f'Distribution {dist["id"]} -- created: {dist["createdDate"]}' for dist in result]
        return distribution_ids

    else:
        return f"Error: Unable to retrieve distributions, status code: {response.status_code}, message: {response.text}"



def get_mailing_list_id_of_distribution(survey_id: str, distribution_id: str) -> str:
    """Get the mailing list IDs connected to a distribution"""
    print("Finding mailing list ID of distribution... ")

    endpoint = f"{QUALTRICS_BASE_URL}/distributions/{distribution_id}"
    parameters = {
        "surveyId": survey_id
    }
    try:
        response = requests.get(endpoint, headers=HEADERS, params=parameters)
        response.raise_for_status()
        mailing_list_id =  response.json()["result"]["recipients"]["mailingListId"]
        
        return mailing_list_id

    except Exception as e:
        return f"Error: Unable to retrieve mailing list ID of distribution, status code: {response.status_code}, message: {response.text}, exception: {str(e)}"


if __name__ == "__main__":
    ### First get the directory ID ###
    
    # directory_id = get_directory_id()
    # print(directory_id)

    ## Then get the distributions for the survey ID ###
    # distributions = get_distributions(SURVEY_ID)
    # print(distributions)


    # ### Then get the mailing list IDs for a chosen distribution ###
    # distribution_id = "EMD_RvVZlgVuUDc6cGs"  # Replace with the desired distribution ID

    # mailing_list_id = get_mailing_list_id_of_distribution(SURVEY_ID, distribution_id)
    # print(mailing_list_id)


    pass
import requests
from datetime import datetime, timedelta
from loadenv import loadenv



load_dotenv()

study_env_path = (
    CONFIG_PATH.parent / "app-secrets" / study_variables.config_path
).resolve()


def get_distributions(survey_id):
    endpoint = f"{QUALTRICS_BASE_URL}/distributions"
    parameters = {
        "surveyId": survey_id,
        "distributionRequestType": "GeneratedInvite"
    }

    response = requests.get(endpoint, headers=HEADERS, params=parameters)

    if response.status_code == 200:
        result = response.json()["result"]["elements"]
        distribution_ids = [f'{dist["id"]} created: {dist["createdDate"]}' for dist in result]
        return distribution_ids

    else:
        print(f"Error in get_distributions_of_survey: {response.text}")
        return None
    
if __name__ == "__main__":
    result = get_distributions("SV_9vJRRiJUI1QKmzA")
    for res in result:
        print(res)


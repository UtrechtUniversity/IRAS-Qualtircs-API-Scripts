import requests
from qualtrics_settings import BASE_URL, HEADERS, SURVEYIDS

def get_distributions(survey_id):
    endpoint = f"{BASE_URL}/distributions"
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
    # Example usage
    survey_id = SURVEYIDS.my_test_survey_id
    result = get_distributions(survey_id)
    for res in result:
        print(res)


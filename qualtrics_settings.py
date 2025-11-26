"""
Qualtrics API settings

Change X-API-TOKEN. You can request it on your account under Account Settings.
Add your survey IDs to the SURVEYIDS class. You can find it in the URL when you open your survey. It always starts with "SV_".
"""

BASE_URL = "https://fra1.qualtrics.com/API/v3"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-TOKEN": "<API TOKEN>" # Replace with your actual API token
    }

class QualtricsAPIError(Exception):
    pass

class SURVEYIDS():
    my_test_survey_id = "SV_0llWVSZNOQOorSC"
    your_survey_id_here = "<SV_YOUR_SURVEY_ID>"  # Replace with your actual survey ID
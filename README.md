# Ldot ↔ Qualtrics API Connection

## Purpose
This application serves as a bridge between the Ldot system and the Qualtrics API, enabling seamless integration and data exchange between the two platforms.

It can automate several types of steps that have previous been done manually:
* Check the status of a subject in Ldot, and if they are eligible for a survey, create a personal survey link in Qualtrics and populate it back into Ldot.
* Check the progress of a subject's survey completion in Qualtrics, and update the subject's status in Ldot if the survey is completed.

Thanks to the modular design of the application, a Ldot study can be set up to integrate with any number of Qualtrics surveys. In addition, the application is designed to be easily extensible, allowing for the addition of new workflows and integrations in the future.


## Usage
Access to the application is only available within the Utrecht University network. Enter via the following URL:

https://iras-ldot-qualtrics-connection-dgk-prd-ldot-qualtrics.apps.cl01.cp.its.uu.nl/


## Setup
There is some setup required to configure a new Ldot study in the application. This includes setting up the study in Ldot itself, creating the survey correctly in Qualtrics, and populating the configuration file with the required variables.

### New study
Studies are built in Ldot by the Ldot team, after extensive discussions with the data management team about the study flow. Once a study is built, it can be configured in the application by adding a new entry to the study_config.yaml file.

### New survey
Surveys are built in Qualtrics by the data management team. The survey must be built in a specific way to ensure that the application can create personal survey links and track survey completion correctly. There are two key requirements for the survey:

1. Embedded data field for subject ID
The survey must have an 'embedded data field'. It is the field that will be used to store the subject's unique study ID. In order to both preserve privacy and enable linking of survey results, this field is piped as an Embedded Data question into the survey flow.

When creating a new survey, the data management team should create a dummy Excel file. It should have the required columns for a survey subject, including a column for this embedded data field. The column can be given any name, such as 'participant_unique_ID', 'Ldot_study_ID', or 'RESPNRK'. 

The name of the column used as the embedded data field is needed for the configuration file.

2. Create a personal links distribution with an distant expiration date
The study builder should create a mailing list in Qualtrics using the dummy excel, and specify the column that should be the embedded data field. Then, they should create an initial *Personal links* distribution in the survey.

It's important that the distribution is set to expire at a distant date. This ensures that the personal links created by the application will remain valid for the duration of the study. 



Since the application itself can't do these steps, this initial setup is required to ensure that the survey is configured correctly.


### New work unit



### Setting up the configuration file

### API Environment
Access to the Qualtrics API requires an API token, and access to the Ldot API requires a client ID and password.

These credentials are stored in a .env file, which is not included in the repository for security reasons. The .env files are in the app-secrets directory of the application, and contain the following variables:

LDOT_client_id
LDOT_client_secret
QUALTRICS_API_TOKEN

Since different Ldot projects may have different API credentials, the study_config.yaml file should be configured to point to the correct .env file for each study. This is done by specifying the path to the .env file in the study configuration.

If a new study is added to the application, the data management team should create a new .env file with the correct credentials for that study for both Qualtrics and Ldot, and update the study_config.yaml file to point to the new .env file.





## For developers

### Setting up a new work unit type

The 

Each workflow is implemented as a separate handler function, which can be easily added or modified without affecting the core functionality of the application.

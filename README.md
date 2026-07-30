# Ldot ↔ Qualtrics API Connection

## Purpose
This application serves as a bridge between the Ldot system and the Qualtrics API, enabling seamless integration and data exchange between the two platforms.

It can automate several types of steps that have previous been done manually:
* Check the status of a subject in Ldot, and if they are eligible for a survey, create a personal survey link in Qualtrics and populate it back into Ldot.
* Check the progress of a subject's survey completion in Qualtrics, and update the subject's status in Ldot if the survey is completed.

Thanks to the modular design of the application, a Ldot study can be set up to integrate with any number of Qualtrics surveys. In addition, the application is designed to be easily extensible, allowing for the addition of new workflows and integrations in the future.


## Access
Access to the application is only available within the Utrecht University network. Enter via the following URL:

https://iras-ldot-qualtrics-connection-dgk-prd-ldot-qualtrics.apps.cl01.cp.its.uu.nl/


## Setup
There is some setup required to configure a new Ldot study in the application. This includes setting up the study in Ldot itself, creating the survey correctly in Qualtrics, and populating the configuration file with the required variables.

The overall setup process culminates in the creation of a new entry in the study_config.yaml file. This is used by the application to configure the study and its associated workflows.

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




### Setting up the configuration file
After the study is built in Ldot and the survey is built in Qualtrics, the data management team should create a new entry in the study_config.yaml file. 

((( )))

#### Set up study variables
The study variables section of the configuration file should be populated with the required variables for the study.

* study_id: The unique identifier for the study in Ldot, just continue the current numbering sequence (LDOT-003, etc.).
* name: The name of the study for the drop-down menu.
* Ldot variables
    * ldot_study_id: The API identifier for the study in Ldot
    * id_deelnemer_entity: Entity ID for the participant entity in the study
    * id_location: Entity ID for the study location in the study


#### Work unit configuration

A study is made up of one or more work units. Each work unit is a specific step in the study flow, and can be configured to run a specific workflow. The application is designed to be modular, allowing for the addition of new workflows as needed.

Currently, there are two types of work units that can be configured:

* Create Qualtrics survey link
* Check Qualtrics survey progress

When a new work unit is added to a study, the data management team should specify the type of work unit in the study_config.yaml file. The application will then use the appropriate handler function to execute the workflow for that work unit.

A work unit is configured with the following variables:
* name: The name of the work unit
* type: From the types listed above, this specifies the workflow that will be executed for this work unit.
* trigger
* resolution



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

## Questions
If you have any questions about the application, please contact the data management team at the following email address:

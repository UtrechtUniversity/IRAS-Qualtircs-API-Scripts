# Ldot ↔ Qualtrics API Connection

Purpose

This application acts as a bridge between the Ldot system and the Qualtrics API, enabling automated data exchange between the two platforms.

It automates several tasks that were previously performed manually:

* Check a subject's status in Ldot and, if the subject is eligible for a survey, create a personal survey link in Qualtrics and save the link back to Ldot.
* Check a subject's survey progress in Qualtrics and update the subject's status in Ldot when the survey has been completed.

The application's modular design allows an Ldot study to integrate with any number of Qualtrics surveys. It is also designed to be extensible, allowing additional workflows and integrations to be added in the future.

## Access

Access to the application is only available within the Utrecht University network. Enter via the following URL:

https://iras-ldot-qualtrics-connection-dgk-prd-ldot-qualtrics.apps.cl01.cp.its.uu.nl/

## Setup for new studies

There is some setup required to configure a new Ldot study in the application. This includes setting up the study in Ldot itself, creating the survey correctly in Qualtrics, and populating the configuration file with the required variables.

1. Creating the study in Ldot.
2. Creating and configuring the required survey in Qualtrics.
3. Adding the study configuration to study_config.yaml.
4. Creating an environment file containing the required API credentials.

The setup process is completed by adding a new study entry to study_config.yaml. The application uses this configuration to identify the study and run its associated workflows.

These setup steps only need to be completed once for each new study.

### Build a new Qualtrics study

Ldot studies are created by the Ldot team following discussions with the data management team about the study flow. After the study has been created, it can be added to the application by creating a new entry in study_config.yaml.

### Build a new survey

Surveys are built in Qualtrics by the data management team. The survey must be built in a specific way to ensure that the application can create personal survey links and track survey completion correctly.

The following requirements must be met.

1. Embedded data field for subject ID

The survey must have an 'embedded data field'. It is the field that will be used to store the subject's unique study ID. In order to both preserve privacy and enable linking of survey results, this field is piped as an Embedded Data question into the survey flow.

When creating a new survey, the data management team should create a dummy Excel file. It should contain a column for the subject's unique study ID.  The column can be given any name, such as 'participant_unique_ID', 'Ldot_study_ID', or 'RESPNRK'. 

The name of the column used as the embedded data field is needed for the study configuration.

2. Create a personal links distribution with an distant expiration date

The study builder should create a Qualtrics mailing list using the dummy Excel file and configure the subject ID column as an embedded data field.

The study builder should create a mailing list in Qualtrics using the dummy excel, and specify the column that should be the embedded data field. Next, they should create an initial Personal Links distribution for the survey.

The distribution should have an expiration date sufficiently far in the future to cover the expected duration of the study. This ensures that the personal survey links created by the application remain valid throughout the study. 

Since the application itself can't do these steps, this initial setup is required to ensure that the survey is configured correctly.

### Set up the configuration file

After the study is built in Ldot and the survey is built in Qualtrics, the data management team should create a new entry in the study_config.yaml file. 

Some of the required identifiers can only be obtained through the Ldot and Qualtrics APIs. The api_ids_finder directory contains two scripts that can be used to find these identifiers.

Example study configurations are included in study_config.yaml. You can copy an existing example as a starting point.

The application also validates the study configuration when it starts. If the configuration is invalid, the application will not start.

#### Enter study variables

Populate the study variables section with the following values:

* study_id: The unique identifier used for the study in this application. Continue the existing numbering sequence, for example, LDOT-003.
* name: The study name displayed in the application's drop-down menu. This is usually the same as the study name in Ldot.
* Ldot variables
    - ldot_study_id: The API identifier for the study in Ldot.
    - id_deelnemer_entity: The entity ID for the participant entity type in the study.
    - id_location: The entity ID for the study location.

#### Add work-unit variables

A study consists of one or more work units. Each work unit represents a specific step in the study flow and is configured to run a particular work action.

A work unit begins with a trigger event in Ldot and ends with a resolution event in Ldot. The work action defines the processing performed between these two events.

Each work unit contains the following variables:

* work_unit_id: A unique identifier for the work unit. Continue the existing numbering sequence, for example, unit-1.
* name: The name of the work unit.
* trigger: The EAID (Event Action ID) of the Ldot event that triggers the work action for a subject. For example, this could be the event indicating that a subject is ready to receive a survey link.
* work_action: The workflow that is executed for each subject when the work unit is triggered.
* resolution: The EAID of the Ldot event that is triggered when the work action has been completed. For example, this could be the event indicating that a subject has completed a survey.

#### Enter work action variables

The application currently supports two work-action types:

* Create Qualtrics survey link
* Check Qualtrics survey progress

Each work action requires the following top-level configuration items:

* type: One of the supported work-action types. Ensure that the spelling and capitalization exactly match the expected value.
* variables: A flexible set of variables required by the selected work-action type.

The required variables differ between work-action types. Refer to the example studies in study_config.yaml for the required configuration of each type.

### API Environment

Access to the Qualtrics API requires an API token. Access to the Ldot API requires a client ID and client secret.

These credentials are stored in .env files, which are not included in the repository for security reasons. The environment files are stored in the application's app-secrets directory and contain the following variables:

LDOT_client_id  
LDOT_client_secret  
QUALTRICS_API_TOKEN

Different Ldot studies may use different API credentials. Therefore, each study configuration in study_config.yaml must specify the name of correct .env file.

If a new study is added to the application, the data management team should create a new .env file with the correct credentials for that study for both Qualtrics and Ldot, and update the study_config.yaml file to point to the new .env file.

## For developers

### Setting up a new work unit type

As explained above, there are currently two work action types available, but more can be configued. Work-units are abstracted, meaning that they always begin with a trigger and end with a resolution in Ldot, but the work action performed in the middle can vary. The config file flexibilty accepts any variables that may be required for this work action.

If you choose to implement a new work action, you will need to make a few additions.

1. In load_studies_config, create a class for the new work-action type.
2. Create a class containing the variables required by the new work action.
3. Add field validators for the new configuration values.
4. Add the new work-action class to the union used by the WorkAction class.
5. In the new_ldot_workflows directory, create a new Python file containing the handler for the work action.
6. In the handler, define:

   * A handler function.
   * A unique workflow class containing a run() method.
7. Implement the required workflow steps in the run() method.
8. In app.py, import the new handler and add it to the WORK_UNIT_HANDLERS dictionary.

The easiest way to create a new work-action type is to copy create_qualtrics_survey_link_handler.py and modify it for the new workflow.



## For developers

## Contact

For questions please contact:

Carmel Suchard, IRAS Data Management

o.suchard@uu.nl

Or open an issue.
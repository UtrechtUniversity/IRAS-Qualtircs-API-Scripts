## Instructions
The functions in this repository are wrappers for survey management tasks that require multiple Qualtics API calls. The tasks are: adding a person to a survey, and getting a person's survey progress.

### Setup
Before you can use the functions, you need to:

* Create a virtual environment, and pip install the requirements.txt

* Input your Qualtrics API token in qualtrics_settings.py. You can get it by going to Qualtics --> click on your username --> Account settings

* Add a survey ID in qualtrics_settings.py. It can be found in the URL of your survey, starting with the letters SV. You can add multiple survey IDs to qualtrics_settings.py, and you can name them whatever you want. You can use the Survey ID without adding it to the settings, but makes it easy to refer to different surveys when running the functions.
<img width="302" height="37" alt="image" src="https://github.com/user-attachments/assets/be89e2ed-afec-426a-8482-1c43ba961fb0" />

* Manually add some contacts to the survey. The functions assume that the contacts are set up in a cetain way, where the ExternalDataReference = another field, which has been turned into an embedded field. It's only possible to set it up manually the first time. If they survey is new, add some respondents from a CSV first before using the functions.

### Adding someone to a survey

**Step 1: Find DistributionID**

Your survey may contain multiple Personal Links distributions. A distributions is the channel by which a survey is sent out to respondents.  You must find the DistributionID of the one that you want to add a person to. You can use the function **get _distributions()**. In the first parameter, fill in the SurveyID of your Survey.

The DistributionID always starts with EMD_. In the example, the survey has two distributions, which I can see on Qualtrics. Run the function to get the DistributionID and date created of each one, so you can compare creation dates and choose the one you want. In this case, you want test_contact_list. Copy the DistributionID.

<img width="391.3" height="211.9" alt="519083748-c94e87cd-0e83-4479-951f-4e8b7dd581b9" src="https://github.com/user-attachments/assets/acee553b-9005-44fc-b1fb-cd5ce22480b4" />
<img width="555" height="59" alt="image" src="https://github.com/user-attachments/assets/651de9d5-65fd-49cb-aced-37312548a45d" />
<br/><br/>

**Step 2: Add an individual to a Survey**

You add a new individual to a survey by adding them to a distribution. A distribution is always linked to exactly one mailing list. Therefore, you must add this individual to the mailing list.

Use the function **add_individual_to_survey()**. The first argument is the person’s Study ID, which is internal to the given study. The second argument is the Qualtrics ID of the survey. The third is the distribution_id found in step 1.

The function adds this individual’s Study ID to the right mailing list, which in turn adds it to the distribution. If the Study Id already exists in this mailing list, it won’t be added again and you’ll get a warning.

The individual’s Personal Link to the survey is printed.

### Getting someone's progress on a survey ###

Use the **get_individual_progress()** function. The first argument is the individual’s Study ID. The second is the field being used as the Emebedded Data Field (for example, "study_id_child"). The third is the ID of the survey. 

The function works by requesting 2 exports from Qualtrics (one for completed, one for in-progress responses), waiting for them, downloading them, and then filtering for the person's ID. If we wanted to get multiple individuals’ progress at once, the function could be modified to filter for multiple study IDs.

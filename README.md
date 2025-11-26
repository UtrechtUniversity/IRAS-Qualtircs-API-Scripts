Setup
* Create a virtual environment with pip install -r requirements.txt


Adding an individual to a survey
1.	Find DistributionID
Your survey may contain multiple Personal Links distributions. A distributions is the channel by which a survey is sent out to respondents.  You must find the DistributionID of the one that you want to add a person to. You can use the function get _distributions(). In the parameter, fill in the SurveyID of your Survey.
The DistributionID always starts with EMD_. In my example, my survey has two distributions. I run the function to get the DistributionID and date created of each one, so I can easily choose the one I want. In this case, I want test_contact_list.
<img width="602" height="326" alt="image" src="https://github.com/user-attachments/assets/c94e87cd-0e83-4479-951f-4e8b7dd581b9" />
<img width="555" height="59" alt="image" src="https://github.com/user-attachments/assets/651de9d5-65fd-49cb-aced-37312548a45d" />


2.	Add an individual to a Survey
You add a new individual to a survey by adding them to a distribution. A distribution is always linked to exactly one mailing list. Therefore, you must add this individual to the mailing list.
Use the function add_individual_to_survey(). The first argument is the person’s Study ID, which is internal to the study at hand. The second argument is the ID of the survey. The third is the distribution_id found in step 1.
The function adds this individual’s Study ID to the right mailing list, which in turn adds it to the distribution. If the Study Id already exists in this mailing list, it won’t be added again and you’ll get a warning.
The individual’s Personal Link to the survey is printed.
Getting an individual’s progress on a survey
Use the get_individual_progress() function. The first argument is the individual’s Study ID. The second is the field being used as the Emebedded Data Field. The third is the ID of the survey. 
Remember that it can take Qualtics ~5 minutes 
The function works by requesting an export from Qualtrics, waiting for it, downloading it, and then filtering for the person. If we wanted to get multiple individuals’ progress at once, the function could be modified to filter for multiple study IDs.







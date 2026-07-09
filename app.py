from pathlib import Path

from flask import Flask, json, render_template, request, jsonify
import requests
import yaml

from new_ldot_workflows.b_1_get_new_subjects import get_new_subjects
from new_ldot_workflows.b_2_get_qualtrics_links import add_individuals_to_survey
from new_ldot_workflows.b_2_send_links_to_ldot import send_links_to_ldot
from new_ldot_workflows.b_3_get_incomplete_subjects import get_incomplete_subjects
# from new_ldot_workflows.b_4_get_individual_progress import get_individual_progress

app = Flask(__name__)

CONFIG_PATH = Path(__file__).resolve().with_name("study_configs.yaml")
STUDIES = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

def get_study_settings(study_key: str):
    study = STUDIES.get(study_key)
    if not study:
        return None, None, None

    return study, study.get("ldot_variables", {}), study.get("qualtrics_variables", {})

@app.route("/")
def index():
    return render_template("index.html", studies=STUDIES)


@app.route("/api/button1", methods=["POST"])
def button1():
    """Get the participants who have not yet been given a survey link and return their subjectIDs"""
    
    data = request.json
    study_id = data.get("study_id")
    print(f"Received study_id: {study_id}")

    study, ldot_vars, qualtrics_vars = get_study_settings(study_id)
    if not study:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    ldot_study_id = ldot_vars.get("ldot_study_id")
    link_creation_eaid = ldot_vars.get("eaid_qualtrics_survey_link_creation_to_do_date")

    new_subjects_ids = get_new_subjects(ldot_study_id, link_creation_eaid)

    message = f"Found {len(new_subjects_ids)} new subjects in this study"
    return jsonify({"success": True, "message": message, "new_subject_ids": new_subjects_ids})



@app.route("/api/button2", methods=["POST"])
def button2():
    """Uses subjectIDs from button 1 to add them to Qualtrics and send the links back to LDOT"""
    data = request.json
    study_id = data.get("study_id")
    new_subject_ids = data.get("new_subject_ids") or data.get("subject_ids")

    if not study_id:
        return jsonify({"success": False, "message": "Missing study_id in request"}), 400

    if not new_subject_ids:
        return jsonify({"success": False, "message": "Missing new_subject_ids in request"}), 400

    # Lookup study variables from STUDIES config
    study, ldot_vars, qualtrics_vars = get_study_settings(study_id)

    ldot_study_id = ldot_vars.get("ldot_study_id")
    id_deelnemer_entity = ldot_vars.get("id_deelnemer_entity")
    id_location = ldot_vars.get("id_location")
    custom_var_qualtrics_link = ldot_vars.get("custom_var_qualtrics_link")
    qualtrics_survey_id = qualtrics_vars.get("survey_id")
    mailing_list_id = qualtrics_vars.get("mailing_list_id")
    embedded_data_field = qualtrics_vars.get("embedded_data_field")
    directory_id = qualtrics_vars.get("directory_id")
    distribution_id = qualtrics_vars.get("distribution_id")

    if not ldot_study_id:
        return jsonify({"success": False, "message": f"Missing ldot_study_id for study_id: {study_id}"}), 400

    debug_inputs = {
        "study_id": study_id,
        "ldot_study_id": ldot_study_id,
        "id_deelnemer_entity": id_deelnemer_entity,
        "id_location": id_location,
        "new_subject_ids": new_subject_ids,
        "qualtrics_survey_id": qualtrics_survey_id,
        "mailing_list_id": mailing_list_id,
        "embedded_data_field": embedded_data_field,
        "directory_id": directory_id,
        "distribution_id": distribution_id
    }

    subject_id_to_link_dict = add_individuals_to_survey(new_subject_ids, ldot_study_id, id_deelnemer_entity, embedded_data_field, distribution_id, qualtrics_survey_id, mailing_list_id, directory_id)
    send_links_to_ldot(ldot_study_id, id_deelnemer_entity, id_location, custom_var_qualtrics_link, subject_id_to_link_dict)

    return jsonify({
        "success": True,
        "message": f"Processed {len(new_subject_ids)} subject IDs",
        "debug_inputs": debug_inputs,
        "subject_id_to_link_dict": subject_id_to_link_dict
    })


@app.route("/api/button3", methods=["POST"])
def button3():
    """Third API call - returns list of subjectIDs"""
    data = request.json
    study_id = data.get("study_id")
    study, ldot_vars, qualtrics_vars = get_study_settings(study_id)

    if not study:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400
    
    ldot_study_id = ldot_vars.get("ldot_study_id")
    eaid_survey_invitation_completed = ldot_vars.get("eaid_survey_invitation_completed")
    eaid_survey_progress_completed = ldot_vars.get("eaid_survey_progress_completed")

    try:
        result = f"Button 3 executed for study {study_id}"
        # Return both message and subject_ids list
        subjects_not_completed_survey = get_incomplete_subjects(ldot_study_id, eaid_survey_invitation_completed, eaid_survey_progress_completed)
        return jsonify({"success": True, "message": result, "subject_ids": subjects_not_completed_survey})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/button4", methods=["POST"])
def button4():
    """Fourth API call - uses subjectIDs from button3"""
    data = request.json
    # study_id = data.get("study_id")
    # subject_ids = data.get("subject_ids")  # List of subjectIDs from button3

    # if not study_id:
    #     return jsonify({"success": False, "message": "Missing study_id in request"}), 400

    # if not subject_ids:
    #     return jsonify({"success": False, "message": "Missing subject_ids in request"}), 400

    # study, vars = get_study_settings(study_id)
    # if not study:
    #     return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    # qualtrics_survey_id = vars.get("qualtrics_survey_id")
    # embedded_data_field = vars.get("embedded_data_field")

    # participant_to_progress_dict = get_individual_progress(subject_ids, embedded_data_field, qualtrics_survey_id)


    # return jsonify({
    #     "success": True,
    #     "message": f"Retrieved progress for {len(participant_to_progress_dict)} subjects",
    #     "study_id": study_id,
    #     "qualtrics_survey_id": qualtrics_survey_id,
    #     "embedded_data_field": embedded_data_field,
    #     "progress_results": participant_to_progress_dict,
    # })


if __name__ == "__main__":
    app.run(debug=True)

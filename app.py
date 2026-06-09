from flask import Flask, json, render_template, request, jsonify
import requests

from new_ldot_workflows.b_1_get_new_subjects import get_new_subjects
from new_ldot_workflows.b_2_get_qualtrics_links import add_individuals_to_survey
from new_ldot_workflows.b_2_send_links_to_ldot import send_links_to_ldot
from new_ldot_workflows.b_4_get_individual_progress import get_individual_progress

app = Flask(__name__)

STUDIES = json.load(open("ldot_study_configs.json"))

@app.route("/")
def index():
    return render_template("index.html", studies=STUDIES)


@app.route("/api/button1", methods=["POST"])
def button1():
    """First API call"""
    data = request.json
    study_id = data.get("study_id")

    # TODO: Replace this with your actual API call that returns subject IDs
    subject_ids = get_new_subjects(study_id)

    message = f"Found {len(subject_ids)} subject IDs for study {study_id}" if study_id else f"Found {len(subject_ids)} subject IDs"
    return jsonify({"success": True, "message": message, "subject_ids": subject_ids})



@app.route("/api/button2", methods=["POST"])
def button2():
    """Second API call - uses subjectIDs from button1"""
    data = request.json
    study_id = data.get("study_id")
    subject_ids = data.get("subject_ids")

    if not study_id:
        return jsonify({"success": False, "message": "Missing study_id in request"}), 400

    if not subject_ids:
        return jsonify({"success": False, "message": "Missing subject_ids in request"}), 400

    # Lookup study variables from STUDIES config
    study = STUDIES.get(study_id)
    if not study:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    vars = study.get("variables", {})
    survey_id = vars.get("survey_id")
    mailing_list_id = vars.get("mailing_list_id")
    embedded_data_field = vars.get("embedded_data_field")
    directory_id = vars.get("directory_id")
    distribution_id = vars.get("distribution_id")
    debug_inputs = {
        "study_id": study_id,
        "subject_ids": subject_ids,
        "survey_id": survey_id,
        "mailing_list_id": mailing_list_id,
        "embedded_data_field": embedded_data_field,
        "directory_id": directory_id,
        "distribution_id": distribution_id
    }

    participant_to_link_dict = add_individuals_to_survey(subject_ids, embedded_data_field, distribution_id, survey_id, mailing_list_id, directory_id)
    send_links_to_ldot(participant_to_link_dict)


    # return jsonify({
    #     "success": True,
    #     "message": "Button 2 inputs resolved successfully",
    #     "debug_inputs": debug_inputs,
    #     "participant_to_link_dict": participant_to_link_dict
    # })


@app.route("/api/button3", methods=["POST"])
def button3():
    """Third API call - returns list of subjectIDs"""
    data = request.json
    study_id = data.get("study_id")
    
    # TODO: Add your API call logic here - should return a list of subjectIDs
    try:
        result = f"Button 3 executed for study {study_id}"
        # Return both message and subject_ids list
        subject_ids = []  # TODO: Fill this with actual subjectIDs from your API call
        return jsonify({"success": True, "message": result, "subject_ids": subject_ids})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/button4", methods=["POST"])
def button4():
    """Fourth API call - uses subjectIDs from button3"""
    data = request.json
    study_id = data.get("study_id")
    subject_ids = data.get("subject_ids")  # List of subjectIDs from button3

    if not study_id:
        return jsonify({"success": False, "message": "Missing study_id in request"}), 400

    if not subject_ids:
        return jsonify({"success": False, "message": "Missing subject_ids in request"}), 400

    study = STUDIES.get(study_id)
    if not study:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    vars = study.get("variables", {})
    survey_id = vars.get("survey_id")
    embedded_data_field = vars.get("embedded_data_field")

    participant_to_progress_dict = get_individual_progress(subject_ids, embedded_data_field, survey_id)


    return jsonify({
        "success": True,
        "message": f"Retrieved progress for {len(participant_to_progress_dict)} subjects",
        "study_id": study_id,
        "survey_id": survey_id,
        "embedded_data_field": embedded_data_field,
        "progress_results": participant_to_progress_dict,
    })


if __name__ == "__main__":
    app.run(debug=True)

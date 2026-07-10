from pathlib import Path

from flask import Flask, json, render_template, request, jsonify
import requests
import yaml
import json

from new_ldot_workflows.ldot_client import LdotClient
from new_ldot_workflows.b_1_get_new_subjects import get_new_subjects
from new_ldot_workflows.b_2_get_qualtrics_links import add_individuals_to_survey
from new_ldot_workflows.b_2_send_links_to_ldot import send_links_to_ldot
from new_ldot_workflows.b_3_get_incomplete_subjects import get_incomplete_subjects
from new_ldot_workflows.b_4_get_individual_progress import get_individual_progress
from new_ldot_workflows.logging_utils import QualtricsAPIError

app = Flask(__name__)


CONFIG_PATH = Path(__file__).resolve().with_name("study_configs.yaml")
STUDIES = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

def get_study_settings(study_key: str):
    study = STUDIES.get(study_key)
    if not study:
        return None, None, None

    return study, study.get("ldot_variables", {}), study.get("qualtrics_variables", {})


with open("new_ldot_workflows/ldot_config.json") as f:
    config = json.load(f)
LDOT_TOKEN_URL = config["LDOT_TOKEN_URL"]
LDOT_API_URL = config["LDOT_API_URL"]
CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]

ldot_client = LdotClient(
    token_url=LDOT_TOKEN_URL,
    api_url=LDOT_API_URL,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

@app.route("/")
def index():
    return render_template("index.html", studies=STUDIES)


@app.route("/api/button1", methods=["POST"])
def button1():
    """Get the participants who have not yet been given a survey link and return their subjectIDs"""
    
    data = request.json
    study_id = data.get("study_id")

    study, ldot_vars, qualtrics_vars = get_study_settings(study_id)
    if not study:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    ldot_study_id = ldot_vars.get("ldot_study_id")
    link_creation_eaid = ldot_vars.get("eaid_qualtrics_survey_link_creation_to_do_date")
    link_completed_eaid = ldot_vars.get("eaid_qualtrics_survey_link_creation_completed")

    try:
        new_subjects_ids = get_new_subjects(ldot_client, ldot_study_id, link_creation_eaid, link_completed_eaid)
    except QualtricsAPIError as e:
        return jsonify({"success": False, "message": str(e)}), 502
    except requests.RequestException as e:
        return jsonify({"success": False, "message": f"Failed to fetch new subjects from Ldot: {e}"}), 502
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"success": False, "message": f"Unexpected Ldot response while fetching new subjects: {e}"}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error in button1: {e}"}), 500

    message = f"Found {len(new_subjects_ids)} new subjects in this study"
    return jsonify({"success": True, "message": message, "new_subject_ids": new_subjects_ids})



@app.route("/api/button2", methods=["POST"])
def button2():
    """Uses subjectIDs from button 1 to add them to Qualtrics and send the links back to Ldot"""
    data = request.json
    study_id = data.get("study_id")
    new_subject_ids = data.get("new_subject_ids") or data.get("subject_ids")

    if not study_id:
        return jsonify({"success": False, "message": "Missing study_id in request"}), 400

    if not new_subject_ids:
        return jsonify({
            "success": True,
            "message": f"No new subjects to process",
        })

    # Lookup study variables from STUDIES config
    study, ldot_vars, qualtrics_vars = get_study_settings(study_id)

    ldot_study_id = ldot_vars.get("ldot_study_id")
    id_deelnemer_entity = ldot_vars.get("id_deelnemer_entity")
    id_location = ldot_vars.get("id_location")
    custom_var_qualtrics_link = ldot_vars.get("custom_var_qualtrics_link")
    link_completed_eaid = ldot_vars.get("eaid_qualtrics_survey_link_creation_completed")

    qualtrics_survey_id = qualtrics_vars.get("survey_id")
    mailing_list_id = qualtrics_vars.get("mailing_list_id")
    embedded_data_field = qualtrics_vars.get("embedded_data_field")
    directory_id = qualtrics_vars.get("directory_id")
    distribution_id = qualtrics_vars.get("distribution_id")

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

    try:
        subject_id_to_link_dict = add_individuals_to_survey(ldot_client, new_subject_ids, ldot_study_id, id_deelnemer_entity, embedded_data_field, distribution_id, qualtrics_survey_id, mailing_list_id, directory_id)
        send_links_to_ldot(ldot_client, ldot_study_id, id_deelnemer_entity, id_location, custom_var_qualtrics_link, link_completed_eaid, subject_id_to_link_dict)
    except QualtricsAPIError as e:
        return jsonify({"success": False, "message": str(e), "debug_inputs": debug_inputs}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error in button2: {e}", "debug_inputs": debug_inputs}), 500

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
        subjects_not_completed_survey = get_incomplete_subjects(ldot_client, ldot_study_id, eaid_survey_invitation_completed, eaid_survey_progress_completed)
        message = f"Found {len(subjects_not_completed_survey)} subjects who have not completed the survey"
        return jsonify({"success": True, "message": message, "subject_ids": subjects_not_completed_survey})
    except QualtricsAPIError as e:
        return jsonify({"success": False, "message": str(e)}), 502
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/button4", methods=["POST"])
def button4():
    """Fourth API call - uses subjectIDs from button3"""
    data = request.json
    study_id = data.get("study_id")
    subject_ids = data.get("subject_ids")  # List of subjectIDs from button3

    if not study_id:
        return jsonify({"success": False, "message": "Missing study_id in request"}), 400

    study, ldot_vars, qualtrics_vars = get_study_settings(study_id)

    ldot_study_id = ldot_vars.get("ldot_study_id")
    id_deelnemer_entity = ldot_vars.get("id_deelnemer_entity")
    id_location = ldot_vars.get("id_location")
    qualtrics_survey_id = qualtrics_vars.get("qualtrics_survey_id")
    embedded_data_field = qualtrics_vars.get("embedded_data_field")

    try:
        participant_to_progress_dict = get_individual_progress(ldot_client, ldot_study_id, id_deelnemer_entity, id_location, subject_ids, embedded_data_field, qualtrics_survey_id)
    except QualtricsAPIError as e:
        return jsonify({"success": False, "message": str(e)}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error in button4: {e}"}), 500

    return jsonify({
        "success": True,
        "message": f"Retrieved progress for {len(participant_to_progress_dict)} subjects",
        "study_id": study_id,
        "qualtrics_survey_id": qualtrics_survey_id,
        "embedded_data_field": embedded_data_field,
        "progress_results": participant_to_progress_dict,
    })

    # Here need to add the last step to send the progress back to Ldot, but that will be done in a separate function or workflow.

if __name__ == "__main__":
    app.run(debug=True)

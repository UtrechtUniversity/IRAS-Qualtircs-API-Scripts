from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from threading import Lock

from dotenv import load_dotenv, dotenv_values
from flask import Flask, render_template, request, jsonify
import requests
import yaml
import os

from new_ldot_workflows.ldot_client import LdotClient
from new_ldot_workflows.qualtrics_client import QualtricsClient
from new_ldot_workflows.b_1_get_new_subjects import get_new_subjects
from new_ldot_workflows.b_2_get_qualtrics_links import add_individuals_to_survey
from new_ldot_workflows.b_2_send_links_to_ldot import send_links_to_ldot
from new_ldot_workflows.b_3_get_incomplete_subjects import get_incomplete_subjects
from new_ldot_workflows.b_4_get_individual_progress import get_individual_progress
from new_ldot_workflows.b_4_send_progress_to_ldot import send_progress_to_ldot
from new_ldot_workflows.logging_utils import QualtricsAPIError

app = Flask(__name__)


CONFIG_PATH = Path(__file__).resolve().with_name("study_configs.yaml")
STUDIES = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

LDOT_API_URL="https://accware.memic.maastrichtuniversity.nl/memic_ldot_api/api/v1.1"
LDOT_TOKEN_URL="https://accware.memic.maastrichtuniversity.nl/ldot_identity_server/connect/token"
QUALTRICS_BASE_URL="https://fra1.qualtrics.com/API/v3"


CLIENT_CACHE = {}
CLIENT_CACHE_LOCK = Lock()


load_dotenv()

@dataclass
class StudySettings:
    study_id: str
    name: str
    config_path: Optional[str] = None
    ldot_study_id: Optional[str] = None
    id_deelnemer_entity: Optional[str] = None
    id_location: Optional[str] = None
    custom_var_qualtrics_link: Optional[str] = None
    eaid_qualtrics_survey_link_creation_to_do_date: Optional[str] = None
    eaid_qualtrics_survey_link_creation_completed: Optional[str] = None
    eaid_survey_invitation_completed: Optional[str] = None
    eaid_survey_progress_completed: Optional[str] = None
    survey_id: Optional[str] = None
    mailing_list_id: Optional[str] = None
    embedded_data_field: Optional[str] = None
    directory_id: Optional[str] = None
    distribution_id: Optional[str] = None

def get_study_settings(study_key: str):
    study_variables = STUDIES.get(study_key)
    if not study_variables:
        return None

    ldot_vars = study_variables.get("ldot_variables", {})
    qualtrics_vars = study_variables.get("qualtrics_variables", {})
    return StudySettings(
        study_id=study_key,
        name=study_variables.get("name", study_key),
        config_path=study_variables.get("config_path"),
        ldot_study_id=ldot_vars.get("ldot_study_id"),
        id_deelnemer_entity=ldot_vars.get("id_deelnemer_entity"),
        id_location=ldot_vars.get("id_location"),
        custom_var_qualtrics_link=ldot_vars.get("custom_var_qualtrics_link"),
        eaid_qualtrics_survey_link_creation_to_do_date=ldot_vars.get("eaid_qualtrics_survey_link_creation_to_do_date"),
        eaid_qualtrics_survey_link_creation_completed=ldot_vars.get("eaid_qualtrics_survey_link_creation_completed"),
        eaid_survey_invitation_completed=ldot_vars.get("eaid_survey_invitation_completed"),
        eaid_survey_progress_completed=ldot_vars.get("eaid_survey_progress_completed"),
        survey_id=qualtrics_vars.get("qualtrics_survey_id"),
        mailing_list_id=qualtrics_vars.get("mailing_list_id"),
        embedded_data_field=qualtrics_vars.get("embedded_data_field"),
        directory_id=qualtrics_vars.get("directory_id"),
        distribution_id=qualtrics_vars.get("distribution_id"),
    )


def get_clients_for_study(study_variables: StudySettings):
    if not study_variables.config_path:
        raise ValueError(f"Missing config_path for study_id: {study_variables.study_id}")

    cached_clients = CLIENT_CACHE.get(study_variables.study_id)
    if cached_clients:
        return cached_clients

    with CLIENT_CACHE_LOCK:
        cached_clients = CLIENT_CACHE.get(study_variables.study_id)
        if cached_clients:
            return cached_clients

        study_env_path = (CONFIG_PATH.parent / "app-secrets" / study_variables.config_path).resolve()

        print(f"Loading study config from: {study_env_path}")

        if not study_env_path.exists():
            raise FileNotFoundError(f"Study config file not found: {study_env_path}")

        study_env = dotenv_values(study_env_path)
        ldot_client_id = study_env.get("LDOT_client_id") or os.environ.get("LDOT_client_id")
        ldot_client_secret = study_env.get("LDOT_client_secret") or os.environ.get("LDOT_client_secret")
        qualtrics_api_token = study_env.get("QUALTRICS_API_TOKEN") or os.environ.get("QUALTRICS_API_TOKEN")

        missing_secrets = [
            secret_name
            for secret_name, secret_value in (
                ("LDOT_client_id", ldot_client_id),
                ("LDOT_client_secret", ldot_client_secret),
                ("QUALTRICS_API_TOKEN", qualtrics_api_token),
            )
            if not secret_value
        ]
        if missing_secrets:
            raise KeyError(f"Missing secrets in {study_env_path}: {', '.join(missing_secrets)}")

        ldot_client = LdotClient(
            token_url=LDOT_TOKEN_URL,
            api_url=LDOT_API_URL,
            client_id=ldot_client_id,
            client_secret=ldot_client_secret,
        )

        qualtrics_client = QualtricsClient(
            api_url=QUALTRICS_BASE_URL,
            token=qualtrics_api_token,
        )

        CLIENT_CACHE[study_variables.study_id] = (ldot_client, qualtrics_client)
        return CLIENT_CACHE[study_variables.study_id]


@app.route("/")
def index():
    return render_template("index.html", studies=STUDIES)


@app.route("/api/button1", methods=["POST"])
def button1():
    """Get the participants who have not yet been given a survey link and return their subjectIDs"""
    
    data = request.json
    study_id = data.get("study_id")

    study_variables = get_study_settings(study_id)
    if not study_variables:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    try:
        ldot_client, _ = get_clients_for_study(study_variables)
    except (KeyError, ValueError) as e:
        return jsonify({"success": False, "message": str(e)}), 500

    try:
        new_subjects_ids = get_new_subjects(
            ldot_client,
            study_variables.ldot_study_id,
            study_variables.eaid_qualtrics_survey_link_creation_to_do_date,
            study_variables.eaid_qualtrics_survey_link_creation_completed,
        )
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
    study_variables = get_study_settings(study_id)

    if not study_variables:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    debug_inputs = {
        "study_id": study_id,
        "ldot_study_id": study_variables.ldot_study_id,
        "id_deelnemer_entity": study_variables.id_deelnemer_entity,
        "id_location": study_variables.id_location,
        "new_subject_ids": new_subject_ids,
        "qualtrics_survey_id": study_variables.survey_id,
        "mailing_list_id": study_variables.mailing_list_id,
        "embedded_data_field": study_variables.embedded_data_field,
        "directory_id": study_variables.directory_id,
        "distribution_id": study_variables.distribution_id,
    }

    try:
        ldot_client, qualtrics_client = get_clients_for_study(study_variables)
    except (KeyError, ValueError) as e:
        return jsonify({"success": False, "message": str(e), "debug_inputs": debug_inputs}), 500

    try:
        subject_id_to_link_dict = add_individuals_to_survey(
            ldot_client,
            qualtrics_client,
            new_subject_ids,
            study_variables.ldot_study_id,
            study_variables.id_deelnemer_entity,
            study_variables.embedded_data_field,
            study_variables.distribution_id,
            study_variables.survey_id,
            study_variables.mailing_list_id,
            study_variables.directory_id,
        )
        send_links_to_ldot(
            ldot_client,
            study_variables.ldot_study_id,
            study_variables.id_deelnemer_entity,
            study_variables.id_location,
            study_variables.custom_var_qualtrics_link,
            study_variables.eaid_qualtrics_survey_link_creation_completed,
            subject_id_to_link_dict,
        )
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
    study_variables = get_study_settings(study_id)

    if not study_variables:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    try:
        ldot_client, _ = get_clients_for_study(study_variables)
    except (KeyError, ValueError) as e:
        return jsonify({"success": False, "message": str(e)}), 500

    try:
        subjects_not_completed_survey = get_incomplete_subjects(
            ldot_client,
            study_variables.ldot_study_id,
            study_variables.eaid_survey_invitation_completed,
            study_variables.eaid_survey_progress_completed,
        )
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

    study_variables = get_study_settings(study_id)

    if not study_variables:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    try:
        ldot_client, qualtrics_client = get_clients_for_study(study_variables)
    except (KeyError, ValueError) as e:
        return jsonify({"success": False, "message": str(e)}), 500

    try:
        participant_to_progress_dict = get_individual_progress(
            ldot_client,
            qualtrics_client,
            study_variables.ldot_study_id,
            study_variables.id_deelnemer_entity,
            study_variables.id_location,
            subject_ids,
            study_variables.embedded_data_field,
            study_variables.survey_id,
        )
        send_progress_to_ldot(
            ldot_client,
            study_variables.ldot_study_id,
            study_variables.eaid_survey_progress_completed,
            participant_to_progress_dict,
        )

    except QualtricsAPIError as e:
        return jsonify({"success": False, "message": str(e)}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error in button4: {e}"}), 500

    return jsonify({
        "success": True,
        "message": f"Retrieved progress for {len(participant_to_progress_dict)} subjects",
        "study_id": study_id,
        "qualtrics_survey_id": study_variables.survey_id,
        "embedded_data_field": study_variables.embedded_data_field,
        "progress_results": participant_to_progress_dict,
    })

    # Here need to add the last step to send the progress back to Ldot, but that will be done in a separate function or workflow.

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
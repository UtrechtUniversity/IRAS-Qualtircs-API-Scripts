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
# from new_ldot_workflows.b_1_get_new_subjects import get_new_subjects
# from new_ldot_workflows.b_2_get_qualtrics_links import add_individuals_to_survey
# from new_ldot_workflows.b_2_send_links_to_ldot import send_links_to_ldot
# from new_ldot_workflows.b_3_get_incomplete_subjects import get_incomplete_subjects
# from new_ldot_workflows.b_4_get_individual_progress import get_individual_progress
# from new_ldot_workflows.b_4_send_progress_to_ldot import send_progress_to_ldot
from new_ldot_workflows.logging_utils import QualtricsAPIError

from new_ldot_workflows.create_qualtrics_survey_link_handler import handle_create_qualtrics_survey_link
from new_ldot_workflows.check_qualtrics_survey_handler import handle_check_qualtrics_survey_module

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
class WorkUnit:
    unit_id: str
    name: str
    trigger: Optional[str]
    resolution: Optional[str]
    boolean_action: dict

@dataclass
class StudySettings:
    study_id: str
    name: str
    config_path: str
    ldot_variables: dict = None
    work_units: dict = None 


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


def get_study_settings(study_key: str) -> Optional[StudySettings]:
    study_variables = STUDIES.get(study_key)
    if not study_variables:
        return None

    work_units = {}
    for unit_id, unit_data in (study_variables.get("work_units") or {}).items():
        work_units[unit_id] = WorkUnit(
            unit_id=unit_id,
            name=unit_data.get("name", unit_id),
            trigger=unit_data.get("trigger"),
            resolution=unit_data.get("resolution"),
            boolean_action=unit_data.get("boolean_action", {}),
        )

    return StudySettings(
        study_id=study_key,
        name=study_variables.get("name", study_key),
        config_path=study_variables.get("config_path"),
        ldot_variables=study_variables.get("ldot_variables", {}),
        work_units=work_units,
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


@app.route("/api/study/<study_id>/work_units")
def study_work_units(study_id):
    study_variables = get_study_settings(study_id)
    if not study_variables:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 404

    units = [
        {"unit_id": wu.unit_id, "name": wu.name}
        for wu in study_variables.work_units.values()
    ]
    return jsonify({"success": True, "work_units": units})



@app.route("/api/execute_work_unit", methods=["POST"])
def execute_work_unit():
    data = request.json
    study_id = data.get("study_id")
    unit_id = data.get("unit_id")

    study_variables = get_study_settings(study_id)
    if not study_variables:
        return jsonify({"success": False, "message": f"Unknown study_id: {study_id}"}), 400

    unit = (study_variables.work_units or {}).get(unit_id)
    if not unit:
        return jsonify({"success": False, "message": f"Unknown work unit: {unit_id}"}), 400


    WORK_UNIT_HANDLERS = {
        "Create Qualtrics survey link": handle_create_qualtrics_survey_link,
        "Check Qualtrics survey": handle_check_qualtrics_survey_module,
    }

    handler = WORK_UNIT_HANDLERS.get(unit.boolean_action.get("type"))
    if not handler:
        return jsonify({
            "success": False,
            "message": f"No handler registered for action type: {unit.boolean_action.get('type')!r}"
        }), 400

    try:
        ldot_client, qualtrics_client = get_clients_for_study(study_variables)
    except (KeyError, ValueError) as e:
        return jsonify({"success": False, "message": str(e)}), 500

    try:
        result = handler(ldot_client, qualtrics_client, study_variables, unit)
    except QualtricsAPIError as e:
        return jsonify({"success": False, "message": str(e)}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {e}"}), 500

    return jsonify({"success": True, **result})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
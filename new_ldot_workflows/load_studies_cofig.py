from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Literal, Union, Annotated
from pathlib import Path
import re
import yaml


# String validation functions

def validate_ldot_guid(value: str, field_name: str) -> str:
    GUID_PATTERN = re.compile(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )

    if not GUID_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a valid GUID, got: {value!r}")
    return value

def validate_qualtrics_prefix(value: str, prefix: str, field_name: str) -> str:
    if not value.startswith(prefix):
        raise ValueError(
            f"{field_name} must start with '{prefix}' per the Qualtrics API documentation"
        )
    return value


# Classes for the boolean action type variables
class CreateQualtricsSurveyLinkVariables(BaseModel):
    ldot_custom_var_qualtrics_link: str = Field(min_length=1)
    qualtrics_survey_id: str
    directory_id: str
    distribution_id: str
    mailing_list_id: str
    embedded_data_field: str = Field(min_length=1)

    @field_validator("qualtrics_survey_id")
    @classmethod
    def validate_survey_id(cls, v):
        return validate_qualtrics_prefix(v, "SV_", "qualtrics_survey_id")

    @field_validator("directory_id")
    @classmethod
    def validate_directory_id(cls, v):
        return validate_qualtrics_prefix(v, "POOL_", "directory_id")

    @field_validator("distribution_id")
    @classmethod
    def validate_distribution_id(cls, v):
        return validate_qualtrics_prefix(v, "EMD_", "distribution_id")

    @field_validator("mailing_list_id")
    @classmethod
    def validate_mailing_list_id(cls, v):
        return validate_qualtrics_prefix(v, "CG_", "mailing_list_id")


class CheckSurveyProgressVariables(BaseModel):
    qualtrics_survey_id: str
    embedded_data_field: str = Field(min_length=1)

    @field_validator("qualtrics_survey_id")
    @classmethod
    def validate_survey_id(cls, v):
        return validate_qualtrics_prefix(v, "SV_", "qualtrics_survey_id")

# Classes for the boolean action types
class CreateQualtricsSurveyLinkAction(BaseModel):
    type: Literal["Create Qualtrics survey link"]
    variables: CreateQualtricsSurveyLinkVariables

class CheckSurveyProgressAction(BaseModel):
    type: Literal["Check Qualtrics survey"]
    variables: CheckSurveyProgressVariables


# Discriminated union: Pydantic picks the right model based on `type`
BooleanAction = Annotated[
    Union[CreateQualtricsSurveyLinkAction, CheckSurveyProgressAction],
    Field(discriminator="type"),
]

# Classe for the work units
class WorkUnit(BaseModel):
    name: str = Field(min_length=1)
    trigger: str
    resolution: str
    boolean_action: BooleanAction

    @field_validator("trigger", "resolution")
    @classmethod
    def check_guid(cls, v, info):
        return validate_ldot_guid(v, info.field_name)


# Classes for the ldot variables
class LdotVariables(BaseModel):
    ldot_study_id: str
    id_deelnemer_entity: str
    id_location: str

    @field_validator("ldot_study_id", "id_deelnemer_entity", "id_location")
    @classmethod
    def check_guid(cls, v, info):
        return validate_ldot_guid(v, info.field_name)
    
# Class for the overall study configuration
class StudyConfig(BaseModel):
    name: str = Field(min_length=1)
    config_path: Path
    ldot_variables: LdotVariables
    work_units: dict[str, WorkUnit]

class StudiesConfig(BaseModel):
    studies: dict[str, StudyConfig]

def load_studies_config(config_path: Path) -> StudiesConfig:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        return StudiesConfig(studies=config)
    except ValidationError as e:
        raise SystemExit(f"The study configuration is invalid, here is why: \n{e}") from e
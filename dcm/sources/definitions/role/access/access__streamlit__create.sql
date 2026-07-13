-- noqa: disable=LT02

define role {{ sis_role_name_prefix }}_ACCESS__STREAMLIT__CREATE
    comment = 'Streamlit App 作成権限'
;

grant role {{ sis_role_name_prefix }}_ACCESS__STREAMLIT__CREATE to role {{ project_owner_role }};

grant usage on database {{ sis_database_name }} to role {{ sis_role_name_prefix }}_ACCESS__STREAMLIT__CREATE;
grant usage on schema {{ sis_database_name }}.APP to role {{ sis_role_name_prefix }}_ACCESS__STREAMLIT__CREATE;

GRANT CREATE STREAMLIT ON SCHEMA {{ sis_database_name }}.APP
    TO ROLE {{ sis_role_name_prefix }}_ACCESS__STREAMLIT__CREATE
;

-- noqa: disable=LT02

define role {{ sis_role_name_prefix }}_FUNC_SIS_READER
    comment = 'Streamlit App 参照者向けロール'
;

grant role {{ sis_role_name_prefix }}_FUNC_SIS_READER to role {{ project_owner_role }};

grant role {{ sis_role_name_prefix }}_ACCESS__WH__SIS__USAGE to role {{ sis_role_name_prefix }}_FUNC_SIS_READER;

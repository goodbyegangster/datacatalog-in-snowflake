-- noqa: disable=LT02

define role {{ sis_role_prefix }}_ACCESS__INT__PYPI__USAGE
    comment = 'external access integration {{ external_access_pypi_name }} 向け利用権限'
;

grant role {{ sis_role_prefix }}_ACCESS__INT__PYPI__USAGE to role {{ project_owner_role }};

grant usage on integration {{ external_access_pypi_name }} to role {{ sis_role_prefix }}_ACCESS__INT__PYPI__USAGE;

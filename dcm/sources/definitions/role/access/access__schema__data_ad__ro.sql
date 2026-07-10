-- noqa: disable=LT02

define database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
    comment = 'スキーマ DATA_AD 向け参照権限'
;

grant usage on schema {{ sis_database_name }}.DATA_AD
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
;

grant select, references on all tables in schema {{ sis_database_name }}.DATA_AD
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
;
grant select, references on all views in schema {{ sis_database_name }}.DATA_AD
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
;
grant select, monitor on all dynamic tables in schema {{ sis_database_name }}.DATA_AD
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
;

grant select, references on future tables in schema {{ sis_database_name }}.DATA_AD
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
;
grant select, references on future views in schema {{ sis_database_name }}.DATA_AD
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
;
grant select, monitor on future dynamic tables in schema {{ sis_database_name }}.DATA_AD
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO
;

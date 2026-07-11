-- noqa: disable=LT02

define database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
    comment = 'スキーマ CATALOG 向け参照権限'
;

grant usage on schema {{ sis_database_name }}.CATALOG
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
;

grant select, references on all tables in schema {{ sis_database_name }}.CATALOG
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
;
grant select, references on all views in schema {{ sis_database_name }}.CATALOG
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
;
grant select, monitor on all dynamic tables in schema {{ sis_database_name }}.CATALOG
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
;

grant select, references on future tables in schema {{ sis_database_name }}.CATALOG
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
;
grant select, references on future views in schema {{ sis_database_name }}.CATALOG
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
;
grant select, monitor on future dynamic tables in schema {{ sis_database_name }}.CATALOG
    to database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO
;

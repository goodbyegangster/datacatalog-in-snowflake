-- noqa: disable=LT02

define database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
    comment = 'スキーマ DATA_SALES 向け参照権限'
;

grant usage on schema {{ datacatalog_database_name }}.DATA_SALES
    to database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
;

grant select, references on all tables in schema {{ datacatalog_database_name }}.DATA_SALES
    to database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
;
grant select, references on all views in schema {{ datacatalog_database_name }}.DATA_SALES
    to database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
;
grant select, monitor on all dynamic tables in schema {{ datacatalog_database_name }}.DATA_SALES
    to database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
;

grant select, references on future tables in schema {{ datacatalog_database_name }}.DATA_SALES
    to database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
;
grant select, references on future views in schema {{ datacatalog_database_name }}.DATA_SALES
    to database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
;
grant select, monitor on future dynamic tables in schema {{ datacatalog_database_name }}.DATA_SALES
    to database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO
;

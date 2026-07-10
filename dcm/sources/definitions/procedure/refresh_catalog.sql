-- noqa: disable=LT02

-- マスターテーブルを依存順にリフレッシュするオーケストレーター。
-- 依存順：USERS / ASSETS → COLUMNS / ACCESS_EDGES → ASSET_VISIBILITY（TAGS は依存なし）

define procedure {{ sis_database_name }}.PROCEDURE.REFRESH_CATALOG()
    returns string
    language sql
    execute as owner
as
$$
begin
    call {{ sis_database_name }}.PROCEDURE.REFRESH_USERS();
    call {{ sis_database_name }}.PROCEDURE.REFRESH_ASSETS();
    call {{ sis_database_name }}.PROCEDURE.REFRESH_COLUMNS();
    call {{ sis_database_name }}.PROCEDURE.REFRESH_TAGS();
    call {{ sis_database_name }}.PROCEDURE.REFRESH_ACCESS_EDGES();
    call {{ sis_database_name }}.PROCEDURE.REFRESH_ASSET_VISIBILITY();

    return 'CATALOG refresh completed';
end;
$$
;

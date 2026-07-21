-- マスターテーブルを依存順にリフレッシュするオーケストレーター。
-- 依存順：USERS / ASSETS → COLUMNS / ACCESS_EDGES → ASSET_VISIBILITY（TAGS は依存なし）

define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_CATALOG()
    returns string
    language sql
    execute as owner
as
$$
begin
    call {{ datacatalog_database_name }}.PROCEDURE.REFRESH_USERS();
    call {{ datacatalog_database_name }}.PROCEDURE.REFRESH_ASSETS();
    call {{ datacatalog_database_name }}.PROCEDURE.REFRESH_COLUMNS();
    call {{ datacatalog_database_name }}.PROCEDURE.REFRESH_TAGS();
    call {{ datacatalog_database_name }}.PROCEDURE.REFRESH_ACCESS_EDGES();
    call {{ datacatalog_database_name }}.PROCEDURE.REFRESH_ASSET_VISIBILITY();

    return 'CATALOG refresh completed';
end;
$$
;

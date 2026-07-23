define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_CATALOG()
    returns string
    language sql
    comment = 'CATALOG スキーマ向け procedure 実行処理'
    execute as owner
as
$$
begin
    -- 各処理の依存関係に従い順番に実行
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

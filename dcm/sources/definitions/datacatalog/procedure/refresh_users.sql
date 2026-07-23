define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_USERS()
    returns string
    language sql
    comment = 'USERS テーブル洗替処理'
    execute as owner
as
$$
begin
    create or replace table {{ datacatalog_database_name }}.CATALOG.USERS (
        USER_NAME    comment '名前',
        DISPLAY_NAME comment '表示名',
        USER_TYPE    comment 'タイプ',
        DISABLED     comment 'ステータス（true = 無効）'
    ) as
    select
        name::varchar(255)                    as USER_NAME,
        display_name::varchar(255)            as DISPLAY_NAME,
        coalesce(type, 'PERSON')::varchar(50) as USER_TYPE,
        disabled::boolean                     as DISABLED
    from SNOWFLAKE.ACCOUNT_USAGE.USERS
    where deleted_on is null
        and (
            type in ('PERSON', 'SERVICE', 'LEGACY_SERVICE')
            or type is null
        )
    ;

    return 'CATALOG.USERS refreshed';
end;
$$
;

-- noqa: disable=LT02

define procedure {{ sis_database_name }}.PROCEDURE.REFRESH_USERS()
    returns string
    language sql
    execute as owner
as
$$
begin
    create or replace table {{ sis_database_name }}.CATALOG.USERS (
        USER_NAME    comment '名前',
        DISPLAY_NAME comment '表示名',
        USER_TYPE    comment 'タイプ',
        DISABLED     comment 'ステータス（true = 無効）'
    ) as
    select
        name::varchar(255)                    as user_name,
        display_name::varchar(255)            as display_name,
        coalesce(type, 'PERSON')::varchar(50) as user_type,
        disabled::boolean                     as disabled
    from snowflake.account_usage.users
    where deleted_on is null
        and (type in ('PERSON', 'SERVICE', 'LEGACY_SERVICE') or type is null)
    ;

    return 'CATALOG.USERS refreshed';
end;
$$
;

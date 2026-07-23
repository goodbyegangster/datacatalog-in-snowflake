define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_TAGS()
    returns string
    language sql
    comment = 'TAGS テーブル洗替処理'
    execute as owner
as
$$
begin
    create or replace table {{ datacatalog_database_name }}.CATALOG.TAGS (
        TAG_DATABASE comment 'タグの DB',
        TAG_SCHEMA   comment 'タグのスキーマ',
        TAG_NAME     comment 'タグ名',
        TAG_VALUE    comment 'タグ定義の allowed_values（未使用の値も含む）',
        TAG_COMMENT  comment 'タグ定義のコメント'
    ) as
    select
        t.tag_database::varchar(255) as TAG_DATABASE,
        t.tag_schema::varchar(255)   as TAG_SCHEMA,
        t.tag_name::varchar(255)     as TAG_NAME,
        av.value::varchar(255)       as TAG_VALUE,
        t.tag_comment::varchar       as TAG_COMMENT
    from SNOWFLAKE.ACCOUNT_USAGE.TAGS as t,
        -- allowed_values 未定義（自由記述）のタグは値を列挙できないため本マスターには現れない
        lateral flatten(input => t.allowed_values) as av
    where t.deleted is null;

    return 'CATALOG.TAGS refreshed';
end;
$$
;

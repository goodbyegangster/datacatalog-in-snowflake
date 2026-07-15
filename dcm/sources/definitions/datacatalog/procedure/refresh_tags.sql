-- noqa: disable=LT02

-- 検索プルダウン用のタグ値マスター。
-- ACCOUNT_USAGE.TAGS の allowed_values を展開して保持する（未使用の値も含めることで
-- 「その値を持つデータ資産が無い」ことを表現できる）。
-- 依存なし（ACCOUNT_USAGE.TAGS のみ）。
-- NOTE: allowed_values 未定義（自由記述）のタグは値を列挙できないため本マスターには現れない。

define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_TAGS()
    returns string
    language sql
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
        t.tag_database::varchar(255),
        t.tag_schema::varchar(255),
        t.tag_name::varchar(255),
        av.value::varchar(255),
        t.tag_comment::varchar
    from snowflake.account_usage.tags as t,
         lateral flatten(input => t.allowed_values) as av
    where t.deleted is null;

    return 'CATALOG.TAGS refreshed';
end;
$$
;

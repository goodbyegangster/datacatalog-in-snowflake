define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_COLUMNS()
    returns string
    language sql
    comment = 'COLUMNS テーブル洗替処理'
    execute as owner
as
$$
begin
    -- 制約情報（PKEY）の SHOW コマンド結果を一時表へ退避
    show primary keys in account;
    create or replace temporary table {{ datacatalog_database_name }}.CATALOG.TMP_PK as
        select
            "database_name" as DATABASE_NAME,
            "schema_name"   as SCHEMA_NAME,
            "table_name"    as TABLE_NAME,
            "column_name"   as COLUMN_NAME
        from table(result_scan(last_query_id()));

    -- 制約情報（UNIQUE）の SHOW コマンド結果を一時表へ退避
    show unique keys in account;
    create or replace temporary table {{ datacatalog_database_name }}.CATALOG.TMP_UK as
        select
            "database_name" as DATABASE_NAME,
            "schema_name"   as SCHEMA_NAME,
            "table_name"    as TABLE_NAME,
            "column_name"   as COLUMN_NAME
        from table(result_scan(last_query_id()));

    -- 制約情報（FKEY）の SHOW コマンド結果を一時表へ退避
    show imported keys in account;
    create or replace temporary table {{ datacatalog_database_name }}.CATALOG.TMP_FK as
        select
            "fk_database_name" as DATABASE_NAME,
            "fk_schema_name"   as SCHEMA_NAME,
            "fk_table_name"    as TABLE_NAME,
            "fk_column_name"   as COLUMN_NAME,
            "pk_database_name" as REFERENCED_DATABASE_NAME,
            "pk_schema_name"   as REFERENCED_SCHEMA_NAME,
            "pk_table_name"    as REFERENCED_TABLE_NAME,
            "pk_column_name"   as REFERENCED_COLUMN_NAME
        from table(result_scan(last_query_id()));

    create or replace table {{ datacatalog_database_name }}.CATALOG.COLUMNS (
        TABLE_ID            comment '所属データ資産のキー',
        DATABASE_NAME       comment '階層_データベース',
        SCHEMA_NAME         comment '階層_スキーマ',
        TABLE_NAME          comment '所属データ資産名',
        COLUMN_NAME         comment '名前',
        ORDINAL_POSITION    comment '表示順',
        DATA_TYPE           comment 'データ型',
        DESCRIPTION         comment '説明',
        TAGS                comment 'タグ一覧。要素 object = {TAG_DATABASE, TAG_SCHEMA, TAG_NAME, TAG_VALUE}。なしは空配列',
        IS_PRIMARY_KEY      comment '制約_PRIMARY_KEY',
        IS_UNIQUE_KEY       comment '制約_UNIQUE',
        FOREIGN_KEYS        comment '制約_FOREIGN_KEY 参照先一覧。なしは空配列',
        IS_NULLABLE         comment '制約_NOT_NULL（false = NOT NULL）',
        MASKING_POLICY_NAME comment 'マスキングポリシー'
    ) as
    with
    -- ACCOUNT_USAGE.COLUMNS から現存するカラムを取得し、METADATA$ 列を除いて source_columns とする
    source_columns as (
        select
            table_catalog    as DATABASE_NAME,
            table_schema     as SCHEMA_NAME,
            table_name       as TABLE_NAME,
            column_name      as COLUMN_NAME,
            ordinal_position as ORDINAL_POSITION,
            data_type        as DATA_TYPE,
            comment          as DESCRIPTION,
            is_nullable      as IS_NULLABLE_TEXT
        from SNOWFLAKE.ACCOUNT_USAGE.COLUMNS
        where
            deleted is null
            -- dynamic table に METADATA$ カラムが現れるため除外
            and not startswith(column_name, 'METADATA$')
    ),

    -- source_columns を CATALOG.ASSETS と照合し、対象資産のカラムに TABLE_ID を付けて asset_columns とする
    asset_columns as (
        select
            a.TABLE_ID,
            c.DATABASE_NAME,
            c.SCHEMA_NAME,
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.ORDINAL_POSITION,
            c.DATA_TYPE,
            c.DESCRIPTION,
            c.IS_NULLABLE_TEXT
        from source_columns as c
        inner join {{ datacatalog_database_name }}.CATALOG.ASSETS as a
            on  a.DATABASE_NAME = c.DATABASE_NAME
            and a.SCHEMA_NAME   = c.SCHEMA_NAME
            and a.ASSET_NAME    = c.TABLE_NAME
    ),

    -- ACCOUNT_USAGE.TAG_REFERENCES から有効なカラムタグを取得し、重複を除いて distinct_column_tag_references とする
    distinct_column_tag_references as (
        select
            tr.object_database as DATABASE_NAME,
            tr.object_schema   as SCHEMA_NAME,
            tr.object_name     as TABLE_NAME,
            tr.column_name     as COLUMN_NAME,
            tr.tag_database    as TAG_DATABASE,
            tr.tag_schema      as TAG_SCHEMA,
            tr.tag_name        as TAG_NAME,
            tr.tag_value       as TAG_VALUE
        from SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES as tr
        where tr.domain = 'COLUMN'
          and tr.object_deleted is null
          and tr.column_name is not null
        group by
            tr.object_database,
            tr.object_schema,
            tr.object_name,
            tr.column_name,
            tr.tag_database,
            tr.tag_schema,
            tr.tag_name,
            tr.tag_value
    ),

    -- distinct_column_tag_references のタグをカラムごとに配列へまとめ、TAGS を持つ column_tags とする
    column_tags as (
        select
            d.DATABASE_NAME,
            d.SCHEMA_NAME,
            d.TABLE_NAME,
            d.COLUMN_NAME,
            array_agg(object_construct(
                'TAG_DATABASE', d.TAG_DATABASE,
                'TAG_SCHEMA',   d.TAG_SCHEMA,
                'TAG_NAME',     d.TAG_NAME,
                'TAG_VALUE',    d.TAG_VALUE
            )) as TAGS
        from distinct_column_tag_references as d
        group by d.DATABASE_NAME, d.SCHEMA_NAME, d.TABLE_NAME, d.COLUMN_NAME
    ),

    -- ACCOUNT_USAGE.POLICY_REFERENCES からカラムに適用されたマスキングポリシーを抽出し、masking_policies とする
    masking_policies as (
        select
            pr.ref_database_name as DATABASE_NAME,
            pr.ref_schema_name   as SCHEMA_NAME,
            pr.ref_entity_name   as TABLE_NAME,
            pr.ref_column_name   as COLUMN_NAME,
            pr.policy_name       as MASKING_POLICY_NAME
        from SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES as pr
        where pr.policy_kind = 'MASKING_POLICY'
          and pr.ref_column_name is not null
    ),

    -- TMP_FK の外部キー参照先をカラムごとに配列へまとめ、FOREIGN_KEYS を持つ foreign_keys とする
    foreign_keys as (
        select
            DATABASE_NAME,
            SCHEMA_NAME,
            TABLE_NAME,
            COLUMN_NAME,
            array_agg(object_construct(
                'REFERENCED_DATABASE', REFERENCED_DATABASE_NAME,
                'REFERENCED_SCHEMA',   REFERENCED_SCHEMA_NAME,
                'REFERENCED_TABLE',    REFERENCED_TABLE_NAME,
                'REFERENCED_COLUMN',   REFERENCED_COLUMN_NAME
            )) as FOREIGN_KEYS
        from {{ datacatalog_database_name }}.CATALOG.TMP_FK
        group by DATABASE_NAME, SCHEMA_NAME, TABLE_NAME, COLUMN_NAME
    ),

    -- asset_columns に制約、タグ、外部キー、マスキングポリシーを付与し、最終出力用の catalog_columns とする
    catalog_columns as (
        select
            cols.TABLE_ID::number                      as TABLE_ID,
            cols.DATABASE_NAME::varchar(255)           as DATABASE_NAME,
            cols.SCHEMA_NAME::varchar(255)             as SCHEMA_NAME,
            cols.TABLE_NAME::varchar(255)              as TABLE_NAME,
            cols.COLUMN_NAME::varchar(255)             as COLUMN_NAME,
            cols.ORDINAL_POSITION::number              as ORDINAL_POSITION,
            cols.DATA_TYPE::varchar(255)               as DATA_TYPE,
            cols.DESCRIPTION::varchar                  as DESCRIPTION,
            coalesce(tags.TAGS, array_construct())     as TAGS,
            iff(pk.COLUMN_NAME is not null, true, false)::boolean
                                                      as IS_PRIMARY_KEY,
            iff(uk.COLUMN_NAME is not null, true, false)::boolean
                                                      as IS_UNIQUE_KEY,
            coalesce(fk.FOREIGN_KEYS, array_construct())
                                                      as FOREIGN_KEYS,
            (cols.IS_NULLABLE_TEXT = 'YES')::boolean   as IS_NULLABLE,
            mpol.MASKING_POLICY_NAME::varchar(255)     as MASKING_POLICY_NAME
        from asset_columns as cols
        left join {{ datacatalog_database_name }}.CATALOG.TMP_PK as pk
            on  pk.DATABASE_NAME = cols.DATABASE_NAME
            and pk.SCHEMA_NAME   = cols.SCHEMA_NAME
            and pk.TABLE_NAME    = cols.TABLE_NAME
            and pk.COLUMN_NAME   = cols.COLUMN_NAME
        left join {{ datacatalog_database_name }}.CATALOG.TMP_UK as uk
            on  uk.DATABASE_NAME = cols.DATABASE_NAME
            and uk.SCHEMA_NAME   = cols.SCHEMA_NAME
            and uk.TABLE_NAME    = cols.TABLE_NAME
            and uk.COLUMN_NAME   = cols.COLUMN_NAME
        left join foreign_keys as fk
            on  fk.DATABASE_NAME = cols.DATABASE_NAME
            and fk.SCHEMA_NAME   = cols.SCHEMA_NAME
            and fk.TABLE_NAME    = cols.TABLE_NAME
            and fk.COLUMN_NAME   = cols.COLUMN_NAME
        left join column_tags as tags
            on  tags.DATABASE_NAME = cols.DATABASE_NAME
            and tags.SCHEMA_NAME   = cols.SCHEMA_NAME
            and tags.TABLE_NAME    = cols.TABLE_NAME
            and tags.COLUMN_NAME   = cols.COLUMN_NAME
        left join masking_policies as mpol
            on  mpol.DATABASE_NAME = cols.DATABASE_NAME
            and mpol.SCHEMA_NAME   = cols.SCHEMA_NAME
            and mpol.TABLE_NAME    = cols.TABLE_NAME
            and mpol.COLUMN_NAME   = cols.COLUMN_NAME
    )
    select
        TABLE_ID,
        DATABASE_NAME,
        SCHEMA_NAME,
        TABLE_NAME,
        COLUMN_NAME,
        ORDINAL_POSITION,
        DATA_TYPE,
        DESCRIPTION,
        TAGS,
        IS_PRIMARY_KEY,
        IS_UNIQUE_KEY,
        FOREIGN_KEYS,
        IS_NULLABLE,
        MASKING_POLICY_NAME
    from catalog_columns
    ;

    return 'CATALOG.COLUMNS refreshed';
end;
$$
;

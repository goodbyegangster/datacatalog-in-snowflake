define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_ASSETS()
    returns string
    language sql
    comment = 'ASSETS テーブル洗替処理'
    execute as owner
as
$$
begin
    create or replace table {{ datacatalog_database_name }}.CATALOG.ASSETS (
        TABLE_ID                    comment 'データ資産の一意キー',
        DATABASE_NAME               comment '階層_データベース',
        SCHEMA_NAME                 comment '階層_スキーマ',
        ASSET_NAME                  comment '名前',
        ASSET_TYPE                  comment 'オブジェクト種類',
        DESCRIPTION                 comment '説明',
        ROW_COUNT                   comment '統計情報_行数（ROW_COUNT）',
        BYTES                       comment '統計情報_データサイズ（BYTES）',
        TAGS                        comment 'タグ一覧。要素 object = {TAG_DATABASE, TAG_SCHEMA, TAG_NAME, TAG_VALUE}。なしは空配列',
        CONTACT_STEWARD             comment '連絡先_スチュワード',
        CONTACT_SUPPORT             comment '連絡先_サポート',
        CONTACT_ACCESS_APPROVAL     comment '連絡先_承認者',
        CONTACT_SECURITY_COMPLIANCE comment '連絡先_セキュリティとコンプライアンス',
        IS_PUBLIC_VISIBILITY        comment 'PUBLIC ロールに OWNERSHIP/SELECT があり全ユーザーが参照可能なら true'
    ) as
    with
    -- ACCOUNT_USAGE.TABLES と DATABASES から現存する標準 DB 内の資産を抽出し、base_assets とする
    base_assets as (
        select
            t.table_id      as TABLE_ID,
            t.table_catalog as DATABASE_NAME,
            t.table_schema  as SCHEMA_NAME,
            t.table_name    as ASSET_NAME,
            case
                when t.is_dynamic = 'YES' then 'DYNAMIC TABLE'
                when t.is_iceberg = 'YES' then 'ICEBERG TABLE'
                when t.is_hybrid  = 'YES' then 'HYBRID TABLE'
                else t.table_type
            end             as ASSET_TYPE,
            t.comment       as DESCRIPTION,
            t.row_count     as ROW_COUNT,
            t.bytes         as BYTES
        from SNOWFLAKE.ACCOUNT_USAGE.TABLES as t
        inner join SNOWFLAKE.ACCOUNT_USAGE.DATABASES as d
            on d.database_name = t.table_catalog
        where t.deleted is null
            and d.deleted is null
            and d.type = 'STANDARD'
    ),

    -- ACCOUNT_USAGE.TAG_REFERENCES から現存する資産タグを取得し、重複を除いて distinct_asset_tag_references とする
    distinct_asset_tag_references as (
        select distinct
            object_database as DATABASE_NAME,
            object_schema   as SCHEMA_NAME,
            object_name     as ASSET_NAME,
            tag_database    as TAG_DATABASE,
            tag_schema      as TAG_SCHEMA,
            tag_name        as TAG_NAME,
            tag_value       as TAG_VALUE
        from SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
        -- 値 TABLE で対象資産に付与されているタグ情報を収集可能
        -- NOTE: https://docs.snowflake.com/en/sql-reference/functions/tag_references#arguments
        -- 'TABLE': Use this for all table-like objects such as views, materialized views, and external tables.
        where domain = 'TABLE'
            and object_deleted is null
            and column_name is null
    ),

    -- distinct_asset_tag_references のタグを資産ごとに配列へまとめ、TAGS を持つ asset_tags とする
    asset_tags as (
        select
            DATABASE_NAME,
            SCHEMA_NAME,
            ASSET_NAME,
            array_agg(object_construct(
                'TAG_DATABASE', TAG_DATABASE,
                'TAG_SCHEMA',   TAG_SCHEMA,
                'TAG_NAME',     TAG_NAME,
                'TAG_VALUE',    TAG_VALUE
            )) as TAGS
        from distinct_asset_tag_references
        group by DATABASE_NAME, SCHEMA_NAME, ASSET_NAME
    ),

    -- ACCOUNT_USAGE.CONTACT_REFERENCES の連絡先をオブジェクトごとに目的別で集約し、asset_contacts とする
    asset_contacts as (
        select
            object_database as DATABASE_NAME,
            object_schema   as SCHEMA_NAME,
            object_name     as ASSET_NAME,
            max(iff(contact_purpose = 'STEWARD',             contact_name, null)) as CONTACT_STEWARD,
            max(iff(contact_purpose = 'SUPPORT',             contact_name, null)) as CONTACT_SUPPORT,
            max(iff(contact_purpose = 'ACCESS_APPROVAL',     contact_name, null)) as CONTACT_ACCESS_APPROVAL,
            max(iff(contact_purpose = 'SECURITY_COMPLIANCE', contact_name, null)) as CONTACT_SECURITY_COMPLIANCE
        from SNOWFLAKE.ACCOUNT_USAGE.CONTACT_REFERENCES
        where object_deleted is null
        group by object_database, object_schema, object_name
    ),

    -- ACCOUNT_USAGE.GRANTS_TO_ROLES から PUBLIC が参照できる資産を抽出し、public_visible_assets とする
    public_visible_assets as (
        select distinct
            table_catalog as DATABASE_NAME,
            table_schema  as SCHEMA_NAME,
            name          as ASSET_NAME
        from SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
        where deleted_on is null
          and grantee_name = 'PUBLIC'
          -- DYNAMIC TABLE / ICEBERG TABLE / HYBRID TABLE は値 'TABLE' にて取得される
          and granted_on in ('TABLE', 'VIEW', 'MATERIALIZED VIEW', 'EXTERNAL TABLE')
          and privilege in ('SELECT', 'OWNERSHIP')
    ),

    -- base_assets にタグ、連絡先、公開可否を付与し、最終出力用の catalog_assets とする
    catalog_assets as (
        select
            assets.TABLE_ID::number                          as TABLE_ID,
            assets.DATABASE_NAME::varchar(255)               as DATABASE_NAME,
            assets.SCHEMA_NAME::varchar(255)                 as SCHEMA_NAME,
            assets.ASSET_NAME::varchar(255)                  as ASSET_NAME,
            assets.ASSET_TYPE::varchar(50)                   as ASSET_TYPE,
            assets.DESCRIPTION::varchar                      as DESCRIPTION,
            assets.ROW_COUNT::number                         as ROW_COUNT,
            assets.BYTES::number                             as BYTES,
            coalesce(tags.TAGS, array_construct())           as TAGS,
            contacts.CONTACT_STEWARD::varchar(255)           as CONTACT_STEWARD,
            contacts.CONTACT_SUPPORT::varchar(255)           as CONTACT_SUPPORT,
            contacts.CONTACT_ACCESS_APPROVAL::varchar(255)   as CONTACT_ACCESS_APPROVAL,
            contacts.CONTACT_SECURITY_COMPLIANCE::varchar(255)
                                                            as CONTACT_SECURITY_COMPLIANCE,
            (public_vis.ASSET_NAME is not null)::boolean     as IS_PUBLIC_VISIBILITY
        from base_assets as assets
        left join asset_tags as tags
            on  tags.DATABASE_NAME = assets.DATABASE_NAME
            and tags.SCHEMA_NAME   = assets.SCHEMA_NAME
            and tags.ASSET_NAME    = assets.ASSET_NAME
        left join asset_contacts as contacts
            on  contacts.DATABASE_NAME = assets.DATABASE_NAME
            and contacts.SCHEMA_NAME   = assets.SCHEMA_NAME
            and contacts.ASSET_NAME    = assets.ASSET_NAME
        left join public_visible_assets as public_vis
            on  public_vis.DATABASE_NAME = assets.DATABASE_NAME
            and public_vis.SCHEMA_NAME   = assets.SCHEMA_NAME
            and public_vis.ASSET_NAME    = assets.ASSET_NAME
    )
    select
        TABLE_ID,
        DATABASE_NAME,
        SCHEMA_NAME,
        ASSET_NAME,
        ASSET_TYPE,
        DESCRIPTION,
        ROW_COUNT,
        BYTES,
        TAGS,
        CONTACT_STEWARD,
        CONTACT_SUPPORT,
        CONTACT_ACCESS_APPROVAL,
        CONTACT_SECURITY_COMPLIANCE,
        IS_PUBLIC_VISIBILITY
    from catalog_assets
    ;

    return 'CATALOG.ASSETS refreshed';
end;
$$
;

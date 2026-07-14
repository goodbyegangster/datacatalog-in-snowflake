-- 「承認者」向けには紐づく Snowflake ユーザー情報を設定
create or replace contact <% sis_database_name %>.CONTACT."山田太郎"  -- noqa: LT02
    users = ('<% SNOWFLAKE_MY_USER_NAME %>')
    comment = '承認者'
;

--　「サポート」向けには、サポートチームのメーリングリストのアドレスを設定
create or replace contact <% sis_database_name %>.CONTACT."佐藤二郎"
    email_distribution_list = 'snowflake-supporto@example.jp'
    comment = 'サポートチーム'
;

-- 「スチュワード」向けには既存設計情報を参照できる URL を設定
create or replace contact <% sis_database_name %>.CONTACT."加藤三郎"
    url = 'https://www.snowflake.com/en/data-governance/data-stewardship/'
    comment = 'データ・スチュワード'
;

-- 「セキュリティとコンプライアンス」向けには連絡先にあたる情報は未設定
create or replace contact <% sis_database_name %>.CONTACT."鈴木四郎"
    comment = 'セキュリティ担当者'
;

-- CAMPAIGN_LEADS テーブルに contact を付与
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    set contact access_approval = <% sis_database_name %>.CONTACT."山田太郎"
;
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    set contact security_compliance = <% sis_database_name %>.CONTACT."鈴木四郎"
;
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    set contact steward = <% sis_database_name %>.CONTACT."加藤三郎"
;
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    set contact support = <% sis_database_name %>.CONTACT."佐藤二郎"
;

-- D_CAMPAIGN_LEADS テーブルに contact を付与
alter table <% sis_database_name %>.DATA_AD.D_CAMPAIGN_LEADS
    set contact access_approval = <% sis_database_name %>.CONTACT."山田太郎"
;
alter table <% sis_database_name %>.DATA_AD.D_CAMPAIGN_LEADS
    set contact security_compliance = <% sis_database_name %>.CONTACT."鈴木四郎"
;
alter table <% sis_database_name %>.DATA_AD.D_CAMPAIGN_LEADS
    set contact steward = <% sis_database_name %>.CONTACT."加藤三郎"
;
alter table <% sis_database_name %>.DATA_AD.D_CAMPAIGN_LEADS
    set contact support = <% sis_database_name %>.CONTACT."佐藤二郎"
;

-- PRODUCTS テーブルに contact を付与
alter table <% sis_database_name %>.DATA_SALES.PRODUCTS
    set contact access_approval = <% sis_database_name %>.CONTACT."山田太郎"
;
alter table <% sis_database_name %>.DATA_SALES.PRODUCTS
    set contact security_compliance = <% sis_database_name %>.CONTACT."鈴木四郎"
;
alter table <% sis_database_name %>.DATA_SALES.PRODUCTS
    set contact steward = <% sis_database_name %>.CONTACT."加藤三郎"
;
alter table <% sis_database_name %>.DATA_SALES.PRODUCTS
    set contact support = <% sis_database_name %>.CONTACT."佐藤二郎"
;

-- V_PRODUCTS ビューに contact を付与
alter view <% sis_database_name %>.DATA_SALES.V_PRODUCTS
    set contact access_approval = <% sis_database_name %>.CONTACT."山田太郎"
;
alter view <% sis_database_name %>.DATA_SALES.V_PRODUCTS
    set contact security_compliance = <% sis_database_name %>.CONTACT."鈴木四郎"
;
alter view <% sis_database_name %>.DATA_SALES.V_PRODUCTS
    set contact steward = <% sis_database_name %>.CONTACT."加藤三郎"
;
alter view <% sis_database_name %>.DATA_SALES.V_PRODUCTS
    set contact support = <% sis_database_name %>.CONTACT."佐藤二郎"
;

-- noqa: disable=LT02

define task {{ sis_database_name }}.TASK.REFRESH_CATALOG
    warehouse = {{ sis_warehouse_name }}
    schedule = 'USING CRON 0 */3 * * * UTC'
    comment = 'データカタログ・マスターテーブルの定期リフレッシュ' -- ACCOUNT_USAGE の遅延（最大数時間）に合わせて 3 時間ごとに実行
as
    call {{ sis_database_name }}.PROCEDURE.REFRESH_CATALOG()
;

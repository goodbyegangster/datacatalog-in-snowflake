-- compute pool を作成
create compute pool if not exists <% datacatalog_compute_pool_name %>
    min_nodes = 1
    max_nodes = 1
    instance_family = CPU_X64_XS
    auto_resume = true
    initially_suspended = false
    auto_suspend_secs = 60
    comment = 'Streamlit 向け'
;

-- compute pool 利用権限を sis owner role に付与
grant usage on compute pool <% datacatalog_compute_pool_name %>
    to role <% sis_owner_role_name %>
;

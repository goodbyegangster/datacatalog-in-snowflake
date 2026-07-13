-- compute pool を作成
create compute pool if not exists <% sis_compute_pool_name %>
    min_nodes = 1
    max_nodes = 1
    instance_family = CPU_X64_XS
    auto_resume = true
    initially_suspended = false
    auto_suspend_secs = 60
    comment = 'Streamlit 向け'
;

-- compute pool 利用権限向け access role を作成
create or alter role <% sis_role_name_prefix %>_ACCESS__CP__SIS__USAGE
    comment = 'コンピュートプール <% sis_compute_pool_name %> 向け利用権限'
;

grant usage on compute pool <% sis_compute_pool_name %>
    to role <% sis_role_name_prefix %>_ACCESS__CP__SIS__USAGE
;

-- 作成した access role を streamlit app owner role に付与
grant role <% sis_role_name_prefix %>_ACCESS__CP__SIS__USAGE
    to role <% sis_role_name_prefix %>_FUNC_SIS_OWNER
;

-- compute pool 向け access role 削除
drop role if exists <% sis_role_name_prefix %>_ACCESS__CP__SIS__USAGE
;

-- compute pool 削除
drop compute pool if exists <% sis_compute_pool_name %>
;

-- contact 削除
drop contact if exists <% sis_database_name %>.CONTACT."山田太郎"
;
drop contact if exists <% sis_database_name %>.CONTACT."佐藤二郎"
;
drop contact if exists <% sis_database_name %>.CONTACT."加藤三郎"
;
drop contact if exists <% sis_database_name %>.CONTACT."鈴木四郎"
;

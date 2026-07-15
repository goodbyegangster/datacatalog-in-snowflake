define warehouse {{ datacatalog_warehouse_name }}
    warehouse_type = 'STANDARD'
    warehouse_size = 'XSMALL'
    generation = '2'
    max_cluster_count = 1
    min_cluster_count = 1
    auto_suspend = 60
    auto_resume = TRUE
    initially_suspended = FALSE
    comment = 'datacatalog 向け'
;

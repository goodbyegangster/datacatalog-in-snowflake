# datacatalog-in-snowflake

## Overview

Snowflake 上のデータ資産を収集し、Streamlit in Snowflake で閲覧するデータカタログ。

## Requirements

- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) (`snow`)
- [uv](https://docs.astral.sh/uv/)（Python 3.11）
- GNU Make / Bash
- ACCOUNTADMIN 権限を持つ Snowflake アカウント

## Usage

(TODO)

## Directory Layout

```text
./
├── bootstrap/   # DCM 実行用ロール・DB を作成する SQL と Makefile
├── dcm/         # DCM プロジェクト（カタログのテーブル・手続き・ロール定義）
├── docs/        # 設計ドキュメント
├── streamlit/   # Streamlit in Snowflake アプリ
├── .env.example # 環境変数のテンプレート
└── README.md
```

## 作成 Snowflake ロールと責務

| Snowflake role name | 責務 |
| --- | --- |
| <dcm_project_owner_role_name> | dcm project 管理向け |
| <sis_role_name_prefix>_FUNC_DATACATALOG_OWNER | データカタログ用オブジェクト管理向け |
| <sis_role_name_prefix>_FUNC_SIS_OWNER | Streamlit APP 管理向け |
| <sis_role_name_prefix>_FUNC_SIS_READER | Streamlit APP 参照向け |

`dcm_project_owner_role_name` / `sis_role_name_prefix` は [.env](.env) で指定される値を利用。

## Related documentation

- [bootstrap/README.md](bootstrap/README.md): DCM 実行基盤の作成
- [dcm/README.md](dcm/README.md): カタログ用オブジェクトの管理
- [streamlit/README.md](streamlit/README.md): Streamlit アプリ
- [docs/design-view.md](docs/design-view.md): 画面設計
- [docs/design-search.md](docs/design-search.md): 検索機能の設計
- [docs/design-model.md](docs/design-model.md): カタログ・データモデル定義
- [docs/technical-guidelines.md](docs/technical-guidelines.md): Streamlit 実装規則

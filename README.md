# datacatalog-in-snowflake

## Overview

Snowflake 上のデータ資産を収集し、Streamlit in Snowflake で閲覧するデータカタログ。

Snowflake のメタデータ（説明・タグ・連絡先・統計・アクセス可能ユーザー）を集約したマスターテーブルを DCM で構築し、Streamlit アプリで検索・参照する。

## Requirements

- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) (`snow`)
- [uv](https://docs.astral.sh/uv/)（Python 3.11）
- GNU Make / Bash
- ACCOUNTADMIN 相当の権限を持つ Snowflake アカウント

## Usage

`.env` を作成し、各サブプロジェクトを順にデプロイする。詳細は各ディレクトリの README を参照。

```shell
cp .env.example .env   # 値を設定する

# 1. DCM 実行基盤（ロール / DB / external access）を作成
cd bootstrap && make setup

# 2. カタログ用オブジェクト（テーブル / procedure / task 等）をデプロイ
cd ../dcm && make init-manifest dcm-create dcm-deploy manual-deploy

# 3. Streamlit アプリをデプロイ
cd ../streamlit && make init-snowflake-yml init-secrets-toml init-settings-py deploy
```

デプロイ後に `CALL <SIS_DATABASE_NAME>.PROCEDURE.REFRESH_CATALOG()` を実行するとカタログが生成される。以降は task が定期更新する。

## Directory Layout

```text
./
├── bootstrap/   # DCM 実行用ロール・DB を作成する SQL と Makefile
├── dcm/         # DCM プロジェクト（カタログのテーブル・手続き・ロール定義）
│   ├── manual/  # DCM で管理できないオブジェクト（compute pool、tag など）
│   └── sources/ # DCM のオブジェクト定義とマクロ
├── docs/        # 設計ドキュメント
├── streamlit/   # Streamlit in Snowflake アプリ
├── .env.example # 環境変数のテンプレート
└── README.md
```

## Related documentation

- [bootstrap/README.md](bootstrap/README.md): DCM 実行基盤の作成
- [dcm/README.md](dcm/README.md): カタログ用オブジェクトの管理
- [streamlit/README.md](streamlit/README.md): Streamlit アプリ
- [docs/design-view.md](docs/design-view.md): 画面設計
- [docs/design-search.md](docs/design-search.md): 検索機能の設計
- [docs/design-model.md](docs/design-model.md): カタログ・データモデル定義
- [docs/technical-guidelines.md](docs/technical-guidelines.md): Streamlit 実装規則

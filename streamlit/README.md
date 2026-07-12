# streamlit

## Overview

データカタログを表示する Streamlit in Snowflake アプリ。

`st.navigation` によるマルチページ構成（ページ本体は `views/`）で、データ資産・カラム・ユーザーを検索して参照する。元データは Snowflake 上のカタログ用マスターテーブル。

## Requirements

- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) (`snow`)
- [uv](https://docs.astral.sh/uv/)（Python 3.11）
- GNU Make / Bash

## Usage

親ディレクトリの `.env` から値を読み込む。`make init-*` で設定ファイルを生成してから起動・デプロイする。`make help` でサブコマンドを確認できる。

```shell
# .env から設定ファイルを生成（settings.py / snowflake.yml / secrets.toml）
make init-snowflake-yml init-secrets-toml init-settings-py

# ローカルで起動
make run_local

# Snowflake へデプロイ
make deploy
```

## Directory Layout

```text
streamlit/
├── .config/                  # snowflake.yml 用の JSON スキーマ
├── .streamlit/
│   └── secrets.toml.template # ローカル接続情報のテンプレート
├── catalog/                  # カタログ DataFrame の schema / provider
├── components/               # 再利用 UI（left / detail pane、行選択テーブル等）
├── infrastructure/           # Snowflake 接続など外部基盤との接続
├── logic/                    # 検索 / グラフ生成などの純粋な業務ロジック
├── runtime/                  # session_state / ログインユーザーなど実行時状態
├── scripts/                  # .env から設定ファイルを生成するスクリプト
├── styles/                   # 全ページ共通 / ページ固有 CSS と loader
├── views/                    # マルチページの各ページ（データ資産 / ユーザー / グラフ）
├── Makefile
├── pyproject.toml            # 依存定義（streamlit[snowflake]）
├── settings.py.template      # 表示 / 検索スコープ定義のテンプレート
├── snowflake.yml.template    # SiS デプロイ定義のテンプレート
├── streamlit_app.py          # エントリポイント
└── uv.lock
```

`settings.py` / `snowflake.yml` / `.streamlit/secrets.toml` は `make init-*` が `.env` から生成する（gitignore 対象）。

## Related documentation

- [../docs/design-view.md](../docs/design-view.md): 画面設計
- [../docs/design-search.md](../docs/design-search.md): 検索機能の設計
- [../docs/design-model.md](../docs/design-model.md): カタログ・データモデル定義
- [../docs/technical-guidelines.md](../docs/technical-guidelines.md): 実装規則

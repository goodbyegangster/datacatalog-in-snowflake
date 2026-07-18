# streamlit

## Overview

Snowflake カタログを検索・参照する Streamlit in Snowflake アプリ。

`st.navigation` によるマルチページ構成で、データ資産・ユーザー・ロール継承グラフを表示する。
元データは Snowflake 上のカタログ用マスターテーブル、または fake provider から取得する。

## Requirements

- Snowflake CLI (`snow`)
- uv（Python 3.11）
- GNU Make / Bash

## Usage

親ディレクトリの `.env` から設定ファイルを生成してから起動する。Snowflake 接続なしで画面確認する場合は fake catalog を使う。

`settings.py` は生成物であり、編集元は `settings.py.template` と親ディレクトリの `.env`。
表示 / 検索スコープを変更する場合は、`settings.py` ではなく編集元を更新してから再生成する。

```shell
make init-snowflake-yml init-secrets-toml init-settings-py
make run_fake
make run_test
```

Snowflake へデプロイする場合は、`snowflake.yml` と Snowflake CLI の接続設定を用意してから実行する。

```shell
make deploy
```

## Directory Layout

```text
streamlit/
├── .config/                  # snowflake.yml 用 JSON schema
├── .streamlit/               # Streamlit config / secrets template
├── catalog/                  # catalog schema / provider facade / provider 実装
│   └── providers/            # fake provider / Snowflake provider
├── components/               # page component
│   ├── assets/               # データ資産 page の search / results / detail
│   ├── common/               # component 共通 helper
│   └── users/                # ユーザー page の search / results / detail
├── infrastructure/           # Snowflake 接続など外部基盤との接続
├── logic/                    # search / graph の純粋ロジック
│   ├── graph/                # ロール継承 graph の経路探索 / DOT 生成
│   └── search/               # assets / users / common に分けた検索ロジック
├── runtime/                  # session_state key / navigation / widget state / ログインユーザー情報
├── scripts/                  # .env から設定ファイルを生成する script
├── styles/                   # 全ページ共通 / ページ固有 CSS と loader
├── tests/                    # pytest
│   ├── app/                  # Streamlit AppTest
│   ├── fixtures/             # fake catalog 用 test data
│   └── unit/                 # search / graph の unit test
├── views/                    # Streamlit page 本体
│   └── common/               # page 共通 helper
├── Makefile
├── pyproject.toml            # 依存定義
├── settings.py.template      # 表示 / 検索スコープ定義の template
├── snowflake.yml.template    # SiS deploy 定義の template
├── streamlit_app.py          # entry point
└── uv.lock
```

`snowflake.yml` / `.streamlit/secrets.toml` も `make init-*` が `.env` から生成する。

## Related Documentation

- [../docs/design-view.md](../docs/design-view.md): 画面設計
- [../docs/design-search.md](../docs/design-search.md): 検索機能の設計
- [../docs/design-model.md](../docs/design-model.md): カタログデータモデル
- [../docs/technical-guidelines.md](../docs/technical-guidelines.md): 実装規則

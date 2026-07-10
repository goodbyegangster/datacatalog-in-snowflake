# dcm

## Overview

データカタログのオブジェクトを [DCM プロジェクト](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects) として宣言的にデプロイする。

`sources/` にテーブル・手続き・ロール・スキーマ・タグ・タスク・ウェアハウスの定義を置く。DCM で管理できないオブジェクト（compute pool、contact、masking policy、tag）は `manual/` の SQL で個別にデプロイする。

## Usage

親ディレクトリの `.env` から値を読み込む。`make help` でサブコマンドを確認できる。

```shell
# .env から manifest.yml を生成
make init-manifest

# プロジェクトを作成し、差分を確認してデプロイ
make dcm-create
make dcm-plan
make dcm-deploy

# DCM で管理できないオブジェクトをデプロイ
make manual-deploy
```

削除は `make dcm-purge`（オブジェクト）、`make dcm-drop`（プロジェクト）、`make manual-remove`（手動デプロイ分）を使う。

## Directory Layout

```text
dcm/
├── manual/               # DCM で管理できないオブジェクト
│   ├── deploy/           # compute pool / contact / masking policy / tag
│   └── remove/
├── sources/
│   ├── definitions/      # DCM が管理するオブジェクト定義
│   └── macros/           # 定義から参照するマクロ
├── Makefile
├── manifest.yml          # make が生成（gitignore 対象）
├── manifest.yml.template # manifest.yml の元テンプレート
└── README.md
```

## Related documentation

- [Supported object types in DCM Projects](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-supported-entities)
- [../docs/design-model.md](../docs/design-model.md): カタログテーブルの定義とデータソース

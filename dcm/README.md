# dcm

## Overview

データカタログのオブジェクトを [DCM プロジェクト](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects) として宣言的にデプロイする。

`sources/definitions/` にデータベース・スキーマ・手続き・ロール・タスク・ウェアハウスの定義を置く。DCM で管理できないオブジェクト（compute pool、contact、masking policy、tag）は `manual/` の SQL で個別にデプロイする。

いずれの定義も、カタログ本体向けの `datacatalog/` と動作確認用の `sample/` に分かれる。

## Usage

親ディレクトリの [.env](../.env) から値を読み込む。`make help` でサブコマンドを確認できる。

```shell
# .env から manifest.yml を生成する
make init-manifest-yml

# プロジェクトを作成し、差分を確認してデプロイする
make dcm-create
make dcm-plan
make dcm-deploy

# DCM で管理できないオブジェクトをデプロイする
make manual-deploy-catalog
make manual-deploy-sample
```

## Directory Layout

```text
dcm/
├── manual/                   # DCM で管理できないオブジェクト
│   ├── deploy/               # datacatalog/ と sample/ に分かれる
│   └── remove/
├── scripts/
│   └── init-manifest-yml.sh  # .env から manifest.yml を生成する
├── sources/
│   ├── definitions/          # DCM が管理するオブジェクト定義（datacatalog/ と sample/）
│   └── macros/               # 定義から参照するマクロ
├── Makefile
├── manifest.yml              # make が生成する（gitignore 対象）
├── manifest.yml.template     # manifest.yml の元テンプレート
└── README.md
```

## Related documentation

- [Supported object types in DCM Projects](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-supported-entities)
- [../docs/design-model.md](../docs/design-model.md): カタログテーブルの定義とデータソース

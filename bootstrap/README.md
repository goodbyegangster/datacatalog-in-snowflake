# bootstrap

## Overview

DCM プロジェクトの実行に必要な Snowflake オブジェクトを作成する。

## Directory Layout

```text
bootstrap/
├── sql/
│   ├── setup.sql   # ロール・DB・external access を作成
│   └── remove.sql  # setup.sql が作成したオブジェクトを削除
├── Makefile
└── README.md
```

## Related documentation

- [../README.md](../README.md): プロジェクト全体のデプロイ手順

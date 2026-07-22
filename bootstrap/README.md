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

## Remove

`make remove` は DCM プロジェクトで作成したオブジェクトを削除してから実行する。
DCM 側のオブジェクトが残った状態で datacatalog owner role を削除すると、残存オブジェクトの所有権が `make remove` の実行ロールへ移る。

## Related documentation

- [../README.md](../README.md): プロジェクト全体のデプロイ手順

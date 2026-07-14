# todo-memo

## Snowflake ロールを分離

以下の責務で Snowflake ロールを分離する。

- dcm object owner / 実行ロール
- datacatalog owner
- sis app owner
- sis app reader

## サンプルオブジェクト用の専用データベースを用意

datacatalog 向けとサンプルデータ向けを、データベース単位で分ける。
=> これは sample であることが分かるスキーマ名にすれば良し。データベース単位ではわけない。

## Snowflake タスクの実行ロール

ACCOUNTADMIN で実行ができるようにする。

- タスク実行ロールに `grant manage grants on account to role <% dcm_project_owner_role_name %>` を付与すればOK

## 実行環境

| | 実行環境 | Snowflake 接続 |
| --- | --- | --- |
| 1 | Snowflake Container Runtime | あり |
| 2 | ローカル | あり |
| 3 | ローカル | なし |

### 改善点

- assets の search で、database / schema が DISPLAY_SCOPES 依存のため、Fake で動作が変になる

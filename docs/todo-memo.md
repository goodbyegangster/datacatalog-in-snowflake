# todo-memo

## 実行環境

| | 実行環境 | Snowflake 接続 |
| --- | --- | --- |
| 1 | Snowflake Container Runtime | あり |
| 2 | ローカル | あり |
| 3 | ローカル | なし |

### 改善点

- assets の search で、database / schema が DISPLAY_SCOPES 依存のため、Fake で動作が変になる

# todo-codex

## Step 4 前：カタログ生成 SQL レビュー Findings

対象:

- `dcm/sources/definitions/procedure/refresh_assets.sql`
- `dcm/sources/definitions/procedure/refresh_access_edges.sql`
- `dcm/sources/definitions/procedure/refresh_asset_visibility.sql`

### 1. `GRANTS_TO_ROLES.GRANTED_TO` の値

- 解決済み
- 当初レビューでは、Snowflake 公式 docs の記載を根拠に `ACCOUNT ROLE` / `DATABASE_ROLE`
  を想定した。
- ただし実環境では `ROLE` が正しい値として確認済み。
- よって、現 SQL の `granted_to in ('ROLE', 'DATABASE_ROLE')` は現時点では修正不要。
- 今後も実環境の `select distinct granted_to ...` を正とする。

### 2. asset grant / PUBLIC 判定の object type が狭い

- 解決済み
- 当初 SQL は `granted_on in ('TABLE', 'VIEW', 'MATERIALIZED VIEW')` のみを対象にしていた。
- `EXTERNAL TABLE` は実環境確認により追加済み。
- 一方、`ASSETS.ASSET_TYPE` は以下も表示対象になり得る。
  - `DYNAMIC TABLE`
  - `ICEBERG TABLE`
  - `HYBRID TABLE`
  - `EVENT TABLE`
  - `TEMPORARY TABLE`
- そのため、動的テーブル等について `ACCESS_EDGES.ROLE_TO_ASSET` や
  `ASSETS.IS_PUBLIC_VISIBILITY` が欠落する可能性がある。
- 要対応候補:
  - 実環境で `grants_to_roles.granted_on` の値を確認する。
  - `ASSETS` に載せる asset type と grant 収集対象を揃える。

### 3. `ASSET_VISIBILITY` の `USER_ROLES` / `ASSET_ROLES` の対応関係

- 現 SQL は `USER_NAME + TABLE_ID` 単位で以下を別々に集約している。
  - `array_agg(distinct r.first_role)` as `USER_ROLES`
  - `array_agg(distinct ag.role_node)` as `ASSET_ROLES`
- これにより、「どの user 直下 role が、どの asset 直前 role へ到達したか」という
  対応関係は保持されない。
- Step 4 の graph 導線でこの対応関係が必要か再検討する。
- 要説明:
  - 例を使って、なぜ対応関係が潰れるのか整理する。
- 要対応候補:
  - `USER_NAME, TABLE_ID, USER_ROLE, ASSET_ROLE` 粒度の行にする。
  - もしくは `ROLE_PATHS` のような object array を追加する。
  - 現在の UI で単なる要約表示だけに使うなら、現形式でも一旦許容可能。

### 4. asset tags の `domain = 'TABLE'` 固定

- `refresh_assets.sql` では asset tag の収集が `TAG_REFERENCES.DOMAIN = 'TABLE'` 固定。
- view / materialized view / dynamic table 等に付与されたタグの `DOMAIN` が別値なら欠落する。
- すぐには確認できないため保留。
- 要確認:
  - 実環境で `select distinct domain from snowflake.account_usage.tag_references` を確認する。

### 5. recursive CTE の `union all` による中間行増加

- `refresh_asset_visibility.sql` の `reach` は `union all` でロール継承を辿る。
- Snowflake は循環ロールを禁止しているため無限ループにはなりにくい。
- ただし diamond 型のロール継承では、同じ role へ複数経路で到達し、中間行が膨らむ可能性がある。
- 要説明:
  - 例を使って diamond 型でなぜ行が増えるのか整理する。
- 要対応候補:
  - `reach` の途中または後段で重複排除する。
  - 規模が小さいうちは、最終集約の `distinct` で許容する判断もあり。

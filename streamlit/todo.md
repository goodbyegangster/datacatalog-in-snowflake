# Streamlit in Snowflake 実装 TODO

データカタログ SiS アプリの実装計画と進捗を管理する。設計の根拠は
[../docs/design-view.md](../docs/design-view.md) /
[../docs/design-search.md](../docs/design-search.md) /
[../docs/design-model.md](../docs/design-model.md) /
[../docs/technical-guidelines.md](../docs/technical-guidelines.md) を参照。

進捗記号: `[ ]` 未着手 / `[~]` 実装中 / `[x]` 完了

## 開発方針（進め方）

**画面ファースト（ウォーキングスケルトン＝縦スライス）** で進める。依存順（下位 lib から積む）
と開発順は分け、早い段階で動く画面を見ながら肉付けする。

- `lib` は最初から完成させない。**関数シグネチャ（モックと本実装の境界）を先に決め**、中身はモックで開始。
- 「Step」= 実際に手を動かす順序。「Phase」= 成果物カテゴリ（下部の一覧）。

### 開発 Step（この順で進める）

- [x] **Step 1. 骨組みを画面に通す**：`streamlit_app.py` ＋ `views/` 2 枚を **モックデータ**で描画。
  sidebar 検索・`st.dataframe`・行選択・タブが出る状態にする。`lib/connection` `lib/catalog`
  はダミー（固定 DataFrame）で可。→ AppTest でスモーク済み。
- [x] **Step 2. モックを本物へ差し替え**：`lib/connection`（ローカル secrets.toml 接続）→
  `lib/catalog`（実カタログ表ロード）を実装し差し替え。`make run_local` で実データ表示を確認済み
  （両ページとも実データ表示 OK）。
- [x] **Step 3. 検索を肉付け**：`lib/search` → 検索 UI を機能追加。
  - [x] Step 3a. データ資産検索（フリーワード / 階層 / 種別 / タグ / AND・OR トグル / 初期空欄＋インタラクティブ検索）。AppTest 検証済み。
  - [x] Step 3b. ユーザー検索（ログインユーザーのみ表示トグル＋フリーワード）。AppTest 検証済み。
- [x] **Step 4. 詳細・グラフを肉付け**：`lib/graph` → ロール継承グラフ専用ページを追加。
  - Step 4 開始時に、グラフ導線と合わせて以下の表示形式を再設計する。
    - `assets.py` 詳細ペインの「ユーザー」タブ。
    - `users.py` 詳細ペインの「閲覧可能なデータ資産」一覧。
    - 直接付与ロールと可視性一覧を、どの粒度でペア表示するか。
    - graph 表示ボタンを、どの行・どの選択単位（ユーザー / 資産 / 起点ロール）に紐づけるか。
  - 一覧は単なる参照表ではなく、ロール継承グラフページの起点選択 UI として扱う。
- [x] **Step 5. 仕上げ**：ページ間遷移・エラー表示・空状態・ソート/一覧表示の詰め。
- [ ] **Step 6. テスト**：純関数（search/graph）の pytest ＋ スモーク。行選択 e2e は後続。

各 Step で対応する成果物は下部 Phase 一覧を参照（進捗はこの Step 側で管理）。

## Phase 0. 前提の訂正

- [x] settings.py / settings.py.template：`DISPLAY_ASSETS`→`DISPLAY_SCOPES`、`CATALOG_DATABASE`→`CATALOG_LOCATION`（TypedDict 名含む）
- [x] docs/design-model.md：ER 図 `MASKING_POLICY`→`MASKING_POLICY_NAME`
- [x] docs/design-view.md / dcm/README.md：`design-catalog-data.md`→`design-model.md`

## Phase 1. lib 層（ロジック）

追加依存なし方針。グラフは `st.graphviz_chart` に DOT 文字列を渡す。pytest を dev 依存へ追加。

- [ ] `lib/connection.py`：`get_session()`。SiS は `get_active_session()`、ローカルは secrets.toml。UI から接続処理を書かず 1 箇所に集約。注入可能にする。
- [ ] `lib/catalog.py`：data access。各カタログ表を `@st.cache_data(ttl=3600)` で一括ロードし DataFrame 化。
  - 対象：ASSETS / COLUMNS / USERS / TAGS / ACCESS_EDGES / ASSET_VISIBILITY。資産は `DISPLAY_SCOPES` で絞る。`SNOWFLAKE.ACCOUNT_USAGE` や本体には触れない。
- [ ] `lib/search.py`：純関数。フリーワード解析（部分一致・大小無視・` OR `/` AND `）、資産フィルタ（カテゴリ1 AND (2 <トグル> 3 <トグル> 4)）、ユーザーフィルタ。
- [ ] `lib/graph.py`：`ACCESS_EDGES` から user↔asset の経路のみを抽出し DOT 生成（多段継承・DB ロール修飾・PUBLIC 除外）。
- [ ] `lib/state.py`：`st.session_state` キー定数・名前空間ヘルパ（`asset_` / `user_` / `search_`）。
- [ ] pytest 導入（`pyproject.toml` dev 依存）。

## Phase 2. components 層（再利用 UI）

- [ ] `components/asset_search.py`：データ資産 sidebar。4 カテゴリ＋カテゴリ間 AND/OR トグル（初期 AND）。DB→スキーマ連動プルダウン（DB `on_change` でスキーマ選択を未選択へリセット）。
- [ ] `components/user_search.py`：ユーザー sidebar。ログインユーザーのみ表示トグル（`IS_VISIBLE_ONLY_SELF_USER=True` で ON 固定）＋フリーワード。
- [ ] `components/result_table.py`：`st.dataframe(selection_mode="single-cell", on_select="rerun")` による全件表示。選択 ID を session_state へ。
- [ ] `components/asset_detail.py`：資産 detail pane。ヘッダ（名前/説明/階層/種別 badge/タグ badge/PUBLIC badge）＋タブ（カラム / 連絡先 / 統計 / ユーザー）。カラム / 連絡先 / 統計は `st.dataframe` 表示。ユーザータブは行選択と明示ボタンでロール継承グラフページへ遷移。
- [ ] `components/user_detail.py`：ユーザー detail pane。ヘッダ（名前/表示名/タイプ/ステータス）＋付与ロール／閲覧可能資産ペア＋ロール継承グラフページへの導線。

## Phase 3. views 層／エントリ

- [x] `views/assets.py`：検索 UI は sidebar、行選択で main を 1:3 分割。ソート DB→スキーマ→名前。初期一覧は空欄。検索条件ありで 0 件の場合は空状態メッセージを表示。
- [x] `views/users.py`：検索 UI は sidebar、行選択で main を 1:3 分割。ソート 名前。初期は全ユーザー表示。
- [x] `views/graph.py`：対象ユーザー→対象データ資産のロール継承 graph を全幅で表示。
- [x] `streamlit_app.py`：`st.set_page_config`・`st.navigation` + `st.Page`（ASCII ファイル名・日本語タイトル）。
- [x] ページ間遷移：`st.session_state` に選択 ID を積み `st.switch_page`（`asset_selected_table_id` / `user_selected_name`）。
  - ブラウザの「戻る」ボタンによる状態復元は保証しない。
  - URL query params はページ間状態管理に利用しない。
  - 遷移操作は `st.dataframe` の暗黙的なセルクリックではなく、明示的なボタンに寄せる。
- [x] エラー：main pane に日本語 `st.error`、traceback は fake mode のみ表示。UI 日本語固定。検索条件未入力は案内表示、検索結果 0 件は空状態メッセージを表示。

## Phase 4. テスト／確認

- [ ] `tests/test_search.py`：フリーワード AND/OR・階層/種別/タグ・カテゴリ間 AND/OR トグル。
- [ ] `tests/test_graph.py`：経路抽出（多段継承・DB ロール・PUBLIC 除外）。
- [ ] スモーク：`streamlit run` 起動確認 or `streamlit.testing.v1.AppTest`。
- [ ] （後続）行選択 `on_select` の実描画は Playwright でクリティカルフローのみ。

## 未確定・要議論の論点

この後の議論で確定する項目（決まり次第、必要なら `docs/design-implementation.md` に切り出す）。

- ~~ナビゲーション実装~~：**確定済み** — `st.navigation` + `st.Page`（`views/` に ASCII 名、タイトルは日本語）。
- カタログ表のロード単位とキャッシュキー設計（資産の DISPLAY_SCOPES 事前絞り込みを SQL/Python どちらで行うか）。
- 検索ロジックの厳密仕様（フリーワードのトークン分割規則、カラムヒット時の資産包含、空選択時の扱い）。
- グラフ経路抽出アルゴリズムの詳細（`ASSET_VISIBILITY` と `ACCESS_EDGES` の使い分け、経路探索の実装）。
- テスト戦略の粒度（pytest 中心・AppTest/Playwright の範囲）。

## 既知の制約 / 保留メモ

- **検索アコーディオンの開閉**：`st.expander` を採用（Streamlit 標準の範囲に留める方針）。
  現状は「その分類で選択がある場合は初期表示を開く」だけを指定し、手動開閉状態は
  Streamlit に委ねる。
  - 完全に決定論的な開閉が必要になった場合は、`st.expander` をやめて session_state 管理の
    自前アコーディオン（見出しトグルボタン＋条件付き表示）へ切り替える必要がある。今回は見送り。

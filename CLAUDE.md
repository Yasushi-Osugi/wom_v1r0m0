# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What is WOM

**WOM (Weekly Operation Model)** は週次PSI（Production/Sales/Inventory）を基本単位とするE2Eサプライチェーン計画・シミュレーションツール。Python \+ tkinter GUI。

- 起動: `python -m main`（GUIモード）/ `python -m main --cli`（ヘッドレス）  
- 現バージョン: v1r0m3（branch: `wom-v1r0m3`）  
- 適用事例: Japanese Rice SC（`data/sample/rice-japan-2027-2028/`）、iPhone Global SC（`data/sample/iphone-2027-2029/`）

---

## Commands

\# GUI起動（通常）

python \-m main

\# CLIシミュレーション

python \-m main \--cli \--start-week 2027-W01 \--num-weeks 156

\# テスト実行

python \-m pytest tests/ \-v

\# 単一テスト

python \-m pytest tests/test\_ppc\_vertical\_slice.py \-v

\# PPC CLIスタンドアロン

python \-m wom.ppc

依存: `pip install tkintermapview pandas numpy matplotlib openpyxl networkx pytest`

---

## Architecture

### 3層モデル

Physical Layer  ←→  Planning Layer  ←→  Management Layer

(実ノード/地図)      (SCTree \+ PSI)       (KPI / PPC / P\&L)

### Planning Engineの実行順序（`wom/gui/app.py: _run_planning_engine`）

1\. demand\_forecast.csv → 需要ロット生成（lot\_generator.py）

2\. sc\_tree\_master.csv → SCTree構築（sc\_tree\_builder.py）

3\. HOOK\_PRE\_PLAN（プラグイン処理: HarvestBatch等）

4\. BackwardPlanner.run(prod\_nm)  ← 需要をleaf\_outから逆伝播

5\. HOOK\_POST\_BACKWARD

6\. copy\_demand\_to\_supply()       ← psi4demand → psi4supply コピー

7\. HOOK\_POST\_COPY

8\. ForwardPlanner.run(prod\_nm)   ← 供給能力制約を適用、CO生成

9\. HOOK\_POST\_FORWARD / HOOK\_POST\_PLAN

10\. sc\_tree\_to\_planning\_df()     ← SCTree → DataFrame（KPI用）

11\. PPC engine自動実行

### コアデータ構造: PlanNode（`wom/model/plan_node.py`）

各ノードが保持するPSIバケット：

psi4demand\[week\_idx\]\[bucket\]  \# BackwardPlannerが書く

psi4supply\[week\_idx\]\[bucket\]  \# ForwardPlannerが書く

\# bucket定数

S  \= 0  \# Sales / 出荷

CO \= 1  \# Carry Over（繰越需要）

I  \= 2  \# Inventory（期末在庫）

P  \= 3  \# Purchase/Production（入荷計画）

### SCTree構造（`wom/model/sc_tree.py`）

InBound (supply side)          OutBound (demand side)

leaf\_in                        supply\_point (bridge/root)

  └─ MOM(tier=0)  ────────────▶  DAD(tier=0)

       └─ tier-1  ←─ Bridge ─▶     └─ DC

            └─ leaf\_in               └─ leaf\_out (sales channel, region必須)

**重要な設計上の注意：**

- 【v1r0m4で更新】以前は「OutBound DADノードは需要アンカー型ロット方式のため`psi4supply[w][I]`は常に0」としていたが、これは**Lot_ID identity-matching方式の導入（下記バグ修正履歴参照）により解消済み**。現在はOutBound DADノードでも`buffering_stock_flag=1`（is_decoupling）かつ`ss_days`が設定されていれば、実際に`psi4supply[w][I]`にSS_days分の安全在庫バッファが積み上がる（Cookie_Import: DC_Import_Bufferで実証済み）。
- 実際のバッファ在庫はInBound MOMノード・OutBound DADノードのどちらでも、is_decouplingノードなら`psi4supply[w][I]`に蓄積されうる（v1r0m4以降）。
- `Buffer Stock (DAD)` はWOMモデル用語として正しい（OutBound decoupling point）  
- GUIのBuffer Stockチャートは実装上MOMノードのデータを参照しているが、DADノードのIも今後表示対象に含める余地がある（v1r0m4時点では未対応、次回検討事項）。

### node\_type一覧

| node\_type | 側 | 役割 |
| :---- | :---- | :---- |
| `supply_point` | OutBound root | InBound/OutBound bridge |
| `dad` | OutBound | 倉庫・DC（Demand Anchored Decoupling point） |
| `leaf_out` | OutBound leaf | 販売チャネル（region必須） |
| `mom` | InBound root | 製造拠点・産地集荷センター（Mother of Manufacturing） |
| `leaf_in` | InBound leaf | 原材料・稲作田 |

### プラグインシステム（`wom/plugins/__init__.py`）

`HookBus`経由でPlanning Engineに割り込む：

HOOK\_PRE\_PLAN      \# sc\_tree構築後、計画ループ前

HOOK\_POST\_BACKWARD \# BackwardPlanner完了後

HOOK\_POST\_COPY     \# demand→supplyコピー後

HOOK\_POST\_FORWARD  \# ForwardPlanner完了後

HOOK\_POST\_PLAN     \# 全製品計画完了後

**組み込みプラグイン：**

- `HarvestBatchPlugin` — 収穫期バッチ生産（seasonal supply spike）  
- `HolidayCalendarPlugin` — 長期休暇の能力閉鎖・需要変動（holiday\_calendar.csv）  
- `CapacityOverridePlugin` — cap\_override.csvによる能力上書き  
- `DemandSmoothingPlugin` — 3週移動平均需要平準化
- `BufferingStockOptimizerPlugin`（v1r0m4〜、HOOK\_POST\_BACKWARD） — decouple\_optimizer\_config.csvでSKUごとにON/OFF、有効時はOutBoundのbuffering\_stock\_flag（is\_decoupling）をコスト最適・サービスレベル制約付きの配置に自動上書き（詳細は本ファイル下部「BufferingStockOptimizerPlugin」参照）

新プラグインは `plugin_base.py` の `WOMPlugin` を継承し、`ALL_BUILTIN_PLUGINS` に追加する。

### PPC（Profit Price Cost）エンジン（`wom/ppc/`）

Planning Engine完了後に自動実行（`_run_ppc_from_planning`）。

- 入力CSV: `ppc_market_price.csv`, `ppc_supplier_cost.csv`, `ppc_node_cost_rule.csv`  
- 計算: Revenue → COGS → Gross Profit → Profit Zone  
- 結果: GUIのPPCタブに表示

### Landed Cost（`wom/engine/landed_cost.py`）

関税・為替・輸送費のシナリオ比較エンジン（Phase 1実装済み）。

- `edge_cost_master.csv`: シナリオ別ルートコスト（Base/FreightUp/DriverShortage等）  
- `route_master.csv`: SKU×regionのルート割り当て  
- ManagementタブのTariff & FX パネルに表示  
- Phase 1制約: ルート間の按分は単純平均（出荷量加重はPhase 2）

---

## Master CSV スキーマ（モデルフォルダ必須ファイル）

| ファイル | 主キー | 用途 |
| :---- | :---- | :---- |
| `sku_master.csv` | sku\_id | 製品定義 |
| `demand_forecast.csv` | sku\_id, region, week | 週次需要予測 |
| `node_master.csv` | node\_id | ノード定義（lat/lon/node\_type） |
| `sc_tree_master.csv` | node\_name, product\_name | SCTree構造定義 |
| `capacity_plan.csv` | node\_id, sku\_id, week | 週次能力制約 |
| `lane_assignment.csv` | sku\_id, leaf\_out\_node | InBound割り当てルール |
| `node_cost_master.csv` | node\_id, sku\_id | ノード別コスト |
| `edge_cost_master.csv` | scenario, src\_region, dst\_region | 輸送コストシナリオ |
| `route_master.csv` | sku\_id, region | SKU×regionルート |
| `holiday_calendar.csv` | node\_id, week | 長期休暇カレンダー |
| `inventory_master.csv` | node\_id, sku\_id | 期初在庫 |

`node_master.csv`の`node_type`はWorldMapの`_MAP_NODE_STYLE`と整合させること：

- `procurement` → オレンジ（玄米保管・SP\_Kome等）  
- `mother_plant` → 紫（産地集荷センター等）  
- `sku_supplier` → 緑（稲作田・サプライヤー）  
- `region_dc` → 青（精米センター・DC）  
- `marketing` → 赤（小売チャネル）

`sc_tree_master.csv`の`node_type`はWOMモデル用語（`mom`/`dad`/`leaf_in`/`leaf_out`/`supply_point`）を使用。上記とは別体系。

---

## GUI構造（`wom/gui/app.py`）

約3900行の単一ファイル。主要パネルクラス：

| クラス | タブ | 役割 |
| :---- | :---- | :---- |
| `ChartPanel` | Charts | Buffer Stock/Harvest Input/Fill Rate等 |
| `WorldMapPanel` | World Map | tkintermapviewベースの地図（起動時初期タブ） |
| `NetworkPanel` | Network | NetworkXによるHammockグラフ |
| `ManagementPanel` | Management | KPI・PPC・Tariff\&FX |
| `PPCPanel` | PPC | Profit Zone可視化 |

**WorldMapPanel:** 起動時の初期タブ。`_render_nodes()`後に`self.after(200, self._fit_to_nodes)`でノード群にauto-zoom。`fit_bounding_box()`またはフォールバック`set_position()+set_zoom()`。

**Planning Engine完了後のフロー（`_on_planning_done`）：**

1. `NetworkPanel.load_planning_tree(sc_tree)`  
2. `ChartPanel.load_sc_tree(sc_tree)` → Buffer Stock/Harvest Inputチャートが有効化  
3. `ChartPanel.load(mgr)` → 既存チャートデータ更新  
4. `_run_ppc_from_planning(sc_tree)` → PPC自動実行

---

## v1r0m3の開発方針

- v1r0m2（branch: `wom-v1r0m2`）をベースラインとして保存済み  
- v1r0m3では **MOM Constrained Demand Allocation**（BackwardPlannerでのMOM cap_hardクリップ + CO前倒し）を実装  
- `data/sample/iphone-2027-2029/` を参照・拡充する  
- コード変更はすべて `wom-v1r0m3` ブランチで行い、GitHubへpushする  
- GitHub: `https://github.com/Yasushi-Osugi/wom_v1r0m0.git`

---

## 設計上の制約・注意事項

- `app.py`はLinuxのbashでは約172KB付近で切り捨てられる。構文チェックはWindowsで行うこと: `python -c "import ast; ast.parse(open('wom/gui/app.py').read())"`
  **重要（2026-07-07追記、v1r0m5セッションで再確認・範囲を拡大）**: この切り捨ては`cat`/`python open()`だけでなく**`git`コマンド自体**（Linux bashマウント経由で実行した場合）にも及ぶことを確認済み。`git diff`/`git status`がapp.pyの末尾（`_on_ppc_done`以降、`launch()`まで）を「削除」として表示するが、これは実際の変更ではなく、bashマウント越しにgitが読んだファイルが切り捨てられているために生じる幻影。しかも**この現象はapp.py（約170KB超級）だけでなく、CLAUDE.md自体（57KB程度、760行）でも再現した**——`wc -l`がgit HEAD blobより少ない行数を返し、`git diff -w`が実際には発生していない大量の削除を表示した。つまり閾値は「約172KB」という固定サイズではなく、bashマウントのセッション内での累積読み込み量や再読込みタイミングに依存する可能性が高く、**編集した全てのファイルについて`git`をLinux bash経由で実行するのは危険**と考えるべき。
  **対策**: WOMのコード・ドキュメントに変更を加えたセッションでは、`git add`/`git commit`/`git push`は必ずユーザー自身のWindows側ターミナルで実行してもらうこと。Claude側のbashツールで`git add`/`git commit`を実行するのは絶対に避ける（ステージされる内容が切り捨てられた壊れたバージョンになる恐れがあるため）。`git diff`/`git status`をClaude側で覗き見て「変更点の要約」を作ること自体は無害だが、その差分表示を鵜呑みにせず、真に受けるべきは常にRead toolで読んだ内容（Windows側の実ファイル）である。
- `sc_tree_to_planning_df()`は`leaf_out`ノードのみを処理するため、DAD在庫はKPI DataFrameに現れない  
- `fit_bounding_box()`はtkintermapview \>= 0.3が必要  
- Planning Engine実行後にChartsタブを確認する場合、`Refresh`ボタンを押すこと  
- 新しいモデルフォルダを追加する場合は`rice-japan-2027-2028/`を参考に全CSVを揃えること
- Linuxのbash Editツールは大きいファイルを切り捨てることがある。重要ファイルの書き換えは `cat > file << 'PYEOF'` ヒアドックで行うこと

---

## 既知のバグ修正履歴（新しいClaude君へ）

### HolidayCalendarPlugin MemoryError（修正済み）
`wom/engine/holiday_calendar_plugin.py` の `on_post_backward` で `cap_hard(w)==0.0` を使って閉鎖週を判定していたが、`plan_node.py` はデフォルトで全週 `cap_hard=0.0` に初期化するため、全週が閉鎖扱いとなり displaced lots が指数的に増加して MemoryError が発生した。
**修正**: `self._rules` から `explicit_closures` dict を構築し、CSVに明示定義された週のみを閉鎖週とする方式に変更。open週がない場合はlotsをdropする（ForwardPlannerへの再割り当てなし）。

### BackwardPlanner._build_lot_leaf_index（実装済み）
`wom/engine/backward_planner.py` の多MOM（Multi-MOM）パスで `self._build_lot_leaf_index(ot_root)` を呼び出しているが、このメソッドが未実装だった（iPhone モデルで `AttributeError`）。
**修正**: OTツリーのleaf_outノード（`node.children`が空）を走査して `lot_id → PlanNode` インデックスを構築するメソッドを追加。また `leaf.region`（PlanNodeに`.region`属性なし）は `lot_id.split(":")[1]` でlot_idから抽出する方式に変更。

### holiday_calendar.csv のノード名（修正済み）
demand_multiplier 行のノード名 `Sales_US_iPhone16` / `Sales_EU_iPhone16` は存在しない。正しくは `Retail_AMER` / `Retail_EMEA`（sc_tree_master.csvのleaf_out node_name）。

### ファイルのnullバイト汚染（修正済み）
v1r0m1の `backward_planner.py` と `holiday_calendar.csv` にnullバイトが混入していた（Windowsでのコピー操作が原因の可能性）。Linuxの `bash cp` で上書きして修復。

### ForwardPlanner: PUSH MOM の在庫が0になるバグ（v1r0m3で修正済み）
`wom/engine/forward_planner.py` の Phase 1（InBound POST-ORDER）で、`is_decoupling=True` の全ノードに `psi4supply[w][P] = psi4demand[w][P]`（Demand-S copy）を適用していた。しかしPUSH設定されたMOM（`plan_mode="push"`）は `is_decoupling=True` になるため、leaf_in → tier-1 の `_propagate_to_parent` で積み上げた P が Demand-S copy に上書きされ、バッファ在庫が 0 になっていた。
**修正**: `node.plan_mode != "push"` 条件を追加し、PUSH MOM には Demand-S copy を適用しない。Buffer_Wafer_TW（`plan_mode="pull"`）は引き続き Demand-S copy が適用される。

### pytest .pyc キャッシュ問題（Linux環境）
Windowsでフォルダをコピーした場合、`__pycache__/*.pyc` も元のパスを `co_filename` として持つ。Linux FUSE マウント経由では .pyc の削除が permission error になるため、Python が古い .pyc を優先して .py の変更が反映されない。
**対処**: `os.utime(file, (now+10, now+10))` で .py ファイルのタイムスタンプを .pyc より新しくするか、`PYTHONDONTWRITEBYTECODE=1` + Python による .py 直接書き込み（`python3 << 'EOF'` ヒアドック）で迂回する。pytest 実行時は `PYTHONDONTWRITEBYTECODE=1 python -m pytest ... -p no:cacheprovider` を使うこと。

### PPC detect_scenario() が biscuit-jp-2026 → Cookie-jp-2026 リネーム後に不一致（修正済み、2026-07-05）
`data/sample/biscuit-jp-2026/` を `Cookie-jp-2026/` にリネーム＋SKU名を `OREO_JP`/`LUVAN_JP` → `Cookie_Import`/`Cookie_Local` に変更した際、`wom/ppc/ppc_engine.py` の `detect_scenario()` 側（`_BISCUIT_PRODUCTS = {"OREO_JP", "LUVAN_JP"}` 等）が更新されておらず、新SKU名と一致しないため `"iphone"` シナリオにフォールバックしていた。`mom_node`/`supplier_node`/`dad_node`/`dad_nodes_chain` も旧ノード名（`Factory_OREO_CN`, `DC_JP_BONDED`, `Factory_LUVAN_JP`, `DC_LUVAN_JP` 等）のままで、`ppc_node_cost_rule.csv` の実ノード名（`Factory_GP_CN`, `DC_Import_Buffer`, `DC_Import_Main`, `Factory_DP_JP`, `DC_Local_JP`）と不一致だった。
**修正**: `wom/ppc/ppc_engine.py`（`_COOKIE_PRODUCTS`/`_COOKIE_CHANNELS`, `build_cookie_vs_paths()`, `detect_scenario()` の戻り値 `"cookie"`）、`wom/ppc/ppc_runner.py`、`wom/ppc/__main__.py`、`wom/ppc/ppc_backward.py`（コメント）を新ノード名・新シナリオ名に更新。また `node_master.csv` / `sc_tree_master.csv` / `edge_cost_master.csv` 内の日本語ラベル「ビスケット」を「クッキー」に修正（World Map表示にも反映）。
**確認状況**: World Map表示は確認済みOK。PPC Cockpit（Cookie_Local）のCost Waterfallが `ppc_node_cost_rule.csv` の実値（Factory_DP_JP conversion_cost 9000 JPY, DC_Local_JP sga_cost 4000 JPY）と一致することを確認し、正しいノードチェーンでコストが拾えていることを確認済み。**Cookie_Import 側（`DC_Import_Buffer`→`DC_Import_Main` の2段DADチェーン、`DC_Import_Main`のSGA 1500円が正しく合算されるか）は未確認 — 次回セッションでSKUフィルタを`Cookie_Import`に切り替えて確認すること。** また `python -c "import ast; ast.parse(...)"` によるWindows側の構文チェックも未実施（Linux bashマウント経由では大きめの `.py` ファイルが切り捨てられ `ast.parse` が誤ってSyntaxErrorを出すため、Windows側で確認が必要）。

### ev-thailand-2026 の BYD/Tesla 実ブランド名を匿名化（完了、2026-07-06）
`data/sample/ev-thailand-2026/` は `BYD_ATTO3`/`TESLA_M3` という実在EVメーカーのブランド名・車種名を含んだままだった。note記事ドラフト（`260704タイEV_note記事ドラフト.docx`）はすでに `EVmaker_Local`/`EVmaker_Import` という匿名名を前提に書かれており、CSVとの不一致があった。
**修正**: 全17 CSVファイル（`sku_master.csv`, `node_master.csv`, `sc_tree_master.csv`, `node_cost_master.csv`, `edge_cost_master.csv`, `lane_assignment.csv`, `route_master.csv`, `push_config.csv`, `holiday_calendar.csv`, `inventory_master.csv`, `capacity_plan.csv`, `demand_forecast.csv`, `ppc_edge_cost_rule.csv`, `ppc_market_price.csv`, `ppc_node_cost_rule.csv`, `ppc_node_profit_zone.csv`, `ppc_profit_zone_rule.csv`, `ppc_supplier_cost.csv`, `ppc_tariff_rule.csv`, `ppc_transfer_price_rule.csv`）で以下の対応関係にリネーム：
- `BYD_ATTO3` → `EVmaker_Local`、`TESLA_M3` → `EVmaker_Import`
- `SP_BYD_TH`→`SP_EV_Local`、`Factory_BYD_TH`→`Factory_Local_TH`、`DC_BYD_TH`→`DC_EV_Local`
- `SP_TESLA_TH`→`SP_EV_Import`、`Factory_TESLA_CN`→`Factory_Import_CN`、`DC_TESLA_TH`→`DC_EV_Import`、`Components_CN_T`→`Components_CN`
- `Sales_TH_BKK_t`/`_PRO_t`/`_ONL_t`（Tesla側チャネル）→ `_i` サフィックスに変更（`Sales_TH_BKK_i` 等）。Local側の `Sales_TH_BKK`/`_PRO`/`_ONL` はサフィックスなしのまま据え置き（note記事ドラフトの命名と一致）。
- 説明文中の実企業名（レバーオートモーティブ、CATL、Gigafactory等）も除去し一般化。

**確認状況**: `wom/ppc/ppc_engine.py`/`ppc_runner.py`にBYD/Tesla固有のハードコード分岐は存在せず（biscuitのような専用シナリオ関数はなし）、PPCエンジンは`ppc_runner.py`の「GENERIC」自動検出パス（sc_treeからmom/supplier/dad nodeを動的に発見）でこのモデルを扱う設計だったため、**Pythonコード側の修正は不要**。リネーム後、CSV内に旧トークン（BYD_ATTO3, TESLA_M3, Factory_BYD_TH等）が残っていないことをGrep確認済み。行数・列構造も変化なし（capacity_plan.csv 625行、demand_forecast.csv 624行、変更前と一致）。GUI起動してWorld MapとPPC Cockpitの実挙動を確認済みOK（下記Landed Costバグ発見時に併せて確認）。

### Landed Cost engine: Landed GM%が1129%等の異常値になるバグ（修正済み、2026-07-06）
`wom/engine/landed_cost.py` の `compute_landed_cost_kpi()` が、Management タブの「Tariff & FX — Landed Cost Impact」パネルで `ev-thailand-2026` を実行した際に `Landed GM% 1129.0%` という非現実的な値を出していた（ユーザー指摘で発覚）。原因は2つ、いずれも「iPhoneモデル（単価$1000前後・fx_rate=1.0のUSDのみ）でしか成立しない代理計算」だった。
1. `estimated_lots = max(revenue / 1000.0, 1.0)` — 「1lot≈$1000」という前提の代理計算。EVモデル（1台80万〜160万THB）では `revenue=75,086,960,000` から `estimated_lots≈75,086,960`（実際は数万〜十数万lot程度のはずが桁違いに膨張）となり、`freight_total = blended_freight_per_lot × estimated_lots` が異常膨張（Freight $43,175,002,000 という表示値の直接原因）。
2. `fx_gain_loss = (blended_fx - 1.0) * cogs` — `fx_rate` が1.0前後の「比率」である前提だが、実際の`edge_cost_master.csv`の`fx_rate`は35.0（THB/USD）や145.0（JPY/USD）といった**絶対為替レート**。`(35.0-1.0)=34倍`がCOGSに掛かり`landed_cogs`から減算され、Landed GM%が桁違いの値になっていた。

**修正**:
- `wom/engine/money.py`: `evaluate_money()`の週次集計に`total_units`（`demand_fulfilled`の合計＝実lot数）を追加し、`build_scenario_money_kpi()`のシナリオ集計にも`units`列として伝播。これにより`compute_landed_cost_kpi()`が実際のlot数を参照できるようになった（`revenue/1000`の代理計算はunitsが取れない場合のフォールバックとしてのみ残す）。
- `wom/engine/landed_cost.py`: `lot_count`は`kpi_row["units"]`から取得。`freight_total = blended_freight_per_lot × lot_count × blended_fx`（USD建てのfreightをfx_rateで報告通貨に変換、docstring本来の設計通り）に修正。`fx_gain_loss`（COGSへの誤った为替比率適用）は完全に削除——revenue/cogsは既にWOM money engineで報告通貨（JPY/THB等）建てのため、二重にfx調整する必要がない。ファイル冒頭のdocstring（Calculation model節）も実装と一致するよう全面的に書き直した。
- 出力dict内の`fx_gain_loss`キーは後方互換のため残すが常に0（廃止済みの注記付き）。

**確認状況**: 手計算でEVモデルのBaseシナリオを検算——修正後 `landed_gm ≈ 28.5%`（元のgross margin 31.9%からtariff/freight負担で妥当な範囲の低下）となることを確認。GUI実行結果（Management タブ）でも Base 27.5%・EV30/EV35 29.6% と妥当な値で表示されることをユーザー確認済み。なお、PPC Cockpit画面で "Base currency: JPY" と表示されるのはTHB建てのev-thailand-2026でも固定表示になっている可能性があり、別途確認の余地あり（今回は未調査）。

### Management タブ: SKUフィルタ追加 + Inv Value常時0バグ修正（完了、2026-07-06）
Management タブの P&L Summary / Strategic KPI / Tariff&FX (Landed Cost) が SKU=ALL の全体合算のみで、SKU別評価ができなかった（ユーザー要望で追加）。あわせて調査中、`build_scenario_money_kpi()`（`wom/engine/money.py`）の集計キーワードが `inv_value=(Cols.INV_VALUE_COST, "mean")` となっており、出力列名が `"inv_value"`（別の定数 `Cols.INV_VALUE`）になっていた。一方 `app.py` の P&L テーブルや `management.py` の `_row_to_money_dict()` はどちらも `Cols.INV_VALUE_COST`（`"inv_value_cost"`）で参照していたため、**Inv Value は常に0扱い**になっていた（P&L SummaryのInv Value列が常に0だったのはこれが原因）。

**修正**:
- `wom/engine/scenario.py`: `ScenarioManager` に `sc_tree` / `lc_scens` / `route_idx` を追加。Planning Engine 実行後（`app.py`）にこれらを保持し、Management タブ側でPlanning再実行なしにSKUフィルタの再計算ができるようにした。
- `wom/engine/strategic_kpi.py`: `compute_strategic_kpi()` に `product_filter` 引数を追加（指定した1製品のノードのみ集計）。
- `wom/engine/landed_cost.py`: `filter_scenario_by_sku()` を新設（`route_master.csv`の(sku_id,region)→(src_region,dst_region)を使い、LandedCostScenarioのprofilesを対象SKUのレーンだけに絞る）。`compute_landed_cost_kpi()`/`compare_lc_scenarios()`に`sku_id`引数を追加し、KD組立コスト集計・関税/為替ブレンドをSKUスコープにできるようにした（`sku_id`未指定時は従来通り全SKU合算）。
- `wom/gui/app.py` `ManagementCockpitPanel`: 「SKU:」ドロップダウン（All + 実在SKU一覧）を追加。選択変更で `_refresh_pl_table()` / `_refresh_strategic_kpis()` / `_refresh_lc_table()` / `_refresh_charts()` を、`mgr.summary_money`をSKUでフィルタして`build_scenario_money_kpi()`で再集計した行、`compute_strategic_kpi(sc_tree, product_filter=sku)`、`compare_lc_scenarios(..., sku_id=sku)`を使って再計算するように変更（"All"選択時は従来通りPlanning Engine実行時に事前計算済みの値を使用、挙動不変）。
- Inv Value バグ修正: `build_scenario_money_kpi()`の集計キーワードを `inv_value_cost=(Cols.INV_VALUE_COST, "mean")` に変更（列名を実際の定数値と一致させた）。

**確認状況**: コードレビューベースで整合性確認済み（Edit toolでの直接編集、bashマウント経由の構文チェックは大きめファイルで信頼できないため未実施）。**次回セッションでGUI起動し、①SKUドロップダウンで実際にP&L/Strategic KPI/Landed Costが切り替わるか、②Inv Value列が0以外の値を表示するか、の実地確認が必要。**

### ForwardPlanner: Lot_ID identity-matching方式への刷新（DADバッファ在庫問題の根本修正、完了、2026-07-06）

Cookie Japan 2026 note記事ドラフトの注記「DADノードの在庫（I）は常に0（pass-through設計）。ss_days=21は将来実装（v1r0m5）向けの設定で、現在DC_Import_Bufferへの在庫積み上がりは発生しない」について、大杉さんから「SS_daysの取扱いはWOM初期から標準機能だったはず」との指摘を受け調査。

**調査で判明した事実**:
1. `backward_planner.py`の`_ot_propagate`/`_in_propagate`は既に`node.lt_wks + node.ss_wks`をオフセットに使っており、大杉さん提案の`LT_shift = LT_transit + SS_weeks`は実装済みだった。
2. `forward_planner.py`の物理搬送（`_propagate_to_child`/`_propagate_to_parent`）はpure `lt_wks`のみを使用（SS_weeks分だけ早着する設計）。
3. しかし実測すると、DC_Import_Buffer（lt_wks=5, ss_days=21→ss_wks=3）の`I`は52週間フルトレースで常に0だった。
4. 原因は`ForwardPlanner._process_node`のCase1/2/3分岐が**個数（len）ベース**で、`available`（物理在庫+入荷）と`total_demand`（CO+S）を**位置（何番目か）でスライス**していたこと。シミュレーション開始直後（期初在庫ゼロ、初週から満量需要）に生じる不可避な立ち上がり不足が、巨大なCOとして生成され、以後は毎週の新規供給がすべてこの「凍結した過去の負債」の穴埋めに使われ続け、二度と在庫として積み上がらなくなっていた（COは`_process_node`内で毎週クリアされ表示上は常に0に見えるため、この凍結は発見しづらかった）。

**大杉さんとの議論で得られた設計方針**:
- `C:\Users\ohsug\WOM_V0R1M0_github\pysi\network\node_base.py`の`calcPS2I4supply()`（v1r0m0オリジナルのPySIエンジン）を確認したところ、`fifo_lot_diff(i0, p, s)`という**Lot_ID identity（集合差分）ベース**の実装だった（個数比較ではなく`if lot not in s`という一件ごとの判定）。COを読むが書き込まない未完成な実装だったため、大杉さんの提案で「COも含めた対称的なidentityマッチング」に一般化：
  - `I1 = (i0+p) − (CO+S)`（identityで、CO+Sに含まれないLot_IDが在庫として残る）
  - `CO1 = (CO+S) − (i0+p)`（identityで、i0+pに実在しなかったLot_IDが翌週へ、これが欠品リストそのもの）
- `S`と`CO`は「計画値」として**一切書き換えない**（Sの一意性を守る）。物理的に実際に出荷されるLot_IDは`ForwardPlanner._actual_s`という別チャネルに保持し、`_propagate_to_child`/`_propagate_to_parent`/MOM→supply_pointブリッジはこちらを参照する。

**実装内容**（`wom/engine/forward_planner.py`）:
- `_match_by_identity(demand_lots, supply_lots)`staticmethodを新設。Lot_ID identityで`matched`/`unmatched_demand`/`unmatched_supply`を返す。
- `_process_node`の通常（pull）分岐を、個数ベースのCase1/2/3から`_match_by_identity`ベースに置換。`S[w]`/`CO[w]`は変更せず、`I[w] = unmatched_supply`、`CO[w+1] += unmatched_demand`。
- `self._actual_s: Dict[node_id, Dict[w, List[lot_id]]]`を新設（旧`_push_actual_s`を全modeに一般化・リネーム）。`_propagate_to_parent`/`_propagate_to_child`/Phase2ブリッジは`psi4supply[w][S]`ではなく`self._actual_s`を参照するよう変更。
- `is_push_mode`/`is_push_sub`分岐は個数ベースのロジックのまま維持（scope外、iPhoneモデルのBuffer_Wafer_TW等で別途十分にテスト済みのため）。

**確認結果**:
- 既存63件のテストは`tests/test_step7_capacity.py::test_e2e_cap_hard_causes_leaf_shortfall`と`tests/test_step8_push_pull.py::test_dad_inventory_cap_hard_shortfall`の2件が失敗（想定通り。DAD.Sが「実供給で制約された値」ではなく「計画値のまま」になったため）。両テストは新設計の検証内容（`fp._actual_s`で実出荷数、`psi4supply[w][CO]`で欠品数を確認）に書き換え、63件全PASSを再確認。
- Cookie_Import / DC_Import_Buffer を52週フルトレースした結果、`I`が41週で非ゼロとなり、SS_days=21日（3週）分の安全在庫バッファが正しく可視化されることを確認。
- 立ち上がり期の不可避な不足（期初在庫ゼロ・初週から満量需要）は、以前のように無限に増殖する凍結COではなく、**有限かつ正直な**未充足Lot_ID集合として`CO`に残る（該当Lot_IDの需要週がシミュレーション開始週より前で、物理的に到底間に合わないため）。

**未対応・次回検討事項**:
- GUIのBuffer Stockチャート（Charts タブ）は依然MOMノードのみ参照。DAD側のIも表示対象に含めるかは次回検討。
- note記事「Cookie Japan 2026」の該当注記（DADのIは常に0、SS_daysは将来実装向け）は誤りとなったため、記事側の修正が必要（大杉さんの記事執筆時に反映）。
- PPC/Money engine・Fill Rate計算はleaf_outノードの`psi4supply[w][S]`のみ参照しており、leaf_outは常にmatched=S（pull_modeでP=demand.Pに強制されるため）なので影響なし。ただしDebugPanelの`_draw_cost_from_plan_node`（app.py、任意のnodeを選択してRevenue/COGSを表示する機能）は非leaf_outノードでは「計画値」ベースの表示になる点に注意（実出荷ベースへの追従は未実施、影響は限定的）。

### Buffering Stock配置最適化エンジン（`wom/engine/decouple_optimizer.py`、新規実装、完了、2026-07-06）

大杉さんの提案「buffering stock候補 = SKU数 × lane中の平均node数、という限られたnodeの組み合わせをすべて評価すれば、cost最適な在庫配置を提示できる」を受け、v1r0m0（PySI）の`pysi/plan/engines.py`を調査。**候補生成ロジック（`make_nodes_decouple_all`）は残っていたが、評価ロジックは見つからなかった**ため、大杉さんに確認の上、v1r0m4で新規実装する方針とした。

**実装内容**:
- `build_decouple_candidates(ot_root)`: `make_nodes_decouple_all`のポート。leaf_out群を出発点に、兄弟ノードを親ノードへ1候補ずつマージしていく（深い方から）ことで、`O(node数)`件の候補（2^N の全組み合わせではない）を生成。**supply_point（仮想bridgeノード、lt_wks=0、実在しない場所）を含む候補は除外**——最初の実装では除外しておらず、後述の理由でランキングが破綻したため追加。
- `evaluate_decouple_placement(...)`: 各候補について、供給層をリセット（`copy_demand_to_supply`で再構築——CO は識別子マッチング方式で追記専用のため、候補間でリークしないようリセットが必須）した上で`ForwardPlanner(..., decouple_node_ids=candidate)`を1回実行し、全ノード合計の在庫lot数・在庫コスト（`node_cost_master.csv`のunit_cost_per_lot使用）・欠品(shortfall) lot数を測定。
- `find_optimal_decouple_placement(...)`: 全候補を評価し、**サービスレベル制約付きランキング**で最良候補を選定。

**サービスレベル制約が必要だった理由（実装中に発見したバグ）**:
最初の実装は単純に「在庫コスト最小」で候補をランキングしたところ、`supply_point`（仮想bridgeノード）が「最良」に選ばれる縮退結果が発生した。原因は、decouple pointをsupply_pointに置くと、それより下流の全ノードがPULLモードに強制され（`P = demand.P`のコピー）、実際の需給ミスマッチが在庫=0・欠品=0として隠蔽され、真の需給ギャップがsupply_point自身のCOだけに（不自然に）集約されるため。この結果、「在庫コストが低い」ことと「実際にサービスレベルが高い」ことが一致しなくなっていた。
**対策**: (1) 候補生成時にsupply_pointを含む候補を除外。(2) `find_optimal_decouple_placement`で「全候補中の最小shortfall × 許容比率(デフォルト1.10倍)」以内の候補だけを`eligible`として抽出し、その中でコスト最小を選定（`ranked`は参考として全候補・コストのみのソート結果も保持）。

**確認結果**（`data/sample/Cookie-jp-2026`、node_cost_master.csvベース）:
- Cookie_Import: 候補3件（`[Retail×3]`, `[DC_Import_Main]`, `[DC_Import_Buffer]`）→ **`DC_Import_Buffer`が最良**（inv_cost最小かつshortfallも最小）。CSV上`buffering_stock_flag=1`が設定されている実際の設計と一致。
- Cookie_Local: 候補2件（`[Retail×3]`, `[DC_Local_JP]`）→ **`DC_Local_JP`が最良**。
- 既存63件のテストは無変更・全PASS（本モジュールは既存エンジンを呼び出すだけで、`ForwardPlanner`/テストコード自体には変更なし）。

**スコープ制約・次回検討事項**:
- OutBound（leaf_out → DAD → supply_point）側のみ対応。InBound（leaf_in → MOM）側のbuffer配置最適化は別問題として未実装（下記の通り、意図的に対応しない方針で確定）。
- ~~GUI統合（Managementタブ等からの呼び出しUI）は未実装。~~ → `BufferingStockOptimizerPlugin`として実装済み（下記）。
- shortfall許容比率（デフォルト1.10）は暫定値。業種・SKUごとのサービスレベル要件に応じて調整可能な設計にはなっているが、デフォルト値自体の妥当性検証は未実施。

### InBound側バッファ配置最適化を対象外とする方針確定（2026-07-06）

大杉さんの判断: 「各素材・部材の加工工程の生産能力のLOT単位処理能力で、相対的にボトルネックが発生した場所で、DBR的なbuffering stockが発生する」ため、InBound側はOutBoundのような「どこに置いてもコスト最適化できる自由度」がなく、物理的な設備能力差・ボトルネック制約が支配的。よってバッファ配置最適化という問題そのものに発展しない。**InBound側は今後も対象外のまま据え置く。**

### BufferingStockOptimizerPlugin（`wom/plugins/buffering_stock_optimizer.py`、新規実装、完了、2026-07-06）

`decouple_optimizer.py`をPluginとしてPlanning Engineパイプラインに組み込み、`decouple_optimizer_config.csv`のON/OFFフラグでSKUごとに有効化できるようにした。

**フック位置の設計判断（重要）**: 当初「PRE_PLANで発火」という案があったが、`evaluate_decouple_placement()`は内部で候補ごとにForwardPlannerを試走する前提としてpsi4demandが埋まっている必要がある（BackwardPlanner完了後）。PRE_PLANはSCTree構築直後・BackwardPlanner実行前に発火するため、この時点ではpsi4demandが空でPlugin側の評価が成立しない。よって**`HOOK_POST_BACKWARD`**（BackwardPlanner完了直後、公式の`copy_demand_to_supply`実行前）を正しいフック位置として採用した。

**実装内容**:
- `BufferingStockOptimizerPlugin`（`WOMPlugin`継承、`on_post_backward`をoverride）:
  1. `decouple_optimizer_config.csv`（`cap_path`と同じディレクトリ、`cap_override.csv`と同じ解決パターン）を読み、対象SKUの行が無い/`enabled=0`/ファイル自体が無い場合は即return（no-op、既存の手動`buffering_stock_flag`設定がそのまま使われる＝後方互換）。
  2. `enabled=1`の場合、`find_optimal_decouple_placement()`を実行し、最良候補を選定。
  3. OutBoundツリー（`sc_tree.get_ot_root(prod_nm)`配下）の全ノードの`is_decoupling`をいったん`False`にリセットし、最良候補のノードのみ`True`に上書き。
  4. Plugin実行後、`psi4supply`（S/CO/I/P全バケット）を空にクリアした状態で終了（**再`copy_demand_to_supply`は呼ばない**——このHookの直後にパイプライン本体が公式の`copy_demand_to_supply`を実行するため、二重実行を避けた）。
- `decouple_optimizer_config.csv`スキーマ: `sku_id, enabled, max_shortfall_ratio`（`max_shortfall_ratio`列は省略可、省略時デフォルト1.10）。
- `wom/plugins/__init__.py`の`ALL_BUILTIN_PLUGINS`に登録済み。
- `data/sample/Cookie-jp-2026/decouple_optimizer_config.csv`をサンプルとして追加（`enabled=0`——スキーマの見本のみ、デフォルト動作は変更しない）。

**テスト**（`tests/test_decouple_optimizer.py`, `tests/test_buffering_stock_optimizer_plugin.py`、計8件、全PASS）:
- 候補生成がsupply_pointを除外することを確認。
- `ss_days`が特定ノードにのみ設定されている場合、そのノードが「decouple点より下流（pull-mode強制）」になると`ss_days`由来の早期在庫シグナルが完全に消える（`psi4supply[w][P]`が`demand.P`で上書きされるため）ことを実際の合成ツリーで確認・数値検証。これが CLAUDE.md 既出の「is_decoupling **かつ** ss_daysが設定されていれば」という前提条件の具体的なメカニズムである。
- `find_optimal_decouple_placement()`をCookie-jp-2026実データで再検証（`decouple_optimizer.py`本体のテストとしては本セッションで初めて追加——これまでは手動probeスクリプトのみだった）：Cookie_Import→`DC_Import_Buffer`、Cookie_Local→`DC_Local_JP`が引き続き最良候補になることを回帰テスト化。
- Plugin側: 設定ファイル無し/`enabled=0`/対象外SKUの行のみ、の3パターンで確実にno-opになること、`enabled=1`時に正しいノードへ`is_decoupling`が切り替わり、かつ`psi4supply`が空にクリアされて公式パイプラインに引き渡せる状態になることを確認。
- 既存63件 + 新規8件 = 計71件、全PASS。

**未対応・次回検討事項**:
- GUI側のPlugin ON/OFFトグル（Management/Settings的な画面からの切り替えUI）は未実装。現状は`decouple_optimizer_config.csv`を直接編集する運用。
- レーン障害時の代替ルート切り替えPlugin（例: ホルムズ海峡封鎖時に紅海ルートへ切り替え）は、大杉さんから将来実装候補として提案あり。こちらは`HOOK_PRE_PLAN`（SCTree構築直後・BackwardPlanner実行前、`edge_cost_master.csv`/`route_master.csv`ベースのlt_wks・cap_hard書き換え）が適切なフック位置で、既存の`CapacityOverridePlugin`/`HolidayCalendarPlugin`と同じパターンで実装できる見込み。次回セッションでの実装候補として記録のみ（今回は未着手）。

---

## v1r0m5 実装済み機能（新しいClaude君へ）

### PPC: 複数Tier-1サプライヤー対応 + 拠点別P/L評価（`ppc_forward.py`, `ppc_kpi.py`, Management タブ、完了）

「第4回: 仮想の欧州EV市場」note記事（`data/sample/ev-europe-2026/`）で、EVのBOM構造を Battery/Motor/ECU の3 Tier-1 サプライヤー（leaf_in）が1つのMOMに供給する形にした際、既存のPPCエンジンが**最初に見つけたleaf_inノード1つしかコストに反映していない**ことが判明した。

**原因**: `wom/ppc/ppc_runner.py`のGENERICシナリオ自動判定で `elif _nt == NODE_TYPE_LEAF_IN and _prod not in _sup_map: _sup_map[_prod] = _nm` としており、`_prod not in _sup_map`のガードにより2つ目以降のleaf_inは無視されていた。さらに`wom/ppc/ppc_forward.py`の`run_forward_propagation()`は`supplier_node`を単一ノードとしてしか解決しない設計だった（`_resolve_node()`がstr/dict[str,str]のみ対応）。この結果、Motor/ECU側は`ppc_supplier_cost.csv`に行があっても一切参照されず、PPCEventすら生成されないため、ノード別コスト集計をしても0円のまま欠落する。

**修正**:
- `wom/ppc/ppc_forward.py`: `_resolve_node_list(node, product_id) -> List[str]` を新設（str / list[str] / dict[str,str] / dict[str,list[str]] の全形式に対応、`ppc_backward.py`の`dad_nodes_chain`解決パターンを踏襲）。`run_forward_propagation()`の`supplier_node`引数をこの関数で解決し、**解決された全サプライヤーをループしてコストを積算 + サプライヤーごとに1件ずつ`supplier_cost`イベントを生成**するよう変更（各イベントの`node_id`はそのサプライヤー自身のノードID）。Cookie/iPhone/RiceのようなシングルサプライヤーはP`_resolve_node_list`が単一値を1要素リストにラップするため無変更で動作する。
- `wom/ppc/ppc_runner.py`: GENERIC分岐の`_sup_map`（単一値）を`_sup_list_map`（全leaf_inのリスト）に変更。積み上げたリストは複数製品時`dict[product_id -> list[str]]`、単一製品時は素の`list[str]`として`supplier_node`に渡す。
- `wom/ppc/ppc_kpi.py`: `build_node_pl_summary(events)` を新設。週次分解の`build_node_week_summary()`と異なり、全期間を通算した「拠点別P/L評価」テーブル（`node_id, product_id, revenue_base, cost_base, tariff_base, gross_profit_base, gross_margin_pct, lot_events`）を1ノード1行で返す。PPCEventの`node_id`にサプライヤーごとの実ノードIDが乗るようになった今回の修正により、Battery/Motor/ECUがそれぞれ独立した行として正しく現れる。
- `wom/ppc/ppc_models.py` / `ppc_engine.py` / `ppc_export.py`: `PPCSimulationResult.node_pl_summary`フィールドを追加し、`run()`内で自動計算・`output/ppc/ppc_node_pl_summary.csv`として出力するよう配線。
- `wom/gui/app.py` `ManagementCockpitPanel`: 既存の「P&L Summary」テーブル直下に新しい「Node P&L（拠点別損益）」テーブルを追加（既存のSKUフィルタドロップダウンに連動）。`_refresh_node_pl_table()`が`output/ppc/ppc_node_pl_summary.csv`を読み込み表示。PPCエンジンが完了した際（`_on_ppc_done`）にも自動リフレッシュされるよう配線済み。

**確認結果**:
- `tests/test_ppc_multi_supplier.py`（新規10件）: `_resolve_node_list`の4形式、複数サプライヤーのイベント生成・コスト合算、`dict[product_id -> list]`形式、既存の単一サプライヤー形式が無変更で動作すること、`build_node_pl_summary`の拠点別内訳を確認。既存71件と合わせて計81件、全PASS。
- `data/sample/ev-europe-2026/`実データで検証（`ppc_supplier_cost.csv`にMotor_DE/ECU_DE/Motor_HU/ECU_HUの行を追加——`node_cost_master.csv`の`unit_cost_per_lot`と整合する値: 3600/1600/3000/1400 EUR）: 修正前はBattery_DE/HUのみノード別コストが乗っていたはずが、修正後は`ppc_node_pl_summary.csv`にBattery/Motor/ECUの3ノードすべてが両SKU（EVmaker_Local/Import）で非ゼロコストとして現れることを確認（Battery_DE ¥265.1M、Motor_DE ¥90.9M、ECU_DE ¥40.4M、Battery_HU ¥202.0M、Motor_HU ¥75.7M、ECU_HU ¥35.3M）。

**設計上の注意（次回のClaude君へ）**:
- 「拠点別P/L評価」は現状、**leaf_outチャネルにのみRevenueが立ち、それ以外の全ノードはCostのみ**という構造（PPCエンジンがMOM一箇所にしかtransfer_priceを持たないため）。よって非チャネルノードの`gross_profit_base`は実質「-cost_base」であり、真の意味でのノード単体P&L（各ノードに自前のRevenue/Costがある社内取引評価）ではない。あくまで「どのノードにコストが集中しているか」を可視化するための一次的な実装であり、真の拠点別損益（ノード間振替価格を全エッジに設定する等）は将来の拡張候補として残っている。
- InBound側（leaf_in）のバッファ配置最適化は引き続き対象外方針（v1r0m4の`decouple_optimizer.py`のセクション参照）。今回の修正はコスト集計のみでPSI計画ロジックには一切手を入れていない。

---

## v1r0m2 実装済み機能（新しいClaude君へ）

### JIT週次同期：cap_hard envelope in `_in_propagate`（commit 7a22648）【v1r0m3で廃止】

~~v1r0m2 で `_in_propagate` に cap_hard envelope を追加し、上流伝播をクリップしていた。~~

**v1r0m3 で廃止**。BackwardPlanner は純粋な需要逆伝播（LT offset のみ）とする方針に変更。
cap_hard enforcement は `_apply_mom_cap_backward`（MOM 専任）と ForwardPlanner に移譲した。
これにより上流ノードは cap 前の全量需要を受け取り、ForwardPlanner が supply allocation を判断できる。

---

### DBR設計：PUSH/PULL break-point at Buffer_Wafer_TW（commit 7a22648）

iPhone Global SC の InBound チェーン：

```
SiliconWafer_TW (leaf_in, PUSH sub)
  → Buffer_Wafer_TW (decoupling node, PUSH) ← PUSH/PULL break-point
    → TSMC_TW (PULL)
      → Foxconn_CN (PULL MOM, Drum)
```

- **Drum**: Foxconn_CN（cap_hard staircase: 800→534→267→0/wk）
- **Buffer**: Buffer_Wafer_TW（在庫クッション、DBRバッファ）
- **SiliconWafer_TW**: 自律PUSH（ウェーハFab = 高固定費・常時稼働型）

`push_config.csv` でBuffer_Wafer_TWをdecoupling nodeとして設定。

---

### Mode 4 LT-shifted PUSH：`push_lead_time_weeks`（commit f9ebc37）

`wom/engine/push_pull.py` の `PushConfig` に `push_lead_time_weeks` フィールドを追加。
`push[w] = demand_ref_node.psi4demand[w + LT][S]`

この1パラメータで**DBRバッファの完全なライフサイクルPSIパターン**が自動生成される：

| フェーズ | 期間 | 動作 |
| :---- | :---- | :---- |
| Pre-build | demand[w]=0, demand[w+LT]>0 | 生産開始、バッファ積み上がり（差分が積み上がる） |
| Steady | demand[w] == demand[w+LT] | 生産=消費=staircase、バッファ平坦 |
| Staircase gap | demand[w+LT] < demand[w] | 生産が先行してステップダウン、バッファが差分を吸収 |
| EOL stop | demand[w+LT]=0, demand[w]>0 | 生産停止、バッファが最終需要を賄いゼロに収束 |

**iPhone16モデルでの設定** (`push_config.csv`)：

```csv
push_lead_time_weeks=26
mom_ref_node_id=""（decoupling node自身 = staircase信号を使用）
```

**確認済み波形** (Buffer_Wafer_TW PSIチャート)：
- 2026-W01〜W27: 生産ゼロ（demand[w+26]がまだ0）
- 2026-W28〜W52: 800/wk pre-build、I上昇（〜20,800 lots）
- 2027-W01〜: P=S=800/wk（平坦）
- 2027-W40〜: 生産534 < 消費800、I段階的低下
- 2030-W13付近: I→0（製品ライフサイクル終了と同時に自然消滅）

Foxconn_CN の生産シフトが TSMC_TW 経由で Buffer_Wafer_TW の在庫減少パターンとして
伝播する「SC lane node間のPSI連動」を実現。

**push_config.csv スキーマ（全フィールド）**：

| フィールド | 説明 |
| :---- | :---- |
| `node_id` | decouplingノードのnode_id |
| `push_qty_per_week` | Mode1: 固定週次生産量（>0でMode1） |
| `buffer_lots` | Mode2/3: 目標バッファ在庫 |
| `mode_only` | plan_modeフラグのみ設定（P-schedule上書きなし） |
| `mom_ref_node_id` | Mode2: 需要参照ノード（空=decoupling node自身） |
| `pre_build_qty_per_week` | Mode3: Phase1固定生産量 |
| `pre_build_end_week` | Mode3: Phase1終了週ラベル（例: "2026-W52"） |
| `push_lead_time_weeks` | Mode4: LTオフセット週数（優先度最高） |

**Mode選択ロジック**：
1. `push_qty_per_week > 0` → Mode 1（固定）
2. `push_lead_time_weeks > 0` → Mode 4（LT-shifted、最優先）
3. `pre_build_qty_per_week > 0` AND `pre_build_end_week` → Mode 3（時間軸分割）
4. それ以外 → Mode 2（古典的補充）

---

## v1r0m3 実装済み機能（新しいClaude君へ）

### MOM Constrained Demand Allocation（`_apply_mom_cap_backward`）

`wom/engine/backward_planner.py` に Phase 3b として `_apply_mom_cap_backward()` を追加。
`mom_constrained=True`（デフォルト）のとき、BackwardPlanner が MOM ノードの `psi4demand[w][P]` を cap_hard でクリップし、オーバーフロー分を CO として前週の S に押し戻す。

**設計意図（Plan Transforming Hypothesis）**: BackwardPlanner = Constrained Demand Allocation。
MOM ノードで cap_hard クリップ + CO前倒しを行うことで、`psi4demand[w][P]` = cap_hard 以内の実行可能計画が生成される。ForwardPlanner は（理想的には）この計画をコピーするだけで CO を発生させない。

```python
def _apply_mom_cap_backward(self, node, n_weeks, result):
    if node.node_type != "mom":
        return
    for w in range(n_weeks - 1, -1, -1):
        cap_w = node.cap_hard(w)
        if cap_w <= 0.0:
            continue
        s_lots = list(node.psi4demand[w][S])
        cap_int = int(cap_w)
        if len(s_lots) <= cap_int:
            continue
        within_cap = s_lots[:cap_int]
        overflow   = s_lots[cap_int:]
        node.psi4demand[w][P].clear()
        node.psi4demand[w][P].extend(within_cap)
        for lot_id in overflow:
            node.psi4demand[w][CO].append(lot_id)
        if w > 0:
            for lot_id in overflow:
                node.psi4demand[w - 1][S].append(lot_id)
        else:
            for lot_id in overflow:
                result.record_past_due(node.node_id, lot_id, w)
```

**`mom_constrained` フラグ**:
- `True`（デフォルト）: v1r0m3 動作。MOM cap_hard クリップ実行。
- `False`: v1r0m2 互換。既存テスト（`test_step7_capacity.py`, `test_step8_push_pull.py`）は `config={"mom_constrained": False}` で実行し v1r0m2 セマンティクスを保持。

### ForwardPlanner: PUSH MOM への Demand-S copy 除外

`wom/engine/forward_planner.py` の Phase 1 InBound 処理で、`plan_mode="push"` の MOM ノードには Demand-S copy（`psi4supply[w][P] = psi4demand[w][P]`）を適用しない条件を追加。Buffer_Wafer_TW（`plan_mode="pull"`, `is_decoupling=True`）には引き続き Demand-S copy が適用される。

---

### BackwardPlanner 純粋化：`_in_propagate` からクリッピング削除（v1r0m3後期）

**背景**: v1r0m2 の cap_hard envelope（`_in_propagate` 内のクリッピング）は、上流ノードが cap 前の全量需要を受け取れないという問題を持っていた。MOM の形状（CO あり）と TSMC_TW の形状（クリップ済み）が「少し異なる」という Osugiさんの観察がトリガー。

**変更内容**:
- `_in_propagate` の cap_hard clipping と is_decoupling fill-up ロジックを削除
- 純粋な LT offset 伝播のみ残す
- cap_hard enforcement は `_apply_mom_cap_backward`（MOM 専任）が担当
- 上流ノードは cap 前の全量需要を受け取り、ForwardPlanner が supply allocation を判断

**テスト更新**:
- `test_step7_capacity.py` の `cap_hard_sealed` 期待値を `0` → `2` に変更
  （v1r0m2: BackwardPlanner がクリップ → sealed=0 → v1r0m3: ForwardPlanner が enforce → sealed=demand-cap）

### DebugPanel PSI グラフに Capacity Line 追加（v1r0m3後期）

`app.py` の `_draw_psi_subplot` に `cap_values` 引数を追加。
`_refresh_charts` で `dbg.get_node(product, node_name)` から cap_hard を週次リストとして取得し、
グラフ左軸（lots）に橙色破線のステップ関数として描画する。

```python
# In _refresh_charts:
node_obj  = dbg.get_node(product, node_name)
cap_values = [node_obj.cap_hard(w) for w in range(n_weeks)] if node_obj else None

# In _draw_psi_subplot: step-line where cap > 0
if cap_values and any(v > 0 for v in cap_values):
    # cap_x/cap_y: horizontal segments, NaN breaks for cap=0 weeks
    ax.plot(cap_x, cap_y, color="#FF9800", linestyle="--", linewidth=1.2, label="Cap. Hard")
```

### app.py: v1r0m3 タイトル更新 + デフォルトサンプルパス修正

- タイトルバーを `v1r0m2` → `v1r0m3` に変更（3箇所）
- `_sample_dir` を `data/sample` → `data/sample/iphone-2027-2029` に変更（直下に `sc_tree_master.csv` がないため）

---

## v1r0m2 設計課題：Lead Time offset と DAD 回転在庫

### 背景（PySI v0r8 からの継承設計思想）

PySI v0r8 では BackwardPlanner が各エッジの Lead Time（LT）オフセットを計算する際、
Holiday Calendar の Long Holiday フラグを参照して閉鎖週をスキップする処理を
Planning Engine 内部で行っていた。
現行 WOM v1r0m1 ではこの LT offset が未実装であり、全ノードが同一週に
需要が発生するように扱われている（設計上の制約）。

### 現状の制約

- DADノード（DC等）の `psi4supply[w][I]` は常に 0（pass-through 設計）
- BackwardPlanner は LT オフセットなしで需要を逆伝播するため、
  上流ノードほど早い週に需要が配置されるべき「market requesting position」が
  正しく計算されていない
- 例: Week 10 に Retail_AMER で需要 100 lots、DC→Retail LT=1週、
  Foxconn→DC LT=2週 の場合、本来は Foxconn に Week 7 の需要として伝播すべきだが、
  現状は全ノードが Week 10 に配置される

### v1r0m2 向け役割分担設計

#### BackwardPlanner（LT計算 + Holiday Calendar 参照）
- LT オフセット計算: `week_idx -= lead_time_weeks`
- 閉鎖週スキップ: `explicit_closures`（PlanningContext 経由）を参照し、
  LT 計算中に閉鎖週があれば実質 LT を加算して正しい週に需要を配置する
  例: LT=2、W9 が閉鎖週 → W10 の需要を W7 に配置（閉鎖週1週分を追加オフセット）
- 責任範囲: 市場要求ポジションの正確な配置

#### HolidayCalendarPlugin
- `HOOK_PRE_PLAN (on_pre_plan)`:
  - cap_hard 設定（ForwardPlanner への能力制約）
  - `explicit_closures dict` を `PlanningContext` に書き込む
    （BackwardPlanner が参照するための共有データ）
- `HOOK_POST_BACKWARD (on_post_backward)`:
  - BackwardPlanner が誤って閉鎖週に配置した P-lot の残余修正（フォールバック）
- 責任範囲: ForwardPlanner の能力制約が主担当

#### ForwardPlanner（v1r0m2 で拡張）
- cap_hard に従って CO 生成（現行）
- DAD ノードの在庫計算を追加（`psi4supply[w][I]` が 0 固定から解放）
- `sc_tree_to_planning_df()` を DAD ノードも KPI 対象に拡張

#### 疎結合の維持方法
BackwardPlanner が HolidayCalendarPlugin のインスタンスに直接依存しないよう、
`sc_tree` または `PlanningContext` に `explicit_closures dict` を事前書き込みし、
BackwardPlanner はそれを参照するだけにする。

### 実装時のパフォーマンス考慮事項

`explicit_closures` は `dict[node_name, set[week_idx]]` 構造であり、
`week_idx in explicit_closures.get(node_name, set())` の lookup は O(1)。
ただし 156週 × 全ノード × 全 Lot のループ内での判定となるため、
以下の最適化を検討すること：
- `explicit_closures` は HOOK_PRE_PLAN で一度だけ構築し、計画期間全体で再利用
- BackwardPlanner 内では node ごとに closure_set を変数にキャッシュしてループ内参照を最小化
- 閉鎖週のない node（closure_set が空）は判定処理をスキップ

### 影響ファイル（v1r0m2 実装時）

| ファイル | 変更内容 |
| :---- | :---- |
| `sc_tree_master.csv` | `lead_time_weeks` 列追加（エッジ属性） |
| `wom/engine/backward_planner.py` | LT オフセット付き需要逆伝播 + 閉鎖週スキップ |
| `wom/engine/forward_planner.py` | DAD ノード在庫計算追加 |
| `wom/engine/holiday_calendar_plugin.py` | `explicit_closures` を PlanningContext に書き込む処理追加 |
| `wom/model/sc_tree.py` | エッジ属性として LT 保持 |
| `wom/engine/sc_tree_to_df.py` | DAD ノードも KPI DataFrame 対象に拡張 |

---

## WOM Original KPI Framework

### 設計思想：3次元 KPI アーキテクチャ

従来の財務 KPI ツリーは「財務指標 → 現場指標」へのトップダウン分解（静的・2次元）。
WOM の KPI フレームワークは根本的に異なる 3 次元構造を持つ：

```
次元1（空間軸）: SC Node  leaf_in → MOM → supply_point → DAD → leaf_out
次元2（財務軸）: KPI     現場活動指標 → 中間KPI → 事業損益 → 資本効率(ROE)
次元3（時間軸）: PSI週次  Week 1 → Week 2 → ... → Week 156（アニメーション可能）
```

静的な財務報告ではなく、**サプライチェーンの因果連鎖が時間軸で動く "活きた KPI"** を実現する。

---

### WOM SC Node × KPI マッピング

#### leaf_in（原材料・調達ノード）
調達起点の現場活動指標：

| WOM 指標 | PSI バケット | 上位 KPI への接続 |
| :---- | :---- | :---- |
| 調達 Lead Time (週) | P バケット配置週 | 工場部材在庫日数 → 棚卸資産回転日数 |
| サプライヤー納入精度 | P 実績 vs 計画差 | 欠品率 → 在庫補償費比率 |
| 調達ロック期間 (週) | 計画確定ホライズン | 部品関連変化対応率 → 販売機会損失率 |
| 調達単価 | ppc_supplier_cost | 直材費比率 → 売上原価率 |

#### MOM（製造・産地集荷ノード）
製造起点の現場活動指標：

| WOM 指標 | PSI バケット | 上位 KPI への接続 |
| :---- | :---- | :---- |
| 製造 Lead Time (週) | P→I バケット幅 | 工場仕掛在庫日数 → 棚卸資産回転日数 |
| 工場安全在庫日数 | `psi4supply[w][I]` / 週次出荷 | 棚卸資産回転日数 → 資産コスト |
| 生産能力充足率 (Fill Rate) | P 実績 / P 計画 | 欠品率 → 販売機会損失率 |
| 製造ノードコスト | ppc_node_cost_rule | 労務費比率 → 売上原価率 |
| Air 輸送発生率 | edge_cost（Air シナリオ） | Air コスト比率 → 物流コスト比率 |

#### supply_point（HQ Bridge ノード）
全体最適の調整指標：

| WOM 指標 | 役割 | 上位 KPI への接続 |
| :---- | :---- | :---- |
| Multi-MOM 配分比率 | lane_assignment.csv | 物流コスト比率・製造コスト比率 |
| Scenario Delta (Upside/Downside) | シナリオ感応度 | 変化対応率 → 販売機会損失率 |
| Tariff & FX 影響額 | Landed Cost engine | 売上原価率・物流コスト比率 |

#### DAD（DC・流通在庫ノード）
※ v1r0m1 現在 pass-through 設計。v1r0m2 で回転在庫を実装予定。

| WOM 指標 | PSI バケット | 上位 KPI への接続 |
| :---- | :---- | :---- |
| 販社在庫日数（回転在庫） | `psi4supply[w][I]`（v1r0m2〜） | 棚卸資産回転日数 → 資産コスト |
| DC → Retail 輸送 LT | エッジ属性（v1r0m2〜） | 販社配送 LT → 販社在庫日数 |
| DC スループット (週次) | S バケット | 物流コスト比率 → 販管費比率 |

#### leaf_out（販売チャネル・需要ノード）
市場起点の販売指標：

| WOM 指標 | PSI バケット | 上位 KPI への接続 |
| :---- | :---- | :---- |
| 需要予測精度 | demand_forecast vs 実績差 | 販売予測精度 → 変化対応率 |
| Fill Rate (充足率) | S 実績 / S 計画 | 販売機会損失率 → 売上高成長率 |
| Sell-through サイクル (週) | S バケット連続性 | デイリー在庫日数 → 販社在庫日数 |
| 販売チャネル Revenue | ppc_market_price × S | 売上高 → 事業損益 |
| Gross Profit / Profit Zone | PPC engine 出力 | 事業利益 → ROE |

---

### WOM KPI 集約ツリー（SC Node ボトムアップ → 財務 KPI）

```
ROE
├─ 事業損益（PPC engine が週次計算）
│   ├─ Revenue（売上高）
│   │   └─ 売上高成長率
│   │       ├─ Fill Rate（leaf_out: S実績/S計画）       ← 販売機会損失率
│   │       ├─ 需要予測精度（leaf_out: 予測vs実績）      ← 変化対応率
│   │       └─ Scenario Upside/Downside 感応度          ← 変化対応率
│   ├─ COGS（売上原価）
│   │   └─ 売上原価率
│   │       ├─ 直材費比率（leaf_in: ppc_supplier_cost）
│   │       ├─ 労務費比率（MOM: ppc_node_cost_rule）
│   │       └─ Tariff & FX 影響（supply_point: Landed Cost）
│   └─ 物流・販管費
│       └─ 物流コスト比率
│           ├─ Air コスト比率（MOM: edge_cost Air シナリオ）
│           └─ 通常輸送コスト（DAD: edge_cost Base シナリオ）
│
└─ 資産コスト（棚卸資産回転日数が主ドライバー）
    ├─ 棚卸資産回転日数
    │   ├─ 工場安全在庫日数（MOM: psi4supply[w][I] / 週次S）
    │   ├─ 工場仕掛在庫日数（MOM: 製造LTから算出）
    │   ├─ 販社在庫日数（DAD: psi4supply[w][I]、v1r0m2〜）
    │   └─ 工場部材在庫日数（leaf_in: 調達LTから算出）
    ├─ 売上債権回転日数
    │   └─ Sell-through サイクル（leaf_out: S バケット）
    └─ 固定資産
        └─ 製造設備稼働率（MOM: cap_hard 充足率）
```

---

### WOM KPI の時間軸展開（3次元目）

上記ツリーの各指標は **週次 PSI アニメーション**と連動する：

```
Week t の ROE 分解：
  Revenue[t]   = Σ leaf_out.psi4supply[t][S] × market_price
  COGS[t]      = Σ leaf_in.psi4supply[t][P]  × supplier_cost
                + Σ node.psi4supply[t][P]     × node_cost
  在庫資産[t]  = Σ MOM.psi4supply[t][I]      × unit_cost   （現行）
               + Σ DAD.psi4supply[t][I]      × unit_cost   （v1r0m2〜）
```

**これにより達成できること：**
- 特定週の Supply Shock（台風・関税引上げ）が ROE に波及するまでの因果連鎖を可視化
- Scenario Delta（Upside/Downside）が財務 KPI に与える感応度をアニメーションで確認
- 在庫日数の週次推移から「どの Node・どの週に在庫コストが集中するか」を特定

---

### v1r0m2 以降の実装優先度（KPI 完全性の観点から）

| 優先度 | 実装内容 | 解決する KPI ギャップ |
| :---- | :---- | :---- |
| ★★★ | DAD 回転在庫（`psi4supply[w][I]`） | 販社在庫日数 → 棚卸資産回転日数 |
| ★★★ | Lead Time offset（BackwardPlanner） | 工場部材在庫日数・工場仕掛在庫日数 |
| ★★  | Fill Rate の週次 KPI タブ表示 | 販売機会損失率の定量化 |
| ★★  | 棚卸資産回転日数の Management タブ追加 | 資産コスト → ROE 接続 |
| ★   | 需要予測精度の週次トラッキング | 変化対応率の定量化 |

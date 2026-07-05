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

- OutBound DADノードは「需要アンカー型ロット方式」のため `psi4supply[w][I]` は常に0（pass-through設計）  
- 実際のバッファ在庫はInBound MOMノードの `psi4supply[w][I]` に蓄積される  
- `Buffer Stock (DAD)` はWOMモデル用語として正しい（OutBound decoupling point）  
- `Buffer Stock (MOM)` はWOMモデル的に誤り（MOMはInBound supply管理点）  
- GUIのBuffer Stockチャートは実装上MOMノードのデータを参照している（OutBound DAD I=0のため）

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

- `app.py`はLinuxのbashでは約172KBで切り捨てられる。構文チェックはWindowsで行うこと: `python -c "import ast; ast.parse(open('wom/gui/app.py').read())"`  
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

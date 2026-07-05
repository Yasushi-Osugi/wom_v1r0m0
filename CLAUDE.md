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
最初の実装は単純に「在庫コスト最小」で候補をランキングしたところ、`supply_point`（仮想b
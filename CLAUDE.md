# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What is WOM

**WOM (Weekly Operation Model)** は週次PSI（Production/Sales/Inventory）を基本単位とするE2Eサプライチェーン計画・シミュレーションツール。Python \+ tkinter GUI。

- 起動: `python -m main`（GUIモード）/ `python -m main --cli`（ヘッドレス）  
- 現バージョン: v1r0m1（branch: `wom-v1r0m1`）  
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

## v1r0m1の開発方針

- v1r0m0（tag: `wom-v1r0m0`, commit: bbf0882）をベースラインとして保存済み  
- v1r0m1では **iPhone Global Supply Chain** モデルの整備を進める  
- `data/sample/iphone-2027-2029/` を参照・拡充する  
- コード変更はすべて `wom-v1r0m1` ブランチで行い、GitHubへpushする  
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

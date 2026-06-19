# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What is WOM

**WOM (Weekly Operation Model)** は週次PSI（Production/Sales/Inventory）を基本単位とするE2Eサプライチェーン計画・シミュレーションツール。Python \+ tkinter GUI。

- 起動: `python -m main`（GUIモード）/ `python -m main --cli`（ヘッドレス）  
- 現バージョン: v1r0m2（branch: `wom-v1r0m2`）  
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

## v1r0m2の開発方針

- v1r0m1（branch: `wom-v1r0m1`）をベースラインとして保存済み  
- v1r0m2では **Lead Time offset** と **DAD 回転在庫** の実装を進める  
- `data/sample/iphone-2027-2029/` を参照・拡充する  
- コード変更はすべて `wom-v1r0m2` ブランチで行い、GitHubへpushする  
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

## v1r0m2 実装済み機能（新しいClaude君へ）

### JIT週次同期：cap_hard envelope in `_in_propagate`（commit 7a22648）

`wom/engine/backward_planner.py` の `_in_propagate` に cap_hard envelope を追加した。
Foxconn_CN の cap_hard（週次能力上限）を上流への伝播クリップとして使用し、
TSMC_TW・Buffer_Wafer_TW がFoxconn_CN と同一の階段波形（800→534→267→0）に
JIT同期する設計を実現。

```python
cap_w = node.cap_hard(w)
propagate_lots = all_lots[:int(cap_w)] if cap_w > 0 else all_lots
```

**設計意図：** Foxconn_CN = DBRのDrum（ペースメーカー）。cap_hard が
OutBound需要をクリップし、その信号が InBound 全体に伝播する。

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

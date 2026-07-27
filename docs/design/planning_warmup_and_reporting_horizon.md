# Planning Warm-up and Reporting Horizon 設計

- **Document Status**: Draft for Design Review
- **Target Release**: WOM v1r2m0 以降
- **Primary Scope**: Planning Start、Warm-up Period、Business Analysis Period、Reporting Horizon
- **Related Scenario**: `data/sample/soysauce-us-2027`
- **Related Integrated Design**: `docs/design/holiday_calendar_push_lead_time_and_planning_horizon.md`

> **重複に関する注記**  
> 本文書は、統合設計書
> [`holiday_calendar_push_lead_time_and_planning_horizon.md`](holiday_calendar_push_lead_time_and_planning_horizon.md)
> からテーマ別に切り出した設計書である。  
> 単独で参照・レビューできるようにするため、背景、設計原則、設定例、検証条件の一部を意図的に重複して記載している。


---

## 1. 目的

本設計は、WOMにおける計算期間と表示・評価期間を分離する。

対象となる期間概念は次のとおりである。

1. Planning Start
2. Planning Horizon
3. Planning Warm-up Period
4. Final Demand Start
5. Business Analysis Period
6. Reporting Start
7. Management Reporting Horizon

特に、2027-W01から需要が発生する醤油モデルで、2026年中に必要な調達・生産・輸送・在庫形成をPlanning Horizonへ含め、DC nodeの初期COを解消することを目的とする。

---

## 2. 問題の本質

現行AutoDetectは、`demand_forecast.csv` に存在する最初の週をPlanning Startとし、ユニーク週数をPlanning Horizonとする。

現状：

```text
Planning Start = 2027-W01
Planning Weeks = 104
```

しかし、2027-W01の最終需要を満たすには、2026年中に次の活動が必要である。

- 原材料手配
- 醸造
- 瓶詰
- FG_WH_Nodaへの事前配置
- 米国DCへの輸送
- 安全在庫形成

現状では、これらの一部または全部がPlanning Horizon外に切り落とされる。

その結果、供給側のLTやPush設定が正しくても、2027-W01付近のDCに初期COが発生する可能性がある。

---

## 3. 設計原則

### 3.1 Final Demand Startは変更しない

```text
Final Demand Start = 2027-W01
```

2026年に追加するゼロ需要行は、最終需要の発生を前倒しするものではない。

### 3.2 Planning Startを前倒しする

```text
Planning Engineの計算開始を2026年側へ前倒しする
```

これにより、販売開始前の供給準備をPlanning Engine内で表現する。

### 3.3 PlanningとReportingを分離する

```text
Planning Horizon
    計算に必要な全期間

Reporting Horizon
    経営評価・通常表示の対象期間
```

Warm-up期間はPSI内部状態には必要だが、通常のPPCや経営レポートでは非表示にできる。

---

## 4. 用語定義

| Term | Definition |
|---|---|
| Planning Start | Planning Engineが計算を開始する週 |
| Planning Horizon | Planning Engineが保持・計算する全期間 |
| Planning Warm-up Period | 最終需要前の調達・生産・輸送・初期在庫形成期間 |
| Final Demand Start | 実際の市場需要が開始する週 |
| Business Analysis Period | 販売、PSI、PPC、利益評価を行う主要期間 |
| Reporting Start | Standard ChartやPPC Reportの表示開始週 |
| Diagnostic Horizon | Warm-up期間を含む検証用表示期間 |

---

## 5. Warm-up Periodの設定水準

### 5.1 4週間の表示を可能にする最小設定

2027-W01より前の4週間：

```text
2026-W53  1 week before
2026-W52  2 weeks before
2026-W51  3 weeks before
2026-W50  4 weeks before
```

設定：

```text
Planning Start = 2026-W50
Planning Weeks = 108
```

この設定は、4週間の先行挙動をグラフで確認するための最小値である。

### 5.2 Push Lead Time 7週間を含む最小設定

```text
Planning Start = 2026-W47
Planning Weeks = 111
```

現行 `push_lead_time_weeks=7` をPlanning Horizon内に完全に含めるための最小設定である。

### 5.3 DC初期CO解消を目的とする推奨設定

米国DCまでには、Push Lead Timeだけでなく、Outbound LTとSafety Stockがある。

概算：

| Market | Outbound Lead / Buffer | Push 7 weeks included | Planning Start Guide |
|---|---:|---:|---|
| Japan | approx. 6 weeks | approx. 13 weeks | 2026-W41 |
| US West | approx. 13 weeks | approx. 20 weeks | 2026-W34 |
| US East | approx. 14 weeks | approx. 21 weeks | 2026-W33 |

米国東海岸の概念時間構造：

```text
Rest_US_East
← 1 week
DC_US_NY
← 6 weeks + safety stock 3 weeks
FG_WH_Noda
← 1 week + safety stock 3 weeks
SP / Bottling_Noda
← push lead time 7 weeks
```

推奨値：

```text
Planning Start          = 2026-W33
Planning Warm-up Period = 2026-W33 .. 2026-W53
Final Demand Start      = 2027-W01
Business Analysis       = 2027-W01 .. 2028-W52
Planning Weeks          = 125
```

---

## 6. `demand_forecast.csv` による現行実装

### 6.1 ゼロ需要行を追加する

現行AutoDetectへWarm-up期間を認識させるため、2026-W33～W53に全地域のゼロ需要行を追加する。

```csv
sku_id,region,week,quantity
Soy_Sauce,JP,2026-W33,0
Soy_Sauce,US_W,2026-W33,0
Soy_Sauce,US_E,2026-W33,0
Soy_Sauce,FR,2026-W33,0
Soy_Sauce,BE,2026-W33,0
Soy_Sauce,NL,2026-W33,0
```

上記を2026-W53まで繰り返す。

2027-W01以降の実需要は変更しない。

### 6.2 期待するAutoDetect結果

```text
[AutoDetect] period: 2026-W33 × 125 weeks
```

### 6.3 ゼロ需要行の意味

```text
誤った理解
    最終需要を2026年へ前倒しする

正しい理解
    最終需要は2027-W01のまま
    Planning Engineの計算開始だけを2026年へ前倒しする
```

---

## 7. `capacity_plan.csv` の同時延長

Demandだけを2026-W33まで延長し、Capacity Planを2027-W01開始のままにすると、Warm-up期間の能力が未設定になる。

現行仕様では、

```text
capacity = 0
```

が未設定・無制約として扱われるため、Warm-up期間だけ無限能力になる可能性がある。

したがって、`capacity_plan.csv` も同期間へ延長する。

```csv
sku_id,node_name,week,cap_hard,note
Soy_Sauce,Bottling_Noda,2026-W33,1500,瓶詰 週次能力
Soy_Sauce,Brewing_Noda,2026-W33,1500,醸造 週次能力
Soy_Sauce,Materials_JP,2026-W33,50000,素材供給 実質無制約
```

上記を2026-W53まで設定する。

---

## 8. 将来の期間設定

ゼロ需要行をCSVへ追加する方法は、現行AutoDetectを利用するための実装上の回避策である。

将来的には、期間をモデル設定として明示する。

推奨案1：

```yaml
planning_start_week: 2026-W33
planning_weeks: 125
reporting_start_week: 2027-W01
warmup_weeks: 21
```

推奨案2：

```yaml
business_start_week: 2027-W01
pre_horizon_weeks: 21
reporting_weeks: 104
```

推奨案3：

```yaml
planning:
  start_week: 2026-W33
  weeks: 125

reporting:
  start_week: 2027-W01
  weeks: 104
```

---

## 9. Engine・Chart・PPCの責任分離

```text
Planning Engine
    2026-W33から計算

PSI Internal State
    2026-W33から保持

Diagnostic Charts
    Warm-up Periodを含めて表示可能

Standard Charts
    2027-W01から表示

PPC Reports
    原則として2027-W01以降を評価
```

Warm-up期間に発生した調達費、製造費、輸送費、在庫形成費をPPCでどう扱うかは、別途会計・Reporting設計が必要である。

少なくとも、次を区別できるようにする。

```text
planning_week
business_week
reporting_included
```

---

## 10. Warm-up Periodの期待PSI

2027-W01より前：

| Node | Expected Behavior |
|---|---|
| Materials_JP | Pが先行して立ち上がる |
| Brewing_Noda | 醸造要求・供給が立ち上がる |
| Bottling_Noda | 瓶詰と一部在庫形成が始まる |
| FG_WH_Noda | 輸出前バッファ在庫が形成される |
| DC_US_SF | 初期安全在庫が形成される |
| DC_US_NY | 初期安全在庫が形成される |

2027-W01の販売開始時点：

```text
DC Inventory > 0
DC CO ≈ 0
Rest_US shipment = demand
```

---

## 11. 検証項目

| Check | Acceptance Guide |
|---|---|
| AutoDetect | `2026-W33 × 125 weeks` |
| Warm-up P | 2026年中に上流Pが発生する |
| Capacity | Warm-up期間にも通常能力が適用される |
| DC Opening Inventory | 2027-W01時点で在庫を保持する |
| Initial DC CO | 0または業務上許容範囲 |
| Rest Shipment | 2027-W01から需要どおり |
| Lot Identity | 先行週移動後もDemand Anchored Lot IDを維持 |
| Standard Report | 2027-W01以降を表示 |
| Diagnostic Report | Warm-up期間を含めて表示 |

---

## 12. 異常時の切り分け

2026-W33まで延長してもDC COが残る場合、Planning Horizon不足以外を確認する。

1. Lot IDの週移動不整合
2. Push supplyとDC demandのidentity mismatch
3. Forward propagation LT
4. Decoupling nodeの供給設定
5. Safety Stockの二重加算または未反映
6. Capacity shortage
7. Opening Inventoryの初期化
8. `transit_lt_wks` と `lt_wks` の意味混在
9. Reporting filterがWarm-up Lotを誤除外していないか

---

## 13. Auto Calculationの将来設計

必要Warm-up Weeksを、SC Treeの累積時間から自動算定する機能を検討する。

概念式：

```text
required_warmup_weeks
=
inbound_push_lead_time
+ outbound_cumulative_transit_lt
+ cumulative_safety_stock_weeks
+ optional_prebuild_buffer
```

市場ごとに必要値が異なる場合は最大値を使用する。

```text
planning_start_week
=
final_demand_start_week
- max(required_warmup_weeks_by_market)
```

自動算定値は、ユーザーがoverrideできるようにする。

---

## 14. Acceptance Criteria

- [ ] Final Demand StartとPlanning Startが分離される
- [ ] Warm-up期間がPlanning Horizonに含まれる
- [ ] `push_lead_time_weeks=7` を変更せずに先行供給を計算できる
- [ ] `demand_forecast.csv` のゼロ需要行で現行AutoDetectが動作する
- [ ] `capacity_plan.csv` も同期間へ延長される
- [ ] 2027-W01前にDC在庫が形成される
- [ ] 2027-W01付近の初期COが解消または合理的に説明される
- [ ] Standard ReportとDiagnostic Reportの表示期間を分離できる
- [ ] 将来の明示的な期間設定項目が定義されている

---

## 15. 設計判断

```text
Final Demand Start
    2027-W01のまま

Planning Start
    2026-W33

Planning Warm-up Period
    2026-W33 .. 2026-W53

Business Analysis Period
    2027-W01 .. 2028-W52

Planning Weeks
    125

Push Lead Time
    7 weeksのまま

Reporting Start
    2027-W01
```

DC初期COの解消は、Supply ChainのLTを短く見せることではなく、販売開始前の供給準備期間をPlanning Horizonへ正しく含めることで行う。

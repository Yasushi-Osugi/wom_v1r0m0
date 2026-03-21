WOM_Inherited_Architecture_v1.md

WOM Kernel 継承アーキテクチャ v1

1. Purpose

本設計は、WOM（Weekly Operation Model）の既存資産である
高速LOTベースPSI Planning Engine を中核に保持したまま、

Traceability

Visual Debugger

Planning Application GUI

を統合するためのアーキテクチャを定義する。

基本思想は以下の通り。

Truth     = Weekly PSI State
Event     = Explainable Transition
Decision  = Planning Rationale

Planning Engine をイベント駆動に置き換えるのではなく、

Plan first
Event later
Explain always

という構造を採用する。

2. Architecture Overview
Planning Application Layer (3視GUI)
        ▲
        │
Visual Debugger v1
        ▲
        │
Planner-Driven Event Synthesis
        ▲
        │
State / Event / Decision Repository
        ▲
        │
Planning Engine Core (WOM PSI Engine)

レイヤー責務

Layer	Role
Planning GUI	意思決定
Visual Debugger	観測・説明
Event Synthesis	状態→イベント生成
Repository	状態・イベント・判断履歴
Planning Engine	PSI生成
3. Core Data Model

WOMのTraceabilityは 3層モデルで定義する。

State
Event
Decision
3.1 State Dataclasses

Stateは Planning Engineの真実の状態。

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class LotState:
    lot_id: str
    product_id: str
    quantity_cpu: float
    current_node: str
    status: str
    created_time_bucket: str


@dataclass
class NodeInventoryState:
    node_id: str
    product_id: str
    inventory_qty: float
    reserved_qty: float
    backlog_qty: float
    inbound_qty: float
    outbound_qty: float


@dataclass
class EdgeFlowState:
    from_node: str
    to_node: str
    product_id: str
    flow_qty: float


@dataclass
class WeeklyPSIState:
    time_bucket: str
    lot_states: List[LotState]
    node_inventory: List[NodeInventoryState]
    edge_flows: List[EdgeFlowState]
    kpi_snapshot: Dict[str, float]
3.2 Event Dataclasses

Eventは 状態遷移の説明ログ。

Eventには2種類ある。

Type	Description
Native Event	Engine内部で発生
Derived Event	State差分から生成
@dataclass
class EventRecord:
    event_id: str
    event_type: str

    time_bucket: str
    seq_no: int

    lot_id: Optional[str]
    product_id: Optional[str]

    from_node: Optional[str]
    to_node: Optional[str]

    quantity_cpu: Optional[float]

    related_demand_id: Optional[str]
    related_sale_id: Optional[str]

    caused_by_decision_id: Optional[str]

    metadata: Optional[dict]
3.3 Decision Dataclasses

Decisionは Traceabilityの中核。

Engineの重要判断点を記録する。

@dataclass
class CandidateEvaluation:
    candidate_id: str
    score: float
    reason: List[str]


@dataclass
class DecisionRecord:
    decision_id: str
    decision_type: str

    time_bucket: str

    context: Dict[str, str]

    candidates: List[CandidateEvaluation]

    selected_candidate: str

    applied_rule: str

    binding_constraints: List[str]

    resulting_event_ids: List[str]

    metadata: Optional[dict] = None

Decisionを記録する典型ケース

allocation

replenishment source selection

shortage decision

substitution selection

priority market decision

4. PlannerDrivenEventSynthesizer

Event Layerは Planning Engineの説明層。

Planning Engineを event-driven に変更しない。

4.1 Interface Definition
class PlannerDrivenEventSynthesizer:

    def generate_events_from_state_diff(
        self,
        previous_state: WeeklyPSIState,
        current_state: WeeklyPSIState
    ) -> List[EventRecord]:
        """
        State差分からDerived Eventを生成
        """

    def link_decisions_to_events(
        self,
        decisions: List[DecisionRecord],
        events: List[EventRecord]
    ) -> None:
        """
        Decision → Event の因果リンクを設定
        """

    def build_replay_frames(
        self,
        state: WeeklyPSIState,
        events: List[EventRecord]
    ):
        """
        Visual Debugger用のFrameを生成
        """

    def build_causality_graph(
        self,
        events: List[EventRecord],
        decisions: List[DecisionRecord]
    ):
        """
        Event / Decision 因果グラフ生成
        """
4.2 Event Generation Principle

Derived Event例

Event	Description
shipment_dispatched	node→node移動
shipment_arrived	edge→node
sale_consumed	lot消費
backlog_created	需要未充足
shortage_observed	node shortage
inventory_carry_over	週繰越
5. GUI State Schema

GUI状態は view_context で管理する。

3視思想

Dimension	Meaning
viewpoint	視点
view_scope	視野
view_position	視座
5.1 view_context
from dataclasses import dataclass


@dataclass
class ViewContext:

    viewpoint: str
    # lot | node | edge | event | product | market

    view_scope: str
    # network | region | node | lot_path | product_scope

    view_position: str
    # operation | planning | management | finance | service

    time_mode: str
    # week | event

    time_bucket: str
5.2 GUIState
@dataclass
class GUIState:

    scenario_id: str
    run_id: str

    view_context: ViewContext

    selected_object_type: Optional[str]
    selected_object_id: Optional[str]

    filters: Dict[str, str]

    replay_mode: str
    # pause | play

    replay_speed: float
6. Debugger v1 API Boundary

Visual Debuggerは 観測専用レイヤー。

Plannerを書き換えない。

6.1 Debugger Inputs
WeeklyPSIState
EventRecord
DecisionRecord
6.2 Debugger Queries
class DebuggerQueryAPI:

    def get_network_snapshot(
        self,
        run_id: str,
        time_bucket: str
    ) -> WeeklyPSIState:
        pass


    def get_event_timeline(
        self,
        run_id: str,
        time_range
    ) -> List[EventRecord]:
        pass


    def get_lot_lifecycle(
        self,
        lot_id: str
    ):
        pass


    def get_node_inventory_trace(
        self,
        node_id: str
    ):
        pass


    def get_event_detail(
        self,
        event_id: str
    ):
        pass


    def get_decision_trace(
        self,
        decision_id: str
    ):
        pass
7. Planning GUI API Boundary

Planning GUIは 意思決定レイヤー。

7.1 Planner API
class PlanningAPI:

    def run_planning(
        self,
        scenario_id: str
    ):
        pass


    def update_policy_parameter(
        self,
        parameter_name: str,
        value
    ):
        pass


    def run_scenario_comparison(
        self,
        scenario_a: str,
        scenario_b: str
    ):
        pass


    def update_supply_policy(
        self,
        product_id: str,
        policy
    ):
        pass
8. Responsibility Separation
Visual Debugger

役割

Replay
Inspect
Trace
Explain

扱う質問

何が起きたか
どこで変わったか
なぜそうなったか
Planning GUI

役割

Decision
Scenario design
Policy control
Management insight

扱う質問

何をすべきか
どの戦略が良いか
9. Key Design Principles
Principle 1

Planning Engine を
観測都合で遅くしない

Principle 2
Truth = State
Trace = Event
Reason = Decision
Principle 3

Decision Trace は
Engine実行時に記録

Principle 4

3視GUIは上位層
view_context は共通概念

10. Future Evolution

Visual Debuggerは将来

Event Debugger
→ Decision Debugger

へ進化する。

最終形

Event + Decision + Policy

を追跡できる Planning Intelligence Tool となる。
# WOM TOBE Image: Weekly Operation Management Simulator

**Version:** v0r1 draft  
**Date:** 2026-06-01  
**Status:** Design memo / North Star memo  
**Target path:** `docs/design/wom_tobe_management_simulator_image.md`

**Strategic role:** Define the north star of WOM as a management simulator connecting Weekly PSI quantity flow and Cost / Profit Structure money evaluation  
**Primary scope:** WOM TOBE image, management simulator concept, quantity-money connection, AI-supported modeling entrance  
**Current practical anchor:** Japanese Rice Case, then iPhone Case and Tesla Case

---

## 1. Purpose

This memo records the TOBE image of WOM.

WOM is not only a PSI planning tool.

WOM is intended to become a Weekly Operation Management Simulator.

The core idea is:

```text
Demand Anchored Lot Base Weekly PSI quantity model
    +
Cost / Profit Structure Ratio money model
    +
Market demand / capacity / lane change parameters
    ↓
Weekly management simulation and decision support
```

This memo defines the north star that should guide current and future WOM development.

---

## 2. Is This Vision Too Large?

The vision is large.

It may sound ambitious.

However, it is not merely a fantasy if it is developed through reproducible vertical slices, visible demos, and repo-based knowledge increments.

The correct stance is:

```text
Not a delusion.
A large hypothesis that must be proven by code, master data, tests, runners, and visible demos.
```

WOM should not try to change the world by slogans.

WOM should prove its value by showing:

```text
1. A realistic business scenario can be modeled.
2. Master data can be created with AI support.
3. Weekly lot-based PSI quantity behavior can be simulated.
4. Capacity constraints can create accepted / blocked lots.
5. Quantity impact can be connected to cost / profit structure.
6. Management can see the change and discuss actions.
```

The first goal is not recommendation AI.

The first goal is:

```text
Management-visible simulation that executives can understand and trust.
```

Recommendation AI should come later.

Visibility and trust must come first.

---

## 3. One-Sentence Definition

WOM is a Weekly Operation Management Simulator that connects a Demand Anchored Lot Base Weekly PSI quantity model with a Cost / Profit Structure money model, predicts and visualizes how market demand, capacity, and lane changes affect global business management, and supports executive decision-making.

In short:

```text
WOM connects weekly lot flow and business structure.
```

---

## 4. Management View of Business Character

In global headquarters management, executives often understand each business subsidiary not only through detailed accounting lines, but through its business character.

That business character appears as a relatively stable cost and profit structure.

Examples:

```text
fixed facility cost ratio
labor cost ratio
material / variable cost ratio
logistics cost ratio
indirect cost ratio
sales administration ratio
profit ratio
```

These ratios represent business body constitution.

They are not easy to change quickly.

They are similar to business DNA.

One executive described cost structure as:

```text
solid cost
liquid cost
gas cost
```

This expression captures the idea that some costs are rigid, some are semi-flexible, and some are easier to change.

WOM should be able to model this business character at a practical management resolution.

---

## 5. Cost / Profit Structure Ratio as Business Character

The WOM money model should not begin as a highly detailed product costing system.

It should begin as a management-level structure ratio model.

Recommended initial model:

```text
Product x Node x Business Unit
  - sales_price
  - material_cost_ratio
  - labor_cost_ratio
  - facility_fixed_cost_ratio
  - logistics_cost_ratio
  - indirect_cost_ratio
  - sales_admin_cost_ratio
  - profit_ratio
```

This is not meant to replace detailed ERP costing.

Instead, it provides a practical simulation model for management discussion.

Fine-grained product costing can be connected later through external interfaces.

WOM should avoid becoming a full ERP costing system.

The first objective is:

```text
Enough financial resolution for executive simulation.
```

Not:

```text
Full accounting precision.
```

---

## 6. Quantity Model: Demand Anchored Lot Base Weekly PSI

The core of the WOM quantity model is Demand Anchored Lot Base Weekly PSI.

The starting point is final market demand.

Demand generates lots.

Those lots move through the E2E supply chain.

The basic time bucket is week.

The core quantity model is:

```text
Market demand
    ↓
DemandAnchoredLot
    ↓
ProductPlanNode
    ↓
Weekly PSI
    ↓
Capacity / lane / leadtime constraints
    ↓
accepted / blocked / delayed / inventory / backlog behavior
```

This is a practical management resolution.

Daily or real-time control can be too detailed for executive simulation.

Monthly planning can be too coarse for global operations.

Weekly operation is a realistic middle layer.

---

## 7. Why Weekly?

Weekly is important because global supply chain operation often moves through practical weekly rhythms:

```text
production cycle
shipping schedule
container movement
warehouse operation
regional sales update
management review
```

WOM should use weekly buckets because they are detailed enough to show operational constraints but simple enough for executive scenario discussion.

This is the key balance:

```text
too fine:
  loses management visibility

too coarse:
  hides operational constraints

weekly:
  practical management resolution
```

---

## 8. Quantity and Money Connection

The strategic value of WOM comes from connecting quantity and money.

The quantity side answers:

```text
what
when
where
how many
through which route
under which capacity
accepted or blocked
```

The money side answers:

```text
sales impact
profit impact
cost structure impact
inventory impact
opportunity loss
capacity utilization impact
```

The connection is:

```text
Lot flow changes
    ↓
Weekly PSI quantity changes
    ↓
Sales / inventory / shortage changes
    ↓
Cost / profit structure evaluation
    ↓
Management KPI changes
```

This is the core backbone of WOM.

---

## 9. Change Parameters

WOM should treat the following as main change parameters.

### 9.1 Market demand change

Examples:

```text
demand increase
demand decrease
regional demand shift
seasonality
promotion effect
market shock
```

Market demand changes generate different DemandAnchoredLots.

### 9.2 Capacity change

Examples:

```text
factory capacity increase
factory capacity decrease
warehouse handling limit
transport capacity shortage
supplier bottleneck
distribution center constraint
```

Capacity changes create accepted / blocked / delayed lots.

### 9.3 Lane change

Examples:

```text
route change
transport mode change
leadtime change
transport capacity change
logistics cost change
risk exposure change
market response time change
```

Lane changes affect both quantity and money.

A lane is not only a route.

A lane is a management parameter that affects:

```text
leadtime
capacity
cost
inventory position
risk
service level
```

---

## 10. Management Evaluation

WOM should convert weekly lot behavior into management evaluation.

Examples:

```text
weekly accepted lots
weekly blocked lots
weekly capacity usage
weekly shortage
weekly inventory
weekly backlog
weekly revenue
weekly profit
weekly opportunity loss
weekly logistics cost
weekly working capital impact
```

The initial goal is not to optimize everything.

The initial goal is to make the change visible.

Management must be able to see:

```text
what changed
where it changed
when it changed
how much it changed
how it affects business structure
```

---

## 11. Decision Support Before Recommendation AI

A key development principle is:

```text
Visualization before recommendation.
```

Before WOM recommends actions, WOM must help executives understand the situation.

Recommended development order:

```text
1. Make the data visible.
2. Make the lot flow visible.
3. Make capacity constraints visible.
4. Make quantity impact visible.
5. Make money impact visible.
6. Then provide action options.
7. Then provide recommendation support.
8. Finally, develop operation decision agent capability.
```

Executive trust comes from visibility.

If WOM recommends too early, before the executive can see the simulation logic, WOM may feel like a black box.

The first deliverable should be:

```text
Management-visible simulation.
```

Recommendation AI should be built on top of that.

---

## 12. WOM as an AI-Supported Modeling Environment

WOM should become easier to customize through AI-supported master data modeling.

The future modeling workflow should be:

```text
User explains business scenario
    ↓
AI asks clarifying questions
    ↓
AI drafts WOM master data
    ↓
User reviews and corrects
    ↓
WOM runs simulation
    ↓
AI explains output
    ↓
User adjusts scenario
    ↓
WOM updates model
```

This creates a conversational modeling environment.

The important master categories are:

```text
network master
demand master
capacity master
lane / leadtime master
cost / profit structure master
scenario parameter master
```

The long-term value of WOM depends heavily on making this modeling entrance easier.

Traditional SCM tools often fail because master data preparation is too heavy.

WOM should use AI support to reduce that barrier.

---

## 13. Current Practical Anchor: Japanese Rice Case

The Japanese Rice Case is the first practical proof point.

Current achieved chain:

```text
capacity_master.csv
demand_master.csv
node_master.csv
network_master.csv
    ↓
ProductPlanNode tree
    ↓
MARKET_TOKYO.psi4demand[week][0]
    ↓
DC_KANTO capacity gate
    ↓
accepted_lot_ids / blocked_lot_ids
    ↓
run_japanese_rice_first_psi_vslice(...) diagnostic
```

Current visible result:

```text
2027-W40:
  accepted 80 / blocked 0

2027-W41:
  accepted 90 / blocked 5

2027-W42:
  accepted 90 / blocked 20

Total:
  accepted 260 / blocked 25
```

This is still small.

But it proves a fundamental behavior:

```text
Demand lots can be generated, placed on actual plan nodes, and split by capacity gate.
```

This is the first concrete step toward WOM as a management simulator.

---

## 14. Future Showcase Cases

WOM should eventually show multiple public cases.

### 14.1 Rice Case

Purpose:

```text
food supply
domestic supply-demand balance
capacity constraints
distribution bottlenecks
public-good style simulation
```

Core message:

```text
WOM can model essential goods and weekly capacity-constrained supply.
```

### 14.2 iPhone Case

Purpose:

```text
global manufacturing
component supply
regional demand
product lifecycle
channel inventory
launch-week pressure
```

Core message:

```text
WOM can model high-tech global supply chains.
```

### 14.3 Tesla Case

Purpose:

```text
EV demand
battery supply
factory capacity
regional lane constraints
price / profit impact
policy and tariff scenarios
```

Core message:

```text
WOM can model mobility and energy-transition businesses.
```

Together, these cases show the breadth of WOM:

```text
essential goods
high-tech consumer products
mobility / energy systems
```

---

## 15. Three-Year Management Planning Horizon

WOM should support a 3-year business management planning horizon.

The horizon should be weekly.

Example:

```text
3 years x 52 weeks = 156 weekly buckets
```

This is practical because:

```text
it is long enough for medium-term business planning
it is detailed enough for operational constraints
it is short enough to remain understandable
```

The goal is not only to simulate next week.

The goal is to simulate medium-term business scenarios.

Examples:

```text
demand growth scenario
capacity expansion scenario
lane disruption scenario
cost inflation scenario
profit structure improvement scenario
regional market shift scenario
```

---

## 16. WOM Output for Executives

The executive view should be simple and powerful.

Examples:

```text
weekly demand / capacity balance
accepted / blocked lots
inventory / backlog
sales / lost sales
profit / profit ratio
capacity usage
bottleneck node
lane impact
scenario comparison
```

The cockpit should answer:

```text
Where is the bottleneck?
When does it occur?
How many lots are affected?
How much sales or profit is affected?
Which scenario is better?
What action options exist?
```

The output must be understandable without requiring users to read the internal model.

---

## 17. Implementation Principle: Repo-Based Knowledge Increment

WOM development should continue to preserve knowledge through:

```text
design markdown
Codex request markdown
implementation commit
focused tests
completion memo
commit hash
```

This prevents important insights from being trapped in chat sessions.

The development unit should be:

```text
Knowledge Increment
```

Each increment should leave behind:

```text
why
what
how
test evidence
next step
```

This is especially important for long-term AI-supported development.

---

## 18. Suggested Architecture Backbone

The WOM architecture should maintain this backbone:

```text
Scenario Master Data
    ↓
Network / Demand / Capacity / Lane / Cost masters
    ↓
ProductPlanNode trees
    ↓
DemandAnchoredLots
    ↓
Weekly PSI quantity behavior
    ↓
Capacity / leadtime / lane constraints
    ↓
Accepted / blocked / delayed / inventory / backlog
    ↓
Cost / Profit Structure money evaluation
    ↓
Management cockpit
    ↓
Scenario comparison
    ↓
Decision support
```

The current Japanese Rice work is building the lower-middle part of this backbone:

```text
master data
ProductPlanNode
DemandAnchoredLots
capacity gate
accepted / blocked
runner diagnostic
```

The next major additions are:

```text
stable runner output
CLI / GUI display
Cost / Profit Structure Ratio
multi-gate capacity flow
leadtime-aware PSI
```

---

## 19. Development Priority

Recommended near-term priority:

```text
1. Stabilize runner output contract.
2. Create CLI smoke output.
3. Wire compact output to GUI / cockpit.
4. Add Cost / Profit Structure Ratio master.
5. Connect accepted / blocked lots to revenue / lost sales.
6. Add weekly management summary.
7. Extend to multi-gate capacity flow.
8. Add iPhone Case and Tesla Case.
```

This order keeps development grounded.

It avoids jumping too early into recommendation AI.

---

## 20. What WOM Should Avoid

WOM should avoid:

```text
trying to become a full ERP
trying to become a detailed accounting system
trying to become a black-box AI recommender too early
trying to model everything at once
trying to optimize before visualizing
trying to build GUI before stable output contract
```

The correct order is:

```text
visible first
trusted second
recommendation third
automation fourth
```

---

## 21. Management Simulator Image

WOM can be imagined as an executive cockpit.

```text
Engine:
  Weekly PSI Planning Engine

Fuel:
  DemandAnchoredLots

Road network:
  E2E Supply Chain Network / Lane

Traffic gates:
  Capacity constraints

Dashboard:
  Cost / Profit Structure and KPI

Pilot:
  Executive / planner / consultant

Co-pilot:
  AI-supported WOM customization assistant
```

This metaphor is useful because it shows that WOM is not only an engine.

WOM needs:

```text
engine
fuel
road
traffic gates
dashboard
pilot
co-pilot
```

The current development is connecting engine, fuel, road, and first traffic gate.

The next stage is dashboard.

---

## 22. TOBE Statement

The TOBE image of WOM is:

```text
WOM is a Weekly Operation Management Simulator that allows executives and planners to model global supply chain scenarios through AI-supported master data creation, simulate Demand Anchored Lot Base Weekly PSI quantity behavior, connect quantity changes to Cost / Profit Structure money evaluation, and visualize how market demand, capacity, and lane changes affect business performance over a medium-term planning horizon.
```

This TOBE image should guide implementation decisions.

---

## 23. Conclusion

The north star is clear.

WOM should first make the business situation visible.

Then it should make the management impact visible.

Then it should support decision options.

Only after that should WOM evolve toward recommendation AI and operation decision agent capability.

The current Japanese Rice Case is a correct and important first proof.

It demonstrates the path:

```text
business scenario
    ↓
AI-supported master definition
    ↓
weekly lot generation
    ↓
actual plan node placement
    ↓
capacity gate behavior
    ↓
management-visible diagnostic
```

If WOM can repeat this path for Rice Case, iPhone Case, and Tesla Case, then WOM will show that AI-supported supply chain master modeling and weekly management simulation can become practical.

This is the bridge from application software to a management dialogue environment.

It is an ambitious vision.

But it is a vision that can be tested, committed, and demonstrated step by step.

That is why it is worth pursuing.

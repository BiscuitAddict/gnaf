Consensus Layer – Weighted Reputation Quorum (v0.3)

Overview The GNAF Consensus Layer uses a reputation-weighted quorum system designed to mitigate two core problems: Quorum manipulation (including Sybil attacks)

Reputation gaming



This mechanism replaces simple majority voting with a merit-based, hierarchical model that strongly favors sustained high-quality contributions. Core Principles Reputation is earned, non-transferable, and time-decaying.

Quorum is measured by reputation weight, not node count.

High-reputation nodes carry significantly more influence.

Contractor/requester approval acts as an additional safeguard.



Mathematical Model1. Total Reputation Weight

TotalRep=∑i=1Nrepi\\text{TotalRep} = \\sum\_{i=1}^{N} \\text{rep}\_i\\text{TotalRep} = \\sum\_{i=1}^{N} \\text{rep}\_i

2\. Required Quorum Weight

QuorumWeight=threshold×TotalRep\\text{QuorumWeight} = \\text{threshold} \\times \\text{TotalRep}\\text{QuorumWeight} = \\text{threshold} \\times \\text{TotalRep}

3\. Minimum Nodes for Quorum

The smallest number of nodes k (sorted by descending reputation) such that:

∑i=1krep\[i]≥QuorumWeight\\sum\_{i=1}^{k} \\text{rep}\_{\[i]} \\geq \\text{QuorumWeight}\\sum\_{i=1}^{k} \\text{rep}\_{\[i]} \\geq \\text{QuorumWeight}

Key SafeguardsReputation Weight RulesMulti-dimensional reputation (Quality, Reliability, Collaboration, Expertise)

Exponential time decay: rep\_new = rep\_old × (1 - decay\_rate)^days

Vesting period: Newly earned reputation contributes only min(1.0, days\_earned / vesting\_days) of its value

Reputation is soulbound (non-transferable)



Quorum RequirementsBase threshold: 55–60% of total reputation weight for normal tasks

High-value contracts: 70%

Guild rule changes / constitutional decisions: 75%+

Minimum number of High-Rep Voters (rep > 1.5 × guild average) required in every quorum



Anti-Gaming MechanismsReputation gains only granted after validated task completion + peer/contractor review

Feedback from higher-reputation members weighs more heavily

Slashing: Malicious or consistently low-quality work reduces reputation (higher ranks risk more)

Diversity malus: Excessive influence from tightly connected subgroups is penalized

Hierarchical escalation: Parent guilds or federation can review suspicious local decisions



Example ScenariosNormal Guild (50 members, TotalRep = 1706, 60% threshold)Quorum needed: 1024

Minimum top nodes required: 18



Sybil Attack (20 low-rep attackers added)TotalRep increases only marginally

Minimum high-rep nodes required remains nearly unchanged → attack largely ineffective



Implementation NotesGuilds may adjust thresholds within allowed ranges defined by parent guild rules.

All reputation and quorum calculations must be deterministic and auditable.

Contractor approval is required in addition to weighted quorum for escrow release.

Sovereign jurisdiction fallback remains the final dispute resolution layer.






# 05 Topic Candidate Lanes

Generate formal candidates from a confirmed strategy search space plus attributable opportunity signals. The coordinator has no business-data write permission; it fans out to two isolated writers and then invokes an explicit mix gate.

```text
topic_id -> lane -> strategy_id -> strategy_assessment_id -> account_fit -> search_scope_ids -> signal_ids
```

`pain_id` is optional. Read the current strategy assessment before generating candidates. Its decision determines whether to reinforce the direction, search for a stronger angle, run a controlled validation topic, or compare with an explicitly labeled adjacent proposal. Every candidate must state its validation hypothesis.

Valid signals include audience pains, search interest, hot topics, industry signals, market tasks and content gaps. Creator posts, tutorials, viral videos, likes and views may validate attention or packaging, but may not redefine account strategy.

The conservative writer creates 60% of the candidate supply in `work/topics/conservative/current.json`. Every item must remain inside the confirmed core direction and pass persona, problem and first-person-proof gates.

The experimental writer creates 40% in `work/topics/experimental/current.json`. It may use fresher audience concerns and adjacent creative angles, but must still match the target persona and creator proof capability. Every item has a hypothesis and expiry; it never auto-promotes into the conservative lane.

The mix writer reads both ready lanes and writes `work/topics/selections/daily.json`. A three-topic day is exactly two conservative plus one experimental. It does not compute a global score or rewrite either lane. Topic-specific benchmark research starts only after this selection and cannot change lane membership.

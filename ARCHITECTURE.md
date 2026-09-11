# Signals, resolution and one combat path

## The problem

Gojomons has many systems that care about the same moment. Damage can trigger an item, a relic, a family ability, an animation, a sound, a combat log entry and a later campaign consequence. Connecting each producer directly to every consumer made new mechanics depend on unrelated files and made their lifetimes difficult to track.

Automatic balance testing created a second constraint. A headless simulator is useful only when it plays by the same rules as the live battle. Maintaining separate resolution paths invited quiet differences in effect order, status handling or random-number consumption.

## The first boundary: a shared event vocabulary

I introduced a central `EventDispatcher` and named `GameEvents`. Systems can announce facts such as a battle starting, damage being calculated, an item triggering, time advancing or a dungeon reward resolving without importing every observer.

```gdscript
func emit(event_name: String, context: Dictionary) -> void:
    if not handlers.has(event_name):
        return
    var current: Array = Array(handlers[event_name]).duplicate()
    for handler in current:
        if handler is Callable:
            handler.call(context)
```

The dispatcher is intentionally small. It rejects duplicate registration, removes empty event lists and copies the listener list before dispatch so a listener can register or unregister safely during an event.

Signals work well for observers and boundaries:

- the interface can react to an item, relic or master effect;
- campaign systems can observe travel, time, shops and dungeon outcomes;
- diagnostic tools can record events without changing the producer;
- scene-specific listeners can attach and detach with a defined lifetime.

## The second boundary: one authoritative resolver

Using events as a second path for combat mutation introduced a different risk. If live combat registered an effect handler while the simulator also called that effect directly, the effect could run twice. If only one path changed, live and simulated battles could disagree.

I consolidated state-changing combat in `CombatResolver`. Both consumers call the same await-free rules:

```text
                    ┌─ live TurnManager ── render result, play effects
intent ──► CombatResolver
                    └─ BattleSimulator ─── tally result, continue headlessly
```

The resolver applies damage, statuses, combat effects, bonus hits and queued healing to the battle state, then returns a result. The live turn manager presents that result. The simulator tallies it without loading the visual scene. Dramatic effect signals still fire from inside the shared path, so interface feedback remains decoupled without changing the outcome.

## Why the hybrid matters

The design uses signals where several independent systems need to observe a fact. It uses direct calls where one function must own an ordered state transition. The distinction prevents “decoupled” from becoming “unclear who changed the state.”

This produced several practical gains:

- Live battles and simulations share one resolution path.
- New interface or diagnostic reactions do not need combat-controller branches.
- Effect order and state mutation have an authoritative home.
- Headless regression tests exercise the rules used by the game.
- Temporary listeners and queued effects have explicit cleanup points.

## Working invariants

- An event name describes a fact or decision point rather than hiding an unrelated state change.
- `CombatResolver` owns authoritative combat mutation.
- Live presentation consumes resolver output; it does not resolve the action again.
- The simulator uses the same effect-enabled path as live combat.
- Listener and temporary-effect lifetimes end at an explicit scene, turn or battle boundary.
- Dispatch occurs in response to game events rather than per-frame polling.

The full game source remains private. The public simulation harness and recorded experiment show one consequence of this architecture: the combat rules can be exercised outside the playable interface while retaining the same resolution path.

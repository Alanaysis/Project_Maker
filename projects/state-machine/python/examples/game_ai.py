"""
Game AI State Machine Example

Demonstrates hierarchical state machine for game AI with:
- Nested states (Patrol has sub-states)
- History states
- Context-based decisions
- Guard conditions
"""

import sys
import random
from typing import Any, Dict

sys.path.insert(0, ".")

from src import (
    Event,
    State,
    HierarchicalState,
    HierarchicalStateMachine,
    Transition,
    FunctionGuard,
    FunctionAction,
)


# Define Base States
IDLE = State("Idle")
PATROL = HierarchicalState("Patrol", use_history=True)
CHASE = State("Chase")
ATTACK = State("Attack")
FLEE = State("Flee")
DEAD = State("Dead")

# Define Patrol Sub-States
PATROL_WALKING = State("Walking")
PATROL_WAITING = State("Waiting")
PATROL_CHECKING = State("Checking")

# Add sub-states to Patrol
PATROL.add_sub_state(PATROL_WALKING)
PATROL.add_sub_state(PATROL_WAITING)
PATROL.add_sub_state(PATROL_CHECKING)
PATROL.initial_state = "Walking"

# Define Events
SEE_ENEMY = Event("see_enemy")
LOSE_ENEMY = Event("lose_enemy")
ENEMY_NEAR = Event("enemy_near")
ENEMY_FAR = Event("enemy_far")
HEALTH_LOW = Event("health_low")
HEALTH_HIGH = Event("health_high")
DIE = Event("die")
RESPAWN = Event("respawn")
PATROL_COMPLETE = Event("patrol_complete")
TIMER = Event("timer")


# Define Guards
def has_low_health(from_state, to_state, event, context):
    """Check if health is low."""
    if context is None:
        return False
    return context.get("health", 100) < 30


def has_high_health(from_state, to_state, event, context):
    """Check if health is high."""
    if context is None:
        return False
    return context.get("health", 100) > 70


def is_enemy_near(from_state, to_state, event, context):
    """Check if enemy is nearby."""
    if context is None:
        return False
    distance = context.get("enemy_distance", float("inf"))
    return distance < 50


def is_enemy_far(from_state, to_state, event, context):
    """Check if enemy is far away."""
    if context is None:
        return False
    distance = context.get("enemy_distance", 0)
    return distance > 100


def has_ammo(from_state, to_state, event, context):
    """Check if has ammo."""
    if context is None:
        return False
    return context.get("ammo", 0) > 0


# Define Actions
def on_idle_enter(state, context):
    """Action when entering idle state."""
    print("  AI: Standing idle, looking around...")
    if context:
        context["idle_time"] = 0


def on_patrol_enter(state, context):
    """Action when entering patrol state."""
    print("  AI: Starting patrol...")


def on_patrol_exit(state, context):
    """Action when leaving patrol state."""
    print("  AI: Leaving patrol area")


def on_chase_enter(state, context):
    """Action when entering chase state."""
    print("  AI: Enemy spotted! Chasing...")
    if context:
        context["chasing"] = True


def on_attack_enter(state, context):
    """Action when entering attack state."""
    print("  AI: Engaging enemy!")
    if context:
        context["attacking"] = True


def on_flee_enter(state, context):
    """Action when entering flee state."""
    print("  AI: Health low! Retreating...")
    if context:
        context["fleeing"] = True


def on_dead_enter(state, context):
    """Action when entering dead state."""
    print("  AI: Defeated!")
    if context:
        context["alive"] = False


def on_respawn(state, context):
    """Action on respawn."""
    print("  AI: Respawning...")
    if context:
        context["health"] = 100
        context["ammo"] = 50
        context["alive"] = True
        context["attacking"] = False
        context["chasing"] = False
        context["fleeing"] = False


def patrol_walk(state, context):
    """Walking patrol action."""
    print("  AI: Walking patrol route...")


def patrol_wait(state, context):
    """Waiting patrol action."""
    print("  AI: Waiting at checkpoint...")


def patrol_check(state, context):
    """Checking patrol action."""
    print("  AI: Checking area...")


def attack_enemy(from_state, to_state, event, context):
    """Attack action."""
    if context:
        damage = random.randint(5, 15)
        context["ammo"] = max(0, context.get("ammo", 0) - 1)
        print(f"  AI: Attacking! Dealt {damage} damage. Ammo: {context['ammo']}")


def flee_action(from_state, to_state, event, context):
    """Flee action."""
    print("  AI: Running away to find health...")


def heal(from_state, to_state, event, context):
    """Heal action when fleeing."""
    if context:
        heal_amount = random.randint(10, 30)
        context["health"] = min(100, context.get("health", 0) + heal_amount)
        print(f"  AI: Healed {heal_amount}. Health: {context['health']}")


def log_transition(from_state, to_state, event, context):
    """Log transition."""
    print(f"  Transition: {from_state} -> {to_state}")


def create_game_ai() -> HierarchicalStateMachine:
    """
    Create a hierarchical state machine for game AI.

    Returns:
        Configured HierarchicalStateMachine instance
    """
    hsm = HierarchicalStateMachine(IDLE, enable_history=True)

    # Add entry/exit actions
    IDLE.add_entry_action(on_idle_enter)
    PATROL.add_entry_action(on_patrol_enter)
    PATROL.add_exit_action(on_patrol_exit)
    CHASE.add_entry_action(on_chase_enter)
    ATTACK.add_entry_action(on_attack_enter)
    FLEE.add_entry_action(on_flee_enter)
    DEAD.add_entry_action(on_dead_enter)

    # Patrol sub-state actions
    PATROL_WALKING.add_entry_action(patrol_walk)
    PATROL_WAITING.add_entry_action(patrol_wait)
    PATROL_CHECKING.add_entry_action(patrol_check)

    # Main transitions
    hsm.add_transition(Transition(
        from_state=IDLE,
        to_state=PATROL,
        event=TIMER,
        description="Start patrolling"
    ))

    # Chase transitions
    hsm.add_transition(Transition(
        from_state=PATROL,
        to_state=CHASE,
        event=SEE_ENEMY,
        action=FunctionAction(log_transition, "log"),
        description="Spot enemy while patrolling"
    ))

    hsm.add_transition(Transition(
        from_state=IDLE,
        to_state=CHASE,
        event=SEE_ENEMY,
        action=FunctionAction(log_transition, "log"),
        description="Spot enemy while idle"
    ))

    # Attack transitions
    hsm.add_transition(Transition(
        from_state=CHASE,
        to_state=ATTACK,
        event=ENEMY_NEAR,
        guard=FunctionGuard(has_ammo, "has_ammo"),
        action=FunctionAction(attack_enemy, "attack"),
        description="Enemy in range, attack!"
    ))

    # Flee transitions
    hsm.add_transition(Transition(
        from_state=CHASE,
        to_state=FLEE,
        event=HEALTH_LOW,
        action=FunctionAction(flee_action, "flee"),
        description="Health low while chasing"
    ))

    hsm.add_transition(Transition(
        from_state=ATTACK,
        to_state=FLEE,
        event=HEALTH_LOW,
        action=FunctionAction(flee_action, "flee"),
        description="Health low while attacking"
    ))

    # Return to patrol
    hsm.add_transition(Transition(
        from_state=CHASE,
        to_state=PATROL,
        event=LOSE_ENEMY,
        action=FunctionAction(log_transition, "log"),
        description="Lost enemy"
    ))

    hsm.add_transition(Transition(
        from_state=ATTACK,
        to_state=PATROL,
        event=LOSE_ENEMY,
        action=FunctionAction(log_transition, "log"),
        description="Lost enemy after attack"
    ))

    hsm.add_transition(Transition(
        from_state=FLEE,
        to_state=PATROL,
        event=HEALTH_HIGH,
        action=FunctionAction(heal, "heal"),
        description="Health recovered, resume patrol"
    ))

    # Death and respawn
    for state in [CHASE, ATTACK, FLEE]:
        hsm.add_transition(Transition(
            from_state=state,
            to_state=DEAD,
            event=DIE,
            action=FunctionAction(log_transition, "log"),
            description=f"Die from {state}"
        ))

    hsm.add_transition(Transition(
        from_state=DEAD,
        to_state=IDLE,
        event=RESPAWN,
        action=FunctionAction(on_respawn, "respawn"),
        description="Respawn"
    ))

    # Patrol sub-state transitions
    hsm.add_transition(Transition(
        from_state=PATROL_WALKING,
        to_state=PATROL_WAITING,
        event=TIMER,
        description="Walk to checkpoint"
    ))

    hsm.add_transition(Transition(
        from_state=PATROL_WAITING,
        to_state=PATROL_CHECKING,
        event=TIMER,
        description="Check area"
    ))

    hsm.add_transition(Transition(
        from_state=PATROL_CHECKING,
        to_state=PATROL_WALKING,
        event=PATROL_COMPLETE,
        description="Continue patrol"
    ))

    return hsm


def demo_patrol():
    """Demo patrol behavior."""
    print("=" * 60)
    print("Game AI - Patrol Demo")
    print("=" * 60)

    hsm = create_game_ai()
    context = {
        "health": 100,
        "ammo": 50,
        "alive": True,
        "enemy_distance": float("inf"),
    }

    print(f"\nInitial state: {hsm.current_state}")
    print(f"State stack: {[str(s) for s in hsm.state_stack]}")

    # Start patrolling
    print("\n--- Start Timer ---")
    hsm.process_event(TIMER, context)
    print(f"State: {hsm.current_state}")
    print(f"Stack: {[str(s) for s in hsm.state_stack]}")

    # Continue patrol cycle
    print("\n--- Continue Patrol ---")
    hsm.process_event(TIMER, context)
    print(f"State: {hsm.current_state}")

    print("\n--- Complete Patrol Cycle ---")
    hsm.process_event(PATROL_COMPLETE, context)
    print(f"State: {hsm.current_state}")


def demo_combat():
    """Demo combat behavior."""
    print("\n" + "=" * 60)
    print("Game AI - Combat Demo")
    print("=" * 60)

    hsm = create_game_ai()
    context = {
        "health": 100,
        "ammo": 50,
        "alive": True,
        "enemy_distance": 200,
    }

    print(f"\nInitial state: {hsm.current_state}")

    # Start patrol
    print("\n--- Start Patrol ---")
    hsm.process_event(TIMER, context)

    # See enemy
    print("\n--- Enemy Spotted! ---")
    context["enemy_distance"] = 150
    hsm.process_event(SEE_ENEMY, context)
    print(f"State: {hsm.current_state}")

    # Enemy approaches
    print("\n--- Enemy Approaches ---")
    context["enemy_distance"] = 30
    hsm.process_event(ENEMY_NEAR, context)
    print(f"State: {hsm.current_state}")

    # Attack multiple times
    for i in range(3):
        print(f"\n--- Attack {i + 1} ---")
        hsm.process_event(ENEMY_NEAR, context)

    # Health drops
    print("\n--- Health Drops! ---")
    context["health"] = 20
    hsm.process_event(HEALTH_LOW, context)
    print(f"State: {hsm.current_state}")

    # Flee and heal
    print("\n--- Heal Up ---")
    hsm.process_event(HEALTH_HIGH, context)
    print(f"State: {hsm.current_state}")


def demo_death_respawn():
    """Demo death and respawn."""
    print("\n" + "=" * 60)
    print("Game AI - Death & Respawn Demo")
    print("=" * 60)

    hsm = create_game_ai()
    context = {
        "health": 100,
        "ammo": 50,
        "alive": True,
        "enemy_distance": 200,
    }

    # Get to chase state
    hsm.process_event(TIMER, context)
    hsm.process_event(SEE_ENEMY, context)
    print(f"State: {hsm.current_state}")

    # Die
    print("\n--- AI Dies ---")
    hsm.process_event(DIE, context)
    print(f"State: {hsm.current_state}")
    print(f"Alive: {context.get('alive')}")

    # Respawn
    print("\n--- Respawn ---")
    hsm.process_event(RESPAWN, context)
    print(f"State: {hsm.current_state}")
    print(f"Health: {context.get('health')}")
    print(f"Alive: {context.get('alive')}")


def demo_history():
    """Demo history state."""
    print("\n" + "=" * 60)
    print("Game AI - History State Demo")
    print("=" * 60)

    hsm = create_game_ai()
    context = {
        "health": 100,
        "ammo": 50,
        "alive": True,
        "enemy_distance": 200,
    }

    # Get to patrol with sub-state
    print("\n--- Start Patrol ---")
    hsm.process_event(TIMER, context)
    print(f"State: {hsm.current_state}")

    print("\n--- Continue Patrol ---")
    hsm.process_event(TIMER, context)
    print(f"State: {hsm.current_state}")

    # Store current sub-state
    print(f"Current sub-state: {PATROL.current_sub_state}")

    # Leave patrol (chase enemy)
    print("\n--- Enemy Spotted ---")
    hsm.process_event(SEE_ENEMY, context)
    print(f"State: {hsm.current_state}")

    # Lose enemy, return to patrol
    print("\n--- Lose Enemy ---")
    hsm.process_event(LOSE_ENEMY, context)
    print(f"State: {hsm.current_state}")
    print(f"Restored sub-state: {PATROL.current_sub_state}")


if __name__ == "__main__":
    demo_patrol()
    demo_combat()
    demo_death_respawn()
    demo_history()

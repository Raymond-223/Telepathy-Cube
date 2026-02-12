from sentient_cube.control.state_machine import DualBrainStateMachine
from sentient_cube.models import Mode


def test_ambient_to_focus():
    sm = DualBrainStateMachine()
    snap = sm.on_event("wake_word")
    assert snap.mode == Mode.FOCUS


def test_focus_to_ambient():
    sm = DualBrainStateMachine()
    sm.switch(Mode.FOCUS, reason="manual")
    snap = sm.on_event("task_completed")
    assert snap.mode == Mode.AMBIENT


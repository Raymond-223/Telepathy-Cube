from sentient_cube.control.hardware import HardwareConfig, MockHardwareController, build_hardware_controller
from sentient_cube.core import SentientCubeCore


def test_build_mock_backend():
    controller = build_hardware_controller(HardwareConfig(backend="mock"))
    assert isinstance(controller, MockHardwareController)


def test_core_with_mock_hardware_config(tmp_path):
    db_path = tmp_path / "test.db"
    core = SentientCubeCore(
        db_path=str(db_path),
        hardware_config=HardwareConfig(backend="mock"),
    )
    status = core.status()
    assert status["hardware"]["mode"] == "ambient"
    core.close()


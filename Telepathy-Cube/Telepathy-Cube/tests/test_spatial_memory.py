from pathlib import Path

from sentient_cube.memory.spatial_memory import SpatialMemoryDB
from sentient_cube.models import ObjectMemory


def test_add_and_query_object(tmp_path: Path):
    db_path = tmp_path / "memory.db"
    db = SpatialMemoryDB(str(db_path))
    try:
        db.add_object(ObjectMemory(name="钥匙", location="桌面右侧", confidence=0.9))
        latest = db.latest_object("钥匙")
        assert latest is not None
        assert latest.name == "钥匙"
        assert latest.location == "桌面右侧"
    finally:
        db.close()


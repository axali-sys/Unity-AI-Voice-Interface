from xparallel.memory_vault import save_memory
from xparallel.memory_backup import create_backup, verify_backup, restore_backup


def test_backup_round_trip(tmp_path):
    db = tmp_path / "memory.sqlite3"
    directory = tmp_path / "backups"
    save_memory("first note", workspace_id="test", db_path=str(db))
    backup = create_backup(str(db), str(directory))
    assert verify_backup(backup["backup_id"], str(directory))["verified"]
    save_memory("second note", workspace_id="test", db_path=str(db))
    restored = restore_backup(backup["backup_id"], str(db), str(directory))
    assert restored["restored"]

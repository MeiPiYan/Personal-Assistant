"""Backup manager for database and configuration files."""

from __future__ import annotations

import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupManager:
    """Manages backups of the database and configuration files.

    Features:
    - Timestamped backups of DB and config
    - Restore from any backup
    - List available backups
    - Auto-cleanup of old backups
    - Auto-backup on startup and on interval
    """

    _instance = None

    def __new__(cls) -> BackupManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._backup_dir: Path = Path("data/backups")
        self._db_path: Path = Path("data/assistant.db")
        self._config_path: Path = Path("config/settings.yaml")
        self._max_backups: int = 10
        self._interval_hours: float = 24
        self._auto_on_startup: bool = True
        self._enabled: bool = True
        self._timer_task: Optional[asyncio.Task] = None

    def configure(
        self,
        backup_dir: str | Path = "data/backups",
        db_path: str | Path = "data/assistant.db",
        config_path: str | Path = "config/settings.yaml",
        max_backups: int = 10,
        interval_hours: float = 24,
        auto_on_startup: bool = True,
        enabled: bool = True,
    ) -> None:
        """Configure backup manager from settings."""
        self._backup_dir = Path(backup_dir)
        self._db_path = Path(db_path)
        self._config_path = Path(config_path)
        self._max_backups = max_backups
        self._interval_hours = interval_hours
        self._auto_on_startup = auto_on_startup
        self._enabled = enabled

    def _ensure_backup_dir(self) -> None:
        """Create backup directory if it doesn't exist."""
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _timestamp() -> str:
        """Return a timestamp string for filenames."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in a human-readable way."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    async def backup_database(self) -> dict:
        """Copy the current database file to the backup directory.

        Returns:
            dict with status, path, and size info, or error message.
        """
        if not self._enabled:
            return {"success": False, "error": "Backup is disabled"}

        if not self._db_path.exists():
            return {"success": False, "error": f"Database file not found: {self._db_path}"}

        self._ensure_backup_dir()
        ts = self._timestamp()
        dest = self._backup_dir / f"database_{ts}.db"

        try:
            # Use run_in_executor to avoid blocking the event loop with I/O
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, str(self._db_path), str(dest))
            size = dest.stat().st_size
            return {
                "success": True,
                "path": str(dest),
                "filename": dest.name,
                "size": size,
                "size_formatted": self._format_size(size),
                "timestamp": ts,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def backup_config(self) -> dict:
        """Copy the current config file to the backup directory.

        Returns:
            dict with status, path, and size info, or error message.
        """
        if not self._enabled:
            return {"success": False, "error": "Backup is disabled"}

        if not self._config_path.exists():
            return {"success": False, "error": f"Config file not found: {self._config_path}"}

        self._ensure_backup_dir()
        ts = self._timestamp()
        dest = self._backup_dir / f"settings_{ts}.yaml"

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, str(self._config_path), str(dest))
            size = dest.stat().st_size
            return {
                "success": True,
                "path": str(dest),
                "filename": dest.name,
                "size": size,
                "size_formatted": self._format_size(size),
                "timestamp": ts,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def backup_all(self) -> dict:
        """Backup both database and config.

        Returns:
            dict with results for each backup.
        """
        db_result = await self.backup_database()
        config_result = await self.backup_config()
        return {
            "database": db_result,
            "config": config_result,
        }

    async def restore_database(self, backup_path: str | Path) -> dict:
        """Restore database from a specified backup.

        Args:
            backup_path: Path to the backup file to restore.

        Returns:
            dict with status info.
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            return {"success": False, "error": f"Backup file not found: {backup_path}"}

        try:
            loop = asyncio.get_event_loop()

            # Create a safety backup of the current DB before restoring
            if self._db_path.exists():
                safety_ts = self._timestamp()
                safety_dest = self._backup_dir / f"database_pre_restore_{safety_ts}.db"
                self._ensure_backup_dir()
                await loop.run_in_executor(
                    None, shutil.copy2, str(self._db_path), str(safety_dest)
                )

            await loop.run_in_executor(
                None, shutil.copy2, str(backup_path), str(self._db_path)
            )
            return {
                "success": True,
                "message": f"Database restored from {backup_path.name}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def restore_config(self, backup_path: str | Path) -> dict:
        """Restore config from a specified backup.

        Args:
            backup_path: Path to the backup file to restore.

        Returns:
            dict with status info.
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            return {"success": False, "error": f"Backup file not found: {backup_path}"}

        try:
            loop = asyncio.get_event_loop()

            # Create a safety backup of the current config before restoring
            if self._config_path.exists():
                safety_ts = self._timestamp()
                safety_dest = self._backup_dir / f"settings_pre_restore_{safety_ts}.yaml"
                self._ensure_backup_dir()
                await loop.run_in_executor(
                    None, shutil.copy2, str(self._config_path), str(safety_dest)
                )

            await loop.run_in_executor(
                None, shutil.copy2, str(backup_path), str(self._config_path)
            )
            return {
                "success": True,
                "message": f"Config restored from {backup_path.name}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_backups(self) -> list[dict]:
        """Return available backups with timestamps and sizes.

        Returns:
            List of dicts sorted by timestamp descending (newest first).
        """
        self._ensure_backup_dir()
        backups = []

        for f in sorted(self._backup_dir.iterdir(), reverse=True):
            if f.is_file() and (
                f.name.startswith("database_") or f.name.startswith("settings_")
            ):
                # Parse type and timestamp from filename
                if f.name.startswith("database_"):
                    btype = "database"
                    # database_YYYYMMDD_HHMMSS.db
                    ts_part = f.name[len("database_"):-3]  # strip prefix and .db
                else:
                    btype = "config"
                    # settings_YYYYMMDD_HHMMSS.yaml
                    ts_part = f.name[len("settings_"):-5]  # strip prefix and .yaml

                # Format timestamp for display
                try:
                    dt = datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    display_time = ts_part

                stat = f.stat()
                backups.append({
                    "filename": f.name,
                    "path": str(f),
                    "type": btype,
                    "timestamp": ts_part,
                    "display_time": display_time,
                    "size": stat.st_size,
                    "size_formatted": self._format_size(stat.st_size),
                })

        return backups

    async def cleanup_old_backups(self, keep_count: int | None = None) -> dict:
        """Remove oldest backups beyond keep_count.

        Args:
            keep_count: Number of most recent backups to keep per type.
                        Uses configured max_backups if None.

        Returns:
            dict with count of removed files.
        """
        if keep_count is None:
            keep_count = self._max_backups

        self._ensure_backup_dir()
        removed = 0
        errors = []

        try:
            loop = asyncio.get_event_loop()

            # Group backups by type
            for prefix, ext in [("database_", ".db"), ("settings_", ".yaml")]:
                files = sorted(
                    [f for f in self._backup_dir.iterdir()
                     if f.is_file() and f.name.startswith(prefix) and f.name.endswith(ext)],
                    key=lambda f: f.stat().st_mtime,
                    reverse=True,
                )

                # Remove files beyond keep_count
                for f in files[keep_count:]:
                    try:
                        await loop.run_in_executor(None, f.unlink)
                        removed += 1
                    except Exception as e:
                        errors.append(f"{f.name}: {e}")

            return {
                "success": True,
                "removed": removed,
                "errors": errors,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "removed": removed}

    async def start_auto_backup(self) -> None:
        """Start the periodic auto-backup timer."""
        if not self._enabled or self._interval_hours <= 0:
            return

        # Cancel any existing timer
        self.stop_auto_backup()

        self._timer_task = asyncio.create_task(self._auto_backup_loop())

    def stop_auto_backup(self) -> None:
        """Stop the periodic auto-backup timer."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            self._timer_task = None

    async def _auto_backup_loop(self) -> None:
        """Internal loop that runs backups at configured intervals."""
        while True:
            try:
                await asyncio.sleep(self._interval_hours * 3600)
                # Perform backup and cleanup
                result = await self.backup_all()
                await self.cleanup_old_backups()
            except asyncio.CancelledError:
                break
            except Exception:
                # Silently continue - backup failure should not crash the app
                pass

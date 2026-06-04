import json
import csv
import io
from datetime import datetime
from pathlib import Path

from config.settings import LOG_DIR, EXPORT_DIR, SESSION_ID
from utils.encryption import EncryptionManager


class FileHandler:

    def __init__(self, encryption_manager: EncryptionManager = None):
        self.crypto = encryption_manager or EncryptionManager()
        self.log_dir = LOG_DIR
        self.export_dir = EXPORT_DIR

    def list_log_files(self) -> list:
        files = []
        for f in sorted(self.log_dir.glob("*.*"), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and f.name != "consent_records.json":
                files.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_kb": round(f.stat().st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "encrypted": f.suffix == ".enc",
                })
        return files

    def decrypt_log_file(self, filepath: Path) -> list:
        entries = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    decrypted = self.crypto.decrypt(line)

                    if decrypted.startswith("SESSION_HEADER:"):
                        entries.append({
                            "type": "header",
                            "data": json.loads(decrypted[15:]),
                        })
                    elif decrypted.startswith("SESSION_FOOTER:"):
                        entries.append({
                            "type": "footer",
                            "data": json.loads(decrypted[15:]),
                        })
                    else:
                        try:
                            parsed = json.loads(decrypted)
                            entries.append({
                                "type": "keystrokes",
                                "data": parsed,
                            })
                        except json.JSONDecodeError:
                            entries.append({
                                "type": "raw",
                                "data": decrypted,
                            })
        except Exception as e:
            entries.append({
                "type": "error",
                "data": f"Failed to read file: {e}",
            })

        return entries

    def export_logs(
        self,
        filepath: Path = None,
        output_format: str = "txt",
        output_name: str = None,
    ) -> Path:
        self.export_dir.mkdir(parents=True, exist_ok=True)

        if filepath:
            files = [filepath]
        else:
            files = list(self.log_dir.glob("keystroke_log_*.enc"))

        all_entries = []
        for f in files:
            entries = self.decrypt_log_file(f)
            all_entries.extend(entries)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_name is None:
            output_name = f"export_{timestamp}"

        if output_format == "json":
            return self._export_json(all_entries, output_name)
        elif output_format == "csv":
            return self._export_csv(all_entries, output_name)
        else:
            return self._export_txt(all_entries, output_name)

    def _export_json(self, entries: list, name: str) -> Path:
        output_path = self.export_dir / f"{name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, default=str)
        return output_path

    def _export_csv(self, entries: list, name: str) -> Path:
        output_path = self.export_dir / f"{name}.csv"
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Timestamp", "Key", "Data"])

            for entry in entries:
                if entry["type"] == "keystrokes" and isinstance(entry["data"], list):
                    for record in entry["data"]:
                        writer.writerow([
                            "keystroke",
                            record.get("timestamp", ""),
                            record.get("key", ""),
                            "",
                        ])
                elif entry["type"] == "header":
                    writer.writerow(["header", "", "", json.dumps(entry["data"])])
                elif entry["type"] == "footer":
                    writer.writerow(["footer", "", "", json.dumps(entry["data"])])
                else:
                    writer.writerow([entry["type"], "", "", str(entry["data"])])

        return output_path

    def _export_txt(self, entries: list, name: str) -> Path:
        output_path = self.export_dir / f"{name}.txt"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("  CyberSentinel - Exported Keystroke Log\n")
            f.write(f"  Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            for entry in entries:
                if entry["type"] == "header":
                    data = entry["data"]
                    f.write(f"--- Session Start: {data.get('started_at', 'Unknown')} ---\n")
                    f.write(f"    Session ID: {data.get('session_id', 'Unknown')}\n\n")
                elif entry["type"] == "keystrokes" and isinstance(entry["data"], list):
                    for record in entry["data"]:
                        key = record.get("key", "")
                        ts = record.get("timestamp", "")
                        if ts:
                            f.write(f"[{ts}] {key}")
                        else:
                            f.write(key)
                elif entry["type"] == "footer":
                    data = entry["data"]
                    f.write(f"\n\n--- Session End: {data.get('session_ended', 'Unknown')} ---\n")
                    f.write(f"    Total Keystrokes: {data.get('total_keystrokes', 0)}\n")
                    f.write(f"    Duration: {data.get('duration_seconds', 0):.0f} seconds\n")
                    f.write(f"    Avg KPM: {data.get('avg_keys_per_minute', 0)}\n")
                else:
                    f.write(str(entry["data"]))
                    f.write("\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("  End of Export\n")
            f.write("=" * 60 + "\n")

        return output_path

    def get_storage_stats(self) -> dict:
        total_size = 0
        file_count = 0

        for f in self.log_dir.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size
                file_count += 1

        return {
            "log_directory": str(self.log_dir),
            "export_directory": str(self.export_dir),
            "total_files": file_count,
            "total_size_mb": round(total_size / (1024 ** 2), 2),
        }

    def cleanup_old_logs(self, keep_days: int = 7) -> int:
        import time
        cutoff = time.time() - (keep_days * 86400)
        removed = 0

        for f in self.log_dir.glob("*.*"):
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1

        return removed

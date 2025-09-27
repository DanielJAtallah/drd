import os
import csv
from typing import List, Dict


class BufferedCSVWriter:
    """Append-only buffered CSV writer.

    Buffer rows in memory and write them in batches. Call close() at the end
    of your run to ensure any remaining rows are flushed.

    Example:
        writer = BufferedCSVWriter('data/sub_candidates.csv', cols, batch_size=500)
        for row in generator():
            writer.append(row)
        writer.close()
    """

    def __init__(
        self,
        path: str,
        fieldnames: List[str],
        batch_size: int = 500,
        encoding: str = "utf8",
    ):
        self.path = path
        self.fieldnames = fieldnames
        self.batch_size = batch_size
        self.encoding = encoding
        self.buffer: List[Dict] = []

        # ensure header exists
        if not os.path.exists(self.path):
            with open(self.path, "w", newline="", encoding=self.encoding) as f:
                csv.DictWriter(f, fieldnames=self.fieldnames).writeheader()

        # open file for append once
        self._file = open(self.path, "a", newline="", encoding=self.encoding)
        self._writer = csv.DictWriter(self._file, fieldnames=self.fieldnames)

    def append(self, row: Dict):
        """Add a single row to the buffer and flush if batch_size reached."""
        self.buffer.append(row)
        if len(self.buffer) >= self.batch_size:
            self.flush()

    def flush(self):
        """Write buffered rows to disk and flush the file handle."""
        if not self.buffer:
            return
        # writerows handles an empty list gracefully, but guard anyway
        self._writer.writerows(self.buffer)
        self._file.flush()
        # For the rare case where you need OS-level durability, uncomment:
        # import os as _os
        # _os.fsync(self._file.fileno())
        self.buffer.clear()

    def close(self):
        """Flush remaining rows and close the underlying file."""
        try:
            self.flush()
        finally:
            try:
                if not self._file.closed:
                    self._file.close()
            except Exception:
                pass

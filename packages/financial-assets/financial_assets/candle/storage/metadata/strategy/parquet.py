import json
from pathlib import Path
from threading import Lock
from .....stock_address import StockAddress
from .base import BaseMetadataStrategy
from simple_logger import init_logging, func_logging


class ParquetMetadataStrategy(BaseMetadataStrategy):
    # Parquet 메타데이터 전략 (JSON 파일 기반)

    @init_logging
    def __init__(self, config: dict):
        self.basepath = Path(config['basepath'])
        self.metadata_file = self.basepath / '_metadata.json'
        self._lock = Lock()

    @func_logging
    def get_last_update_ts(self, address: StockAddress) -> int | None:
        # 마지막 업데이트 타임스탬프 조회
        with self._lock:
            if not self.metadata_file.exists():
                return None

            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)

            address_key = address.to_filename()
            return metadata.get(address_key)

    @func_logging
    def set_last_update_ts(self, address: StockAddress, timestamp: int) -> None:
        # 마지막 업데이트 타임스탬프 저장
        with self._lock:
            # 기존 메타데이터 로드
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            # 업데이트
            address_key = address.to_filename()
            metadata[address_key] = timestamp

            # 저장
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

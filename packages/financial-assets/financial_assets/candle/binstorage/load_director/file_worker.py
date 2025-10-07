import os
import pyarrow.parquet as pq


class FileWorker:
    """StockAddress를 기반으로 parquet 파일을 읽어 DataFrame과 unit 반환"""

    def __init__(self, basepath: str):
        """
        Args:
            basepath: 파일이 저장된 기본 경로
        """
        self.basepath = basepath

    def __call__(self, address) -> tuple:
        """
        파일에서 DataFrame과 unit 로드

        Args:
            address: StockAddress 객체

        Returns:
            (DataFrame, unit)
        """
        # 파일명 생성
        filename = address.to_filename() + ".parquet"
        filepath = os.path.join(self.basepath, filename)

        # parquet 파일 로드
        table = pq.read_table(filepath)

        # 메타데이터에서 unit 추출
        unit = int(table.schema.metadata[b'unit'].decode())

        # DataFrame으로 변환
        df = table.to_pandas()

        return df, unit

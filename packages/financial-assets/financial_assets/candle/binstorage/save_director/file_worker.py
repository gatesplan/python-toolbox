import os
import pyarrow as pa
import pyarrow.parquet as pq


class FileWorker:
    """Candle 객체를 parquet 형식으로 저장"""

    def __call__(self, candle) -> None:
        """
        Candle 객체의 DataFrame을 파일로 저장
        unit 정보를 메타데이터에 저장

        Args:
            candle: Candle 객체
        """
        # 파일명 생성
        filename = candle.address.to_filename() + ".parquet"
        filepath = os.path.join(candle.basepath, filename)

        # 디렉토리가 없으면 생성
        os.makedirs(candle.basepath, exist_ok=True)

        # DataFrame을 Arrow Table로 변환
        table = pa.Table.from_pandas(candle.candle_df)

        # unit을 메타데이터에 추가
        metadata = {b'unit': str(candle._unit).encode()}
        existing_metadata = table.schema.metadata or {}
        merged_metadata = {**existing_metadata, **metadata}
        table = table.replace_schema_metadata(merged_metadata)

        # parquet으로 저장
        pq.write_table(table, filepath)

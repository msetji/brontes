from typing import List
from brontes.application.dtos.point_dto import PointReading

def test_setup_db(postgres_container, timescale):
  with timescale.postgres.cursor() as cur:
    cur.execute("""
      SELECT extname AS name FROM pg_extension
      UNION ALL
      SELECT table_name AS name FROM information_schema.tables WHERE table_schema = 'public'
      UNION ALL
      SELECT indexname AS name FROM pg_indexes WHERE tablename = 'timeseries'
    """)
    results = cur.fetchall()
    extensions = [row[0] for row in results if row[0] == "timescaledb"]
    table_names = [row[0] for row in results if row[0] == "timeseries"]
    indexes = [row[0] for row in results if row[0] == 'timeseries_timeseriesid_ts_idx']

    assert "timescaledb" in extensions
    assert "timeseries" in table_names
    assert "timeseries_timeseriesid_ts_idx" in indexes

def test_insert_timeseries(timescale):
  point_readings: List[PointReading] = [
    PointReading(value=20, timeseriesid="12345678", ts="2024-04-15T13:41:32+00:00")
  ]
  timescale.insert_timeseries(point_readings)

  points = timescale.get_timeseries(["12345678"], start_time="2024-02-15T13:41:32+00:00", end_time="2024-05-15T13:41:32+00:00")
  assert len(points) == 1

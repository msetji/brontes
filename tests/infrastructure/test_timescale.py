import unittest
from typing import List
from openoperator.infrastructure import Timescale, Postgres
from openoperator.domain.model import PointReading
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

class TestTimescale(unittest.TestCase):
  def setUp(self) -> None:
    postgres_continaer = DockerContainer("pg")
    postgres_continaer.start()
    self.postgres_continaer = postgres_continaer
    try:
      wait_for_logs(postgres_continaer, "listening on IPv4 address", timeout=30)
    except Exception as e:
      print(postgres_continaer.get_logs())
      raise e
    conn_string = 'postgresql://postgres:postgres@localhost:5432/postgres'
    self.postgres = Postgres(connection_string=conn_string)
    self.timescale = Timescale(postgres=self.postgres)

  def tearDown(self) -> None:
    self.postgres_continaer.stop()

  def test_setup_db(self):
    with self.postgres.cursor() as cur:
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

  def test_insert_timeseries(self):
    point_readings: List[PointReading] = [
      PointReading(value=20, timeseriesid="12345678", ts="2024-04-15T13:41:32+00:00")
    ]
    self.timescale.insert_timeseries(point_readings)

    points = self.timescale.get_timeseries(["12345678"], start_time="2024-02-15T13:41:32+00:00", end_time="2024-05-15T13:41:32+00:00")
    assert len(points) == 1


if __name__ == '__main__':
  unittest.main()
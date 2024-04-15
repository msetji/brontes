import unittest
from typing import List
from openoperator.infrastructure import Timescale, Postgres
from openoperator.domain.model import PointReading
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

class TestTimescale(unittest.TestCase):
  def setUp(self) -> None:
    postgres_container = DockerContainer("pg").with_exposed_ports(5432).with_bind_ports(5432, 5432)
    postgres_container.start()
    self.postgres_continaer = postgres_container
    try:
      wait_for_logs(postgres_container, "listening on IPv6 address", timeout=30)
    except Exception as e:
      print(postgres_container.get_logs())
      raise e
    ip_address = postgres_container.get_container_host_ip()
    conn_string = f'postgresql://postgres:postgres@{ip_address}:5432/postgres'
    print(conn_string)
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
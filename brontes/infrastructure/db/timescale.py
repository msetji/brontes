from typing import List
from dataclasses import asdict

from brontes.application.dtos.point_dto import PointReading # TODO: not sure if dto should be here
from .postgres import Postgres

class Timescale:
  def __init__(self, postgres: Postgres) -> None:
    self.postgres = postgres
    self.collection_name = 'timeseries'
    self.setup_db()
    
  def setup_db(self):
    """Make sure the timescaledb extension is enabled, the table and indexes are created"""
    try:
      with self.postgres.cursor() as cur:
        # Create timescaledb extension
        cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') 

        # Check if timeseries table exists
        cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{self.collection_name}\')') 
        if not cur.fetchone()[0]: 
          cur.execute(f'CREATE TABLE {self.collection_name} (ts timestamptz NOT NULL, value FLOAT NOT NULL, timeseriesid TEXT NOT NULL)') # Create timeseries table if it doesn't exist
          cur.execute(f'SELECT create_hypertable(\'{self.collection_name}\', \'ts\')') # Create hypertable if it doesn't exist
          cur.execute(f'CREATE INDEX {self.collection_name}_timeseriesid_ts_idx ON {self.collection_name} (timeseriesid, ts DESC)') # Create the timeseriesid index if it doesn't exist
          self.postgres.conn.commit()
    except Exception as e:
      raise e
  
  def get_timeseries(self, timeseriesIds: List[str], start_time: str, end_time: str) -> List[dict]:
    """Fetch timeseries data given some ids and a start and end time. Times should use ISO format string."""
    ids = ', '.join([f'\'{id}\'' for id in timeseriesIds])
    query = f"SELECT * FROM timeseries WHERE timeseriesid IN ({ids}) AND ts >= %s AND ts <= %s ORDER BY ts ASC"
    try:
      with self.postgres.cursor() as cur:
        cur.execute(query, (start_time, end_time))
        rows = cur.fetchall()
        result = []
        for id in timeseriesIds:
          data = [asdict(PointReading(ts=row[0].isoformat(), value=row[1], timeseriesid=row[2])) for row in rows if row[2] == id]
          result.append({'data': data, 'timeseriesid': id})
        return result
    except Exception as e:
      raise e
    
  def get_latest_values(self, timeseriesIds: List[str]) -> List[PointReading]:
    """
    Get the most recent reading for a list of timeseriesIds. Limit to the last 30 minutes.
    """
    ids = ', '.join([f'\'{id}\'' for id in timeseriesIds])
    query = f"SELECT DISTINCT ON (timeseriesid) * FROM timeseries WHERE timeseriesid IN ({ids}) AND ts >= NOW() - INTERVAL '30 minutes' ORDER BY timeseriesid, ts DESC"
    try:
      with self.postgres.cursor() as cur:
        cur.execute(query)
        return [PointReading(ts=row[0].isoformat(), value=row[1], timeseriesid=row[2]) for row in cur.fetchall()]
    except Exception as e:
      raise e
    
  def insert_timeseries(self, data: List[PointReading]) -> None:
    """
    Insert a list of timeseries data into the timeseries table.
    """
    query = "INSERT INTO timeseries (ts, value, timeseriesid) VALUES (%s, %s, %s)"
    values = [(reading.ts, reading.value, reading.timeseriesid) for reading in data]
    try:
      with self.postgres.cursor() as cur:
        cur.executemany(query, values)
        cur.execute('COMMIT')
    except Exception as e:
      raise e
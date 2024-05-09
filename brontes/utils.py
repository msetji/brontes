from typing import List
from urllib.parse import quote
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator
import numpy as np
import cv2
import tempfile
import os

def split_string_with_limit(text: str, limit: int, encoding) -> List[str]:
  """
  Splits a string into multiple parts with a limit on the number of tokens in each part.
  """
  tokens = encoding.encode(text)
  parts = []
  current_part = []
  current_count = 0

  for token in tokens:
    current_part.append(token)
    current_count += 1

    if current_count >= limit:
      parts.append(current_part)
      current_part = []
      current_count = 0

  if current_part:
    parts.append(current_part)

  text_parts = [encoding.decode(part) for part in parts]

  return text_parts

def create_uri(name: str) -> str:
  """
  Create a URI from string.
  """
  # name = re.sub(r'[^a-zA-Z0-9]', '', str(name).lower())
  # name = name.replace("'", "_")  # Replace ' with _
  name = quote(name.lower())
  return name

def dbscan_cluster(x):
  """
  DBSCAN clustering algorithm.
  """
  # Find the optimal epsilon
  n_neighbors = min(5, len(x))
  nbrs = NearestNeighbors(n_neighbors=n_neighbors).fit(x)
  distances, _ = nbrs.kneighbors(x)
  distances = np.sort(distances, axis=0)
  kneedle = KneeLocator(
    range(1, distances.shape[0] + 1), distances[:, 1], curve="convex", direction="increasing"
  )
  eps = kneedle.knee_y if kneedle.knee_y else 0.1
  db = DBSCAN(eps=eps, min_samples=3).fit(x)
  labels = db.labels_

  # Number of clusters in labels, ignoring noise if present.
  n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
  n_noise_ = list(labels).count(-1)

  print(f"Estimated number of clusters: {n_clusters_}")
  print(f"Estimated number of noise points: {n_noise_}")

  return labels

def video_thumbnail(file_content: bytes, sec = 0, width=320, height=240) -> bytes | None:
  """
  Given a video file content as bytes and a specific second, creates a thumbnail image of specified size.
  
  Args:
  file_content (bytes): The content of the video file.
  sec (int): The second at which the thumbnail should be captured.
  width (int): The width of the thumbnail in pixels.
  height (int): The height of the thumbnail in pixels.

  Returns:
  bytes: The bytes of the PNG thumbnail image, or None if an error occurs.
  """
  try:
    # Create a temporary file to write the video content
    with tempfile.NamedTemporaryFile(delete=False) as tvf:
      tvp = tvf.name
      tvf.write(file_content)

    # Load video file and set the frame position
    cap = cv2.VideoCapture(tvp)
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()  # Read the frame at the specified second
    cap.release()  # Release the video capture object
    os.unlink(tvp)  # Remove the temporary file

    if ret:
      # Resize the frame to the specified dimensions
      frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
      success, encoded_frame = cv2.imencode('.png', frame)  # Encode the frame as PNG
      if success:
        return encoded_frame.tobytes()  # Return the thumbnail as bytes
    else:
      print("Failed to capture frame.")
      return None
  except Exception as e:
    print(f"An error occurred: {e}")
    return None
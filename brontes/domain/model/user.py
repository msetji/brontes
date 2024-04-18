from pydantic import BaseModel

class User(BaseModel):
  email: str
  hashed_password: str
  full_name: str
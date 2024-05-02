from dataclasses import dataclass

@dataclass 
class Permission:
  name: str
  description: str

@dataclass
class Role:
  name: str
  description: str

@dataclass
class User:
  email: str
  hashed_password: str
  full_name: str
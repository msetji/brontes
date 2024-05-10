#!/usr/bin/env python

from typing import List, Generator, Optional
from dataclasses import asdict
import os
import json
import jwt
from io import BytesIO
from fastapi import FastAPI, UploadFile, Depends, Security, HTTPException, BackgroundTasks
from fastapi.responses import Response, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
import importlib.metadata

from brontes.domain.models import Portfolio, User, Facility, Document, Device, Point, Discipline
from brontes.application.dtos.document_dto import DocumentMetadataChunk, DocumentQuery
from brontes.application.dtos.device_dto import DeviceCreateParams
from brontes.application.dtos.point_dto import PointUpdates, PointCreateParams

### Infrastructure/External Services
from brontes.infrastructure import KnowledgeGraph, AzureBlobStore, Postgres, Timescale, OpenaiAudio, MQTTClient
## Langchain
embeddings = OpenAIEmbeddings()
vector_store = PGVector(
  collection_name=os.environ.get("POSTGRES_EMBEDDINGS_TABLE"),
  connection=os.environ.get("POSTGRES_CONNECTION_STRING"),
  embeddings=embeddings,
  use_jsonb=True
)
## Custom
knowledge_graph = KnowledgeGraph()
blob_store = AzureBlobStore()
postgres = Postgres()
timescale = Timescale(postgres=postgres)
audio = OpenaiAudio()
mqtt_client = MQTTClient()

### Repositories
from brontes.infrastructure.repos import PortfolioRepository, UserRepository, FacilityRepository, DocumentRepository, DeviceRepository, PointRepository, AIRepository
portfolio_repository = PortfolioRepository(kg=knowledge_graph)
user_repository = UserRepository(kg=knowledge_graph)
facility_repository = FacilityRepository(kg=knowledge_graph)
document_repository = DocumentRepository(kg=knowledge_graph)
point_repository = PointRepository(kg=knowledge_graph, ts=timescale)
device_repository = DeviceRepository(kg=knowledge_graph)
ai_repository = AIRepository(postgres=postgres, kg=knowledge_graph)

### Application Services
from brontes.application.services import PortfolioService, UserService, FacilityService, DocumentService, CobieToGraphService, DeviceService, PointService, BacnetToGraphService, AIAssistantService
portfolio_service = PortfolioService(portfolio_repository=portfolio_repository)
user_service = UserService(user_repository=user_repository)
facility_service = FacilityService(facility_repository=facility_repository)
document_service = DocumentService(document_repository=document_repository, vector_store=vector_store, blob_store=blob_store)
device_service = DeviceService(device_repository=device_repository, point_repository=point_repository)
point_service = PointService(point_repository=point_repository, device_repository=device_repository, mqtt_client=mqtt_client)
ai_assistant_service = AIAssistantService(document_service=document_service, portfolio_repository=portfolio_repository, ai_repository=ai_repository, facility_repository=facility_repository)
cobie_service = CobieToGraphService(blob_store=blob_store, kg=knowledge_graph, facility_repository=facility_repository)
bacnet_service = BacnetToGraphService(blob_store=blob_store, kg=knowledge_graph)

api_secret = os.getenv("API_TOKEN_SECRET")
app = FastAPI(title="Brontes API", version=importlib.metadata.version("brontes"))
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
  # If its local development, return a dummy user
  if os.environ.get("ENV") == "dev":
    return User(email="example@example.com", hashed_password="", full_name="Example User")
  if credentials is None or credentials.credentials is None:
    raise HTTPException(status_code=401, detail="Invalid token")
  token = credentials.credentials
  try:
    decoded = jwt.decode(token, api_secret, algorithms=["HS256"])
    email = decoded.get("email")  
    user = user_service.get_user(email)
    return user
  except HTTPException as e:
    raise e

## AUTH ROUTES 
@app.post("/signup", tags=["Auth"])
async def signup(email: str, password: str, full_name: str) -> JSONResponse:
  try:
    user_service.create_user(email, full_name, password)
    token = jwt.encode({"email": email}, api_secret, algorithm="HS256")  
    return JSONResponse({
      "token": token,
    })
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to create user: {e}"}, status_code=500)

@app.post("/login", tags=["Auth"])
async def login(email: str, password: str) -> JSONResponse:
  try:
    verified = user_service.verify_user_password(email, password)
    if not verified:
      return JSONResponse(content={"message": "Invalid credentials"}, status_code=401)
    token = jwt.encode({"email": email}, api_secret, algorithm="HS256")
    return JSONResponse({"token": token})
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to login: {e}"}, status_code=500)

## AI ROUTES
@app.post("/chat", tags=["AI"], response_model=Generator[str, None, None])
async def chat(
  input: str,
  session_id: str,
  portfolio_uri: str,
  facility_uri: str | None = None,
  document_uri: str | None = None,
  current_user: User = Security(get_current_user)
) -> StreamingResponse:
  """Session id must be a valid uuid string"""
  try:
    if document_uri and not facility_uri:
      raise HTTPException(status_code=400, detail="If a document_uri is provided, a facility_uri must also be provided.")
    
    async def event_stream() -> Generator[str, None, None]:
      async for chunk in ai_assistant_service.chat(user=current_user, session_id=session_id, input=input, portfolio_uri=portfolio_uri, facility_uri=facility_uri, document_uri=document_uri, verbose=False):
        yield f"event: {chunk['event']}\ndata: {json.dumps(chunk['data'])}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to chat: {e}"}, status_code=500)

@app.get("/chat/sessions", tags=["AI"])
async def get_chat_sessions(current_user: User = Security(get_current_user)) -> JSONResponse:
  return JSONResponse(ai_assistant_service.get_user_chat_session_history(current_user))

@app.post("/transcribe", tags=["AI"], response_model=str)
async def transcribe_audio(
  file: UploadFile,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    file_content = await file.read()
    buffer = BytesIO(file_content)
    buffer.name = file.filename
    return Response(content=audio.transcribe(buffer))
  except Exception as e:
    return JSONResponse(content={"message": f"Unable to transcribe audio: {e}"}, status_code=500)

## PORTFOLIO ROUTES
@app.get("/portfolio/list", tags=['Portfolio'], response_model=List[Portfolio])
async def list_portfolios(current_user: User = Security(get_current_user)) -> JSONResponse:
  portfolios = portfolio_service.list(current_user.email)
  return JSONResponse([asdict(portfolio) for portfolio in portfolios])

@app.post("/portfolio/create", tags=['Portfolio'], response_model=Portfolio)
async def create_portfolio(
  portfolio_name: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    portfolio = portfolio_service.create_portfolio(portfolio_name, current_user.email)
    return JSONResponse(asdict(portfolio))
  except Exception as e:
    return JSONResponse(content={"message": f"Unable to create portfolio: {e}"}, status_code=500)

## FACILITY ROUTES
@app.get("/facility/list", tags=['Facility'], response_model=List[Facility])
async def list_facilities(portfolio_uri: str, current_user: User = Security(get_current_user)) -> JSONResponse:
  return JSONResponse([asdict(facility) for facility in facility_service.list_facilities_for_portfolio(portfolio_uri)])    

@app.post("/facility/create", tags=['Facility'], response_model=Facility)
async def create_facility(
  portfolio_uri: str,
  facility_name: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    facility = facility_service.create_facility(facility_name, portfolio_uri)
    return JSONResponse(asdict(facility))
  except Exception as e:
    return JSONResponse(content={"message": f"Unable to create facility: {e}"}, status_code=500)

## DOCUMENTS ROUTES
@app.get("/documents", tags=['Document'], response_model=List[Document])
async def list_documents(
  facility_uri: str,
  space_uri: Optional[str] = None,
  type_uri: Optional[str] = None,
  component_uri: Optional[str] = None,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    #Validate
    if space_uri is not None and facility_uri+"/" not in space_uri:
      raise HTTPException(status_code=412, detail="The Space must belong to the same Facility") 
    
    if type_uri is not None and facility_uri+"/" not in type_uri:
      raise HTTPException(status_code=412, detail="The Type must belong to the same Facility") 
    
    if component_uri is not None and facility_uri+"/" not in component_uri:
      raise HTTPException(status_code=412, detail="The Space must belong to the same Facility") 
    
    docs = [asdict(doc) for doc in document_service.list_documents(facility_uri,space_uri,type_uri,component_uri)]
    return JSONResponse(status_code=200, content=docs)
  except Exception as e:  
    return JSONResponse(
      content={"message": f"Unable to list documents: {e}"},
      status_code=500
    )
  
@app.post("/documents/search", tags=['Document'], response_model=List[DocumentMetadataChunk])
async def search_documents(
  query: DocumentQuery,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse([asdict(chunk) for chunk in document_service.search(query)])

@app.post("/documents/upload", tags=['Document'])
async def upload_files(
  files: List[UploadFile],
  portfolio_uri: str,
  facility_uri: str,
  background_tasks: BackgroundTasks,
  discipline: Discipline = None,
  space_uri: Optional[str] = None,
  type_uri: Optional[str] = None,
  component_uri: Optional[str] = None,
  current_user: User = Security(get_current_user),
)-> JSONResponse:
  uploaded_files_info = []  # To store info about uploaded files.
  try:
    #validate 
    if portfolio_uri not in facility_uri:
      raise HTTPException(status_code=412, detail="The Facility must belong to the same Portfolio") 
    
    if space_uri is not None and facility_uri not in space_uri:
      raise HTTPException(status_code=412, detail="The Space must belong to the same Facility & Portfolio") 
    
    if type_uri is not None and facility_uri not in type_uri:
      raise HTTPException(status_code=412, detail="The Type must belong to the same Facility & Portfolio") 
    
    if component_uri is not None and facility_uri not in component_uri:
      raise HTTPException(status_code=412, detail="The Space must belong to the same Facility & Portfolio") 
    
    for file in files:
      try:
        file_content = await file.read()
        document = document_service.upload_document(portfolio_uri=portfolio_uri, facility_uri=facility_uri, file_content=file_content, file_name=file.filename, discipline=discipline, background_tasks=background_tasks, space_uri = space_uri, type_uri = type_uri, component_uri = component_uri)
        uploaded_files_info.append({"filename": file.filename, "uri": document.uri})
        
      except Exception as e:  
        return JSONResponse(
            content={"message": f"Unable to upload file {file.filename}: {e}"},
            status_code=500
        )
    return JSONResponse(status_code=200, content = {"message": "Files uploaded successfully", "uploaded_files": uploaded_files_info})
  except Exception as e:  
    raise e
  
@app.delete("/document/delete", tags=['Document'])
async def delete_document(
  document_uri: str,
  current_user: User = Security(get_current_user)
) -> Response:
  try:
    document_service.delete_document(document_uri)
    return JSONResponse(content={
      "message": "Document deleted successfully",
    })
  except Exception as e:
    return JSONResponse(
      content={"message": f"Unable to delete document: {e}"},
      status_code=400
    )
  
## DEVICES ROUTES
@app.get("/devices", tags=['Devices'], response_model=List[Device])
async def list_devices(
  facility_uri: str,
  component_uri: str | None = None,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    devices = device_service.get_devices(facility_uri=facility_uri, component_uri=component_uri)
    # for device in devices: # Remove the embedding from the response
    #   device.pop('embedding', None)
    devices = [asdict(device) for device in devices]
    return JSONResponse(devices)
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to list devices: {e}"},
        status_code=500
    )
  
@app.get("/device/graphic", tags=['Devices'])
async def get_device_graphic(
  facility_uri: str,
  device_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    return Response(
      device_service.get_device_graphic(facility_uri=facility_uri, device_uri=device_uri), 
      media_type="image/svg+xml"
    )
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to get device graphic: {e}"},
        status_code=500
    )

@app.post("/device/create", tags=['Devices'], response_model=Device)
async def create_device(
  facility_uri: str,
  device: DeviceCreateParams,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    device = device_service.create_device(facility_uri=facility_uri, device=device)
    return JSONResponse(asdict(device))
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to create device: {e}"},
        status_code=500
    )
  
@app.post("/device/link", tags=['Devices'])
async def link_to_component(
  device_uri: str,
  component_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    return JSONResponse(device_service.link_device_to_component(device_uri=device_uri, component_uri=component_uri))
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to link device to component: {e}"},
        status_code=500
    )
  
@app.put("/device/update", tags=['Devices'])
async def update_device(
  device_uri: str,
  new_details: dict,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    device_service.update(device_uri=device_uri, new_details=new_details)
    return JSONResponse(content={"message": "Device updated successfully"})
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to update device: {e}"},
        status_code=500
    )
  
## POINT ROUTES
@app.get("/points", tags=['Points'], response_model=List[Point])
async def list_points(
  facility_uri: str,
  component_uri: str | None = None,
  collect_enabled: bool = True,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  points = point_service.get_points(facility_uri=facility_uri, component_uri=component_uri, collect_enabled=collect_enabled)
  points = [asdict(point) for point in points]
  for point in points: # Remove the embedding from the response
    point.pop('embedding', None)
  return JSONResponse(points)

@app.get("/point", tags=['Points'], response_model=Point)
async def get_point(
  point_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  point = point_service.get_point(point_uri=point_uri)
  return JSONResponse(asdict(point))

@app.post("/point/create", tags=['Points'], response_model=Point)
async def create_point(
  facility_uri: str,
  device_uri: str,
  point: PointCreateParams,
  brick_class_uri: str | None = None,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    point = point_service.create_point(facility_uri=facility_uri, device_uri=device_uri, point=point, brick_class_uri=brick_class_uri)
    return JSONResponse(asdict(point))
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to create point: {e}"},
        status_code=500
    )

@app.post("/point/command", tags=['Points'])
async def command_point(
  point_uri: str,
  command: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    point_service.command_point(point_uri=point_uri, command=command)
    return JSONResponse(content={"message": "Command sent successfully"})
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to send command to point: {e}"},
        status_code=500
    )

@app.post("/points/history", tags=['Points'])
async def get_points_history(
  start_time: str,
  end_time: str,
  point_uris: List[str],
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse(point_service.get_points_history(start_time=start_time, end_time=end_time, point_uris=point_uris))

@app.put("/point/update", tags=['Points'])
async def update_point(
  point_uri: str,
  updates: PointUpdates | None = None,
  brick_class_uri: str | None = None,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    point_service.update_point(point_uri=point_uri, updates=updates, new_brick_class_uri=brick_class_uri)
    return JSONResponse(content={"message": "Point updated successfully"})
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to update point: {e}"},
        status_code=500
    )

## COBie ROUTES
@app.post("/cobie/import", tags=['COBie'])
async def import_cobie_spreadsheet(
  facility_uri: str, 
  file: UploadFile, 
  validate: bool = True,
  current_user: User = Security(get_current_user)
):
  try:
    file_content = await file.read()
    errors_found, errors = cobie_service.process_cobie_spreadsheet(facility_uri=facility_uri, file=file_content, validate=validate)
    if errors_found:
      return JSONResponse(content={"errors": errors}, status_code=400)
    return "COBie spreadsheet imported successfully"
  except HTTPException as e:
    return Response(content=str(e), status_code=500)
  
## BACNET INTEGRATION ROUTES
@app.post("/bacnet/import", tags=['BACnet'])
async def upload_bacnet_data(
  facility_uri: str,
  file: UploadFile,
  vectorize: bool = False,
  current_user: User = Security(get_current_user)
):
  try:
    file_content = await file.read()
    bacnet_service.upload_bacnet_data(facility_uri=facility_uri, file=file_content)

    return "BACnet data uploaded successfully"
  except HTTPException as e:
    return Response(content=str(e), status_code=500)
  
def start():
  print(f"ENV: {os.environ.get('ENV')}")
  reload = True if os.environ.get("ENV") == "dev" or os.environ.get("ENV") == "beta" else False
  uvicorn.run("brontes.application.api.app:app", host="0.0.0.0", port=8080, reload=reload)
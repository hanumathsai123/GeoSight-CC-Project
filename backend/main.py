from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path
from PIL import Image
import io, os, uuid, json, math
import numpy as np
import requests

try:
    import boto3
except Exception:
    boto3 = None

BASE = Path(__file__).resolve().parent.parent
UPLOADS = BASE / "data" / "uploads"
RESULTS = BASE / "data" / "results"
UPLOADS.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    app_name: str = "GeoSight"
    admin_email: str = "admin@geosight.local"
    admin_password: str = "Admin@123"
    cdse_stac_url: str = "https://stac.dataspace.copernicus.eu/v1"
    aws_region: str = "ap-south-1"
    aws_s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
app = FastAPI(title="GeoSight API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/files", StaticFiles(directory=str(BASE / "data")), name="files")

class LoginRequest(BaseModel):
    email: str
    password: str

class SearchRequest(BaseModel):
    bbox: list[float] = [77.45, 17.35, 78.65, 18.25]
    start_date: str = "2026-01-01"
    end_date: str = "2026-12-31"
    cloud_cover: float = 20

@app.get("/api/health")
def health():
    return {"status":"online","service":"GeoSight API","aws_configured": bool(settings.aws_s3_bucket and settings.aws_access_key_id)}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    if req.email.lower() == settings.admin_email.lower() and req.password == settings.admin_password:
        return {"ok": True, "token": "geosight-demo-session", "user": {"email": settings.admin_email, "role": "Administrator"}}
    raise HTTPException(status_code=401, detail="Invalid admin credentials")

@app.get("/api/stats")
def stats():
    return {"images_analyzed": 1284, "live_sources": 3, "cloud_status":"Connected", "processing_ms": 842, "storage":"S3 Ready" if settings.aws_s3_bucket else "Local Demo Storage"}

def analyze_image(im: Image.Image):
    rgb = np.asarray(im.convert("RGB").resize((512,512))).astype(np.float32)
    r,g,b = rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    green = (g > r*1.08) & (g > b*1.05) & (g > 55)
    water = (b > r*1.15) & (b > g*1.02) & (b > 65)
    urban = (np.std(rgb, axis=2) < 24) & (r > 70) & (g > 70) & (b > 70)
    other = ~(green | water | urban)
    counts = np.array([green.sum(), water.sum(), urban.sum(), other.sum()], dtype=float)
    pct = counts / counts.sum() * 100
    out = rgb.copy()
    out[green] = [40,210,100]
    out[water] = [40,130,245]
    out[urban] = [240,80,70]
    out[other] = [235,205,80]
    result = Image.fromarray(out.astype(np.uint8)).resize(im.size)
    return result, {"vegetation":round(float(pct[0]),1),"water":round(float(pct[1]),1),"built_up":round(float(pct[2]),1),"other":round(float(pct[3]),1)}

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Please upload an image file")
    raw = await file.read()
    try: im = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception: raise HTTPException(400, "Invalid image")
    job = uuid.uuid4().hex[:10]
    source = UPLOADS / f"{job}_{file.filename.replace('/','_')}"
    result = RESULTS / f"{job}_classified.png"
    source.write_bytes(raw)
    classified, metrics = analyze_image(im)
    classified.save(result)
    # Optional S3 upload
    s3_uploaded = False
    if boto3 and settings.aws_s3_bucket and settings.aws_access_key_id and settings.aws_secret_access_key:
        try:
            s3 = boto3.client("s3", region_name=settings.aws_region, aws_access_key_id=settings.aws_access_key_id, aws_secret_access_key=settings.aws_secret_access_key, aws_session_token=settings.aws_session_token or None)
            s3.upload_file(str(source), settings.aws_s3_bucket, f"uploads/{source.name}")
            s3.upload_file(str(result), settings.aws_s3_bucket, f"results/{result.name}")
            s3_uploaded = True
        except Exception as e:
            print("S3 upload failed:", e)
    return {"job_id":job,"source_url":f"/files/uploads/{source.name}","result_url":f"/files/results/{result.name}","metrics":metrics,"storage":"AWS S3" if s3_uploaded else "Local Demo Storage","message":"Analysis completed"}

@app.post("/api/satellite/search")
def satellite_search(req: SearchRequest):
    # STAC supports spatial/temporal/cloud-cover search for Sentinel-2 L2A.
    payload = {"collections":["sentinel-2-l2a"],"bbox":req.bbox,"datetime":f"{req.start_date}T00:00:00Z/{req.end_date}T23:59:59Z","query":{"eo:cloud_cover":{"lte":req.cloud_cover}},"limit":8,"sortby":[{"field":"datetime","direction":"desc"}]}
    try:
        r = requests.post(settings.cdse_stac_url + "/search", json=payload, timeout=15)
        r.raise_for_status(); data=r.json()
        features=[]
        for f in data.get("features",[]):
            p=f.get("properties",{})
            assets=f.get("assets",{})
            thumb=None
            for key in ["thumbnail","rendered_preview","visual"]:
                if key in assets: thumb=assets[key].get("href"); break
            features.append({"id":f.get("id"),"date":p.get("datetime"),"cloud_cover":p.get("eo:cloud_cover"),"thumbnail":thumb})
        return {"source":"Copernicus Data Space STAC","count":len(features),"items":features}
    except Exception as e:
        return {"source":"Demo fallback","count":3,"items":[{"id":"S2-DEMO-2026-001","date":"2026-09-20T05:30:00Z","cloud_cover":8.2},{"id":"S2-DEMO-2026-002","date":"2026-09-15T05:28:00Z","cloud_cover":12.6},{"id":"S2-DEMO-2026-003","date":"2026-09-09T05:25:00Z","cloud_cover":4.1}],"warning":str(e)}

@app.get("/api/architecture")
def architecture():
    return {"layers":[{"name":"Frontend","tech":"React + Vite","role":"Dashboard, upload, animation, maps/results"},{"name":"Backend","tech":"FastAPI + Python","role":"Authentication, image analysis, STAC search, AWS integration"},{"name":"Earth Observation","tech":"Copernicus Sentinel-2 / STAC","role":"Live satellite product discovery"},{"name":"Cloud","tech":"AWS S3 + optional EC2","role":"Object storage and deployment"}]}

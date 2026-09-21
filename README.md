# GeoSight — Cloud-Based Satellite Image Analysis

A demo-ready full-stack **Geo Science: Satellite Image Application** for a Cloud Applications course.

## What works
- Animated Earth with an orbiting satellite and space UI
- Admin login
- React + Vite frontend
- FastAPI + Python backend
- Image upload and deterministic land-cover demo analysis
- Original vs classified result viewer
- Live Sentinel-2 product metadata search through Copernicus Data Space STAC
- Optional AWS S3 upload for source/result images
- AWS-ready architecture explanation page
- Dockerfiles + docker-compose
- Sample satellite-style image: `data/demo_satellite.png`

## Demo login
- Email: `admin@geosight.local`
- Password: `Admin@123`

Change both values in `backend/.env` before any real deployment.

## Start locally — easiest method
### Terminal 1
```bash
./run-backend.sh
```

### Terminal 2
```bash
./run-frontend.sh
```

Open: `http://localhost:5173`

If the browser asks for a port, use the Vite URL shown in Terminal 2.

## Demo flow for your guide
1. Open GeoSight and show the animated Earth + satellite.
2. Sign in with the demo admin account.
3. Click **Analysis**.
4. Upload `data/demo_satellite.png`.
5. Click **Run Analysis**.
6. Explain: React → FastAPI → image processing → result → optional S3 storage.
7. Open **Datasets** → **Search Live Data** to query Sentinel-2 catalog metadata.
8. Open **Architecture** and explain Frontend → Backend → Sentinel-2/STAC → AWS.

## AWS setup
Copy the example file:
```bash
cp backend/.env.example backend/.env
```

Then set:
```env
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your-unique-bucket-name
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
```

The backend uploads the original image and classified result to S3 when valid AWS credentials and a bucket are configured. **Never put AWS credentials in the React frontend.** For deployment, prefer an IAM role on EC2/ECS instead of long-lived access keys.

## Real satellite data
The application queries:
`https://stac.dataspace.copernicus.eu/v1`

It searches the `sentinel-2-l2a` collection using bounding box, date range, and cloud-cover parameters. The response is satellite-product metadata; it should not be described as live video. Earth-observation imagery is captured when the satellite passes over the area.

## Technology stack
- Frontend: React, Vite, Lucide icons, CSS animations
- Backend: FastAPI, Pillow, NumPy, Boto3
- Earth Observation: Copernicus Data Space STAC / Sentinel-2
- Cloud: AWS S3; EC2-ready deployment

## Production upgrade path
Replace the demo classifier with a trained multispectral land-cover segmentation model, add PostgreSQL/RDS for analysis history, use Cognito/real identity management, and serve signed S3 URLs rather than public objects.
# GeoSight-CC-Project

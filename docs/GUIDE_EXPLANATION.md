# 2-minute guide explanation

**Project title:** GeoSight — Cloud-Based Satellite Image Analysis

**Problem:** Satellite imagery contains valuable information about vegetation, water and urban development, but users need a simple cloud application to search and analyze that imagery.

**Solution:** GeoSight is a full-stack cloud application. The React frontend provides an animated satellite/Earth interface and analysis dashboard. A FastAPI backend receives requests, performs image processing, searches the Copernicus Sentinel-2 catalog and optionally stores files in AWS S3. The system can be hosted on AWS EC2.

**Data:** Sentinel-2 Level-2A products are discoverable through the Copernicus Data Space STAC API. The application sends a spatial/temporal/cloud-cover query and displays returned product metadata.

**Cloud:** AWS S3 stores uploaded source imagery and generated result images. EC2 can host the FastAPI service. IAM controls access.

**Demo:** Sign in → Analysis → upload image → Run Analysis → show original/classified result → Datasets → Search Live Data → Architecture.

**Future scope:** NDVI from NIR/red bands, U-Net land-cover segmentation, temporal change detection, geospatial map overlays, object detection and scheduled satellite monitoring.

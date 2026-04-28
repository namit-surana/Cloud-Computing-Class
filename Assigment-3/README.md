# Cloud Computing Assignment 3 - AI Photo Search

This project implements an AI-powered photo search application using AWS services.

## Overview

The application allows users to:
- Upload photos with optional custom labels.
- Automatically index uploaded photos using Rekognition labels + custom labels.
- Search photos using natural language/keywords.
- View matching photo results in a web frontend.

## AWS Services Used

- Amazon S3
  - `b2-namit-a3-photos` (photo storage bucket)
  - `b1-namit-a3-frontend` (static website hosting bucket)
- AWS Lambda
  - `index-photos` (LF1)
  - `search-photos` (LF2)
  - `upload-photos` (upload API helper)
- Amazon Rekognition (`DetectLabels`)
- Amazon OpenSearch (`photos` domain/index)
- Amazon Lex V2 (`SearchIntent`)
- Amazon API Gateway
- AWS CodeBuild + CodePipeline
- AWS CloudFormation (minimal stack template)

## Architecture Flow

1. User uploads photo from frontend/API.
2. API uploads image to S3 photo bucket.
3. S3 `ObjectCreated` event triggers `index-photos` Lambda.
4. `index-photos`:
   - reads object bytes from S3,
   - gets labels from Rekognition,
   - reads custom labels from S3 metadata (`x-amz-meta-customLabels`),
   - stores combined labels into OpenSearch index `photos`.
5. User searches from frontend (`GET /search?q=...`).
6. `search-photos`:
   - disambiguates query via Lex/fallback keyword extraction,
   - queries OpenSearch,
   - returns matching photo URLs and labels.

## API Endpoints

- `PUT /photos` (or configured `PUT /` in current API deployment)
  - Upload photo bytes
  - Headers:
    - `x-api-key`
    - `Content-Type: image/jpeg` (or image type)
    - `x-amz-meta-customLabels: label1,label2`
- `GET /search?q={query}`
  - Search indexed photos
  - Header:
    - `x-api-key`

## Frontend

- Static website hosted on S3 frontend bucket.
- Main file: `index.html`
- Features:
  - search input + result cards
  - upload file + custom labels
  - status messages and error handling

## Repository/Project Files

- `index.html` - frontend app
- `index-photos/lambda_function.py` - indexing lambda (LF1)
- `search-photos/lambda_function.py` - search lambda (LF2)
- `upload-photos/lambda_function.py` - upload lambda
- `buildspec-backend.yml` - backend CodeBuild commands
- `buildspec-frontend.yml` - frontend CodeBuild commands
- `template.yaml` - minimal CloudFormation stack
- `codebuild-iam-policies.json` - IAM policy snippets for CodeBuild roles
- `FINAL_STEPS.md` - execution checklist

## CodePipeline Setup

Two pipelines are configured:

1. Backend pipeline (`a3-backend-pipeline`)
   - Source: GitHub backend repo (`main`)
   - Build: CodeBuild (`a3-backend-build`)
   - Buildspec updates Lambda code for `index-photos` and `search-photos`

2. Frontend pipeline (`a3-frontend-pipeline`)
   - Source: GitHub frontend repo (`main`)
   - Build: CodeBuild (`a3-frontend-build`)
   - Buildspec uploads `index.html` to frontend S3 bucket

## CloudFormation

`template.yaml` provides a minimal stack with:
- Frontend S3 bucket
- Photos S3 bucket
- Two Lambda functions (minimal placeholders)
- API Gateway REST API
- IAM roles for Lambdas

Note: Public bucket policy was intentionally removed from template to satisfy account-level S3 public access restrictions during stack creation.

## How to Run / Verify

1. Open frontend website URL from S3.
2. Upload a photo (with optional custom labels).
3. Confirm `index-photos` CloudWatch logs show successful indexing.
4. Search by Rekognition label (example: `person`).
5. Search by custom label (example: `sam`).
6. Confirm matching images appear in frontend.

## Acceptance Checklist

- [x] Photo upload works via API + frontend
- [x] S3 trigger invokes indexing lambda
- [x] Rekognition labels indexed in OpenSearch
- [x] Custom labels indexed and searchable
- [x] Search endpoint returns matching results
- [x] API key enforced for endpoints
- [x] Frontend hosted on S3 static website
- [x] Backend and frontend pipelines configured
- [x] CloudFormation minimal stack created

## Known Notes

- Search responses currently use pre-signed S3 URLs to ensure image rendering without requiring public-read access on the photos bucket.
- API path may be configured as `PUT /photos` or `PUT /` depending on final API Gateway configuration used during setup.


# Assignment 3 Final Steps

This checklist is tailored to your current setup.

## 1) Create GitHub repos

- Create `a3-backend` repo and add:
  - `index-photos/lambda_function.py`
  - `search-photos/lambda_function.py`
  - `buildspec.yml` (copy from `buildspec-backend.yml`)
- Create `a3-frontend` repo and add:
  - `index.html`
  - `buildspec.yml` (copy from `buildspec-frontend.yml`)

## 2) Create CodeBuild projects

- Backend project:
  - Name: `a3-backend-build`
  - Source: CodePipeline
  - Buildspec: `buildspec.yml`
  - Attach backend IAM policy from `codebuild-iam-policies.json`
- Frontend project:
  - Name: `a3-frontend-build`
  - Source: CodePipeline
  - Buildspec: `buildspec.yml`
  - Attach frontend IAM policy from `codebuild-iam-policies.json`

## 3) Create CodePipelines

- Pipeline 1:
  - Name: `a3-backend-pipeline`
  - Source: GitHub `a3-backend` main branch
  - Build: `a3-backend-build`
- Pipeline 2:
  - Name: `a3-frontend-pipeline`
  - Source: GitHub `a3-frontend` main branch
  - Build: `a3-frontend-build`

## 4) Test pipelines

- Push one commit to backend repo and verify both Lambdas update.
- Push one commit to frontend repo and verify S3 website updates.

## 5) Deploy CloudFormation template

- Open CloudFormation and create stack with `template.yaml`.
- If default bucket names are taken, override params:
  - `FrontendBucketName`
  - `PhotosBucketName`
- Verify stack status is `CREATE_COMPLETE`.
- Copy output `FrontendWebsiteURL`.

## 6) Final acceptance checks

- Upload via frontend/API works.
- `index-photos` logs show indexing success.
- Search returns matching photos.
- Custom labels are searchable.
- API key required for upload/search.
- Both pipelines show successful run.
- CloudFormation stack exists and outputs frontend URL.

## 7) Submission evidence (screenshots)

- Working frontend search/upload
- `index-photos` success log
- `search-photos` response with results
- CodePipeline P1 + P2 successful executions
- CloudFormation `CREATE_COMPLETE` and outputs

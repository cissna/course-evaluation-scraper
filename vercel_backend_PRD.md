# Product Requirements Document: Backend Code Reorganization

## Current State Analysis
- **Backend location**: Code is currently scattered between the root directory and `backend/` directory
- **Import structure**: Backend modules like `scraper_service.py` are in the root while the Flask app is in `backend/`
- **Deployment target**: Vercel for both frontend hosting and serverless Python functions (backend API)
- **Development requirement**: Need to support both local development and production deployment

## Problem Statement
1. **Deployment failure**: `vercel dev` fails because the backend in `backend/app.py` cannot import modules from the root directory (`scraper_service`, `db_utils`, etc.)
2. **Development complexity**: Current setup requires running separate Flask server alongside React dev server
3. **Future scalability**: Need to support batch scripts running from the root directory while maintaining Vercel deployment compatibility

## Requirements

### Functional Requirements
1. **Vercel deployment must succeed**: All backend modules must be importable when deployed to Vercel
2. **Local development must work**: Both single development command (`vercel dev`) and separate development workflows should function
3. **Root-level scripts must work**: Python scripts in the root directory must be able to import all backend modules
4. **No breaking changes to existing functionality**: Maintain the same API endpoints and functionality

### Technical Requirements
1. **Proper Python packaging**: Backend modules must be organized to support both relative imports within the backend and absolute imports from root scripts
2. **Vercel configuration compatibility**: The structure must work with Vercel's Python serverless function deployment
3. **Dependency management**: All required modules must be accessible regardless of the entry point

## Proposed Solution

### Backend Reorganization Strategy
1. **Move core modules into backend directory**: Move files like `scraper_service.py`, `db_utils.py`, `analysis.py`, etc. into the `backend/` directory
2. **Create proper Python package structure**: Add `__init__.py` files and update import paths
3. **Maintain root script compatibility**: Set up Python path or create a mechanism for root-level scripts to access backend modules
4. **Update Vercel configuration**: Ensure `vercel.json` properly handles imports

### Implementation Approach
1. **Package structure**: Convert backend directory into a proper Python package
2. **Import path updates**: Update all import statements to reflect new locations
3. **Root script compatibility**: Add relative import paths or modify Python path in root scripts
4. **Testing**: Verify both deployment and local development workflows

## Technical Considerations

### Vercel vs Local Development
- **Vercel deployment**: Python files are isolated in their own environment and only the specified entry point (`backend/app.py`) is accessible
- **Local development**: `vercel dev` should simulate this architecture locally
- **Serverless functions**: Each API endpoint runs in isolation, so all dependencies must be properly packaged

### Deployment Architecture
- **Vercel backend**: Python serverless functions that handle API requests
- **Vercel frontend**: Static React build that makes requests to API endpoints
- **Local development**: `vercel dev` should simulate this architecture locally

## Success Criteria
- `vercel dev` runs without import errors
- API endpoints are accessible during local development
- Root-level scripts can import backend modules for batch operations
- Production deployment to Vercel succeeds
- No functionality is broken by the reorganization

## Risks & Mitigation
- **Risk**: Import path changes break existing functionality
  - **Mitigation**: Thorough testing of all backend functionality after reorganization
- **Risk**: Vercel deployment fails due to packaging issues
  - **Mitigation**: Test deployment thoroughly with a staging environment before production

## Note on Alternative Approaches

Initially, there was consideration of running a separate Flask server for local development and proxying requests. However, this approach has been deemed unnecessary as the proper Vercel approach is to use `vercel dev` to simulate the production environment locally, where both frontend and backend run as they would in production. This ensures consistency between development and production environments.

This PRD outlines the requirements for reorganizing the backend code to support both Vercel deployment and future batch scripts. The key goal is to maintain the same functionality while making the codebase deployable to Vercel and maintainable for future features.
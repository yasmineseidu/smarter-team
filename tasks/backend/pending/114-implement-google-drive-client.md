# Task: Implement Google Drive Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Google Drive extending BaseIntegrationClient with Document storage and sharing.

## Integration Details

**Category:** Communication & Scheduling
**Base URL:** https://www.googleapis.com/drive/v3
**Authentication:** OAuth 2.0 (Google)
**Documentation:** https://developers.google.com/drive/api
**Special:** OAuth 2.0 with refresh tokens - supports file uploads

## Files to Create/Modify

- [ ] `app/backend/src/integrations/google_drive.py`
- [ ] `app/backend/__tests__/unit/integrations/test_google_drive.py`
- [ ] `app/backend/__tests__/fixtures/google_drive_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GoogleDriveClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GOOGLE_DRIVE_CREDENTIALS_JSON` environment variable
- [ ] Set base URL to `https://www.googleapis.com/drive/v3`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `list_files(query: str | None = None, **kwargs) -> list[dict] - List files`
- [ ] `upload_file(file_path: str, folder_id: str | None = None) -> dict - Upload file`
- [ ] `download_file(file_id: str) -> bytes - Download file`
- [ ] `create_folder(name: str, parent_id: str | None = None) -> dict - Create folder`
- [ ] `share_file(file_id: str, email: str, role: str = 'reader') -> dict - Share file`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GoogleDriveAPIError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting
- [ ] Log errors with context

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses
- [ ] Test error scenarios (401, 429, invalid requests)
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List key features and capabilities
- [ ] Note rate limits and best practices

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_google_drive.py -v

# Check coverage
pytest --cov=src/integrations/google_drive --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GOOGLE_DRIVE_CREDENTIALS_JSON`
- **Special**: OAuth 2.0 with refresh tokens - supports file uploads
- Primary use case: Document storage and sharing
- See https://developers.google.com/drive/api for full API reference

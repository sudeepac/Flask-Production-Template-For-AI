# Uploads Directory

This directory contains user-uploaded files and temporary file storage.

## Directory Structure

```
uploads/
├── README.md              # This file
├── images/                # Image uploads
│   ├── avatars/          # User profile images
│   ├── documents/        # Document images
│   └── temp/             # Temporary image files
├── documents/             # Document uploads
│   ├── pdfs/             # PDF files
│   ├── spreadsheets/     # Excel, CSV files
│   └── presentations/    # PowerPoint files
├── data/                  # Data file uploads
│   ├── datasets/         # ML training datasets
│   ├── models/           # User-uploaded models
│   └── exports/          # Exported data files
└── temp/                  # Temporary files
    ├── processing/       # Files being processed
    └── cache/            # Cached file operations
```

## File Upload Configuration

### Allowed File Types

**Images:**
- `.jpg`, `.jpeg` - JPEG images
- `.png` - PNG images
- `.gif` - GIF images
- `.webp` - WebP images

**Documents:**
- `.pdf` - PDF documents
- `.doc`, `.docx` - Microsoft Word
- `.xls`, `.xlsx` - Microsoft Excel
- `.ppt`, `.pptx` - Microsoft PowerPoint
- `.txt` - Plain text files

**Data Files:**
- `.csv` - Comma-separated values
- `.json` - JSON data
- `.xml` - XML data
- `.parquet` - Parquet data files

**Archives:**
- `.zip` - ZIP archives
- `.tar.gz` - Compressed tar archives

### File Size Limits

- **Images:** 5MB maximum
- **Documents:** 10MB maximum
- **Data files:** 50MB maximum
- **Archives:** 100MB maximum

### Security Measures

1. **File Type Validation**
   - MIME type checking
   - File extension validation
   - Magic number verification

2. **Content Scanning**
   - Virus scanning (if enabled)
   - Malicious content detection
   - File integrity checks

3. **Access Controls**
   - User-based file access
   - Temporary URL generation
   - File expiration policies

## File Processing Workflow

1. **Upload**
   - File validation
   - Temporary storage
   - Metadata extraction

2. **Processing**
   - File type specific processing
   - Thumbnail generation (images)
   - Text extraction (documents)
   - Data validation (datasets)

3. **Storage**
   - Permanent file storage
   - Database record creation
   - Cleanup of temporary files

## File Management

### Naming Convention

```
{user_id}_{timestamp}_{original_name}
```

Example: `user123_20240101120000_document.pdf`

### Metadata Storage

File metadata is stored in the database:

```python
class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    checksum = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### File Cleanup

- **Temporary files:** Cleaned up after 24 hours
- **Orphaned files:** Removed if no database record exists
- **User deletion:** Files removed when user account is deleted
- **Expired files:** Removed based on retention policies

## API Endpoints

### Upload File
```
POST /api/v2/files/upload
Content-Type: multipart/form-data

Parameters:
- file: File to upload
- category: File category (optional)
- description: File description (optional)
```

### Download File
```
GET /api/v2/files/{file_id}/download
Authorization: Bearer {token}
```

### Get File Info
```
GET /api/v2/files/{file_id}
Authorization: Bearer {token}
```

### Delete File
```
DELETE /api/v2/files/{file_id}
Authorization: Bearer {token}
```

## Storage Backends

### Local Storage (Default)
- Files stored in local filesystem
- Suitable for development and small deployments
- Configure path in `UPLOAD_FOLDER` environment variable

### Cloud Storage (Production)
- AWS S3
- Google Cloud Storage
- Azure Blob Storage
- Configure credentials in environment variables

## Monitoring and Maintenance

### Disk Usage Monitoring
- Monitor available disk space
- Set up alerts for low disk space
- Implement automatic cleanup policies

### Performance Optimization
- Use CDN for file delivery
- Implement file compression
- Cache frequently accessed files
- Use streaming for large file downloads

### Backup Strategy
- Regular backup of uploaded files
- Verify backup integrity
- Test restore procedures
- Document recovery processes

## Development Notes

### Testing File Uploads

```python
def test_file_upload(client, auth_headers):
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt'),
        'category': 'document'
    }
    response = client.post(
        '/api/v2/files/upload',
        data=data,
        headers=auth_headers,
        content_type='multipart/form-data'
    )
    assert response.status_code == 201
```

### File Processing Example

```python
from app.utils.file_processing import process_uploaded_file

def handle_file_upload(file):
    # Validate file
    if not allowed_file(file.filename):
        raise ValidationError('File type not allowed')
    
    # Save file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Process file
    result = process_uploaded_file(file_path)
    
    return result
```

## Security Best Practices

1. **Never trust user input**
   - Validate all file uploads
   - Sanitize file names
   - Check file contents

2. **Implement proper access controls**
   - Authenticate users
   - Authorize file access
   - Use temporary URLs

3. **Monitor for abuse**
   - Rate limit uploads
   - Monitor file sizes
   - Detect suspicious patterns

4. **Keep software updated**
   - Update file processing libraries
   - Apply security patches
   - Monitor security advisories
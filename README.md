# Basketball AI Backend

A comprehensive Django REST API backend for basketball video analysis, player detection, action recognition, and highlight generation using machine learning models including mmaction2, YOLOv8, and DeepSORT.

## Features

- **Video Upload & Processing**: Upload basketball game videos and process them asynchronously
- **Player Detection**: Automatic player detection and tracking using YOLOv8 + DeepSORT
- **Action Recognition**: Basketball action recognition using mmaction2 (TSN, SlowFast models)
- **Statistics Generation**: Automatic calculation of basketball statistics from detected actions
- **Highlight Generation**: AI-powered highlight video creation
- **RESTful API**: Complete REST API with JWT authentication
- **Async Processing**: Celery-based background task processing
- **Admin Interface**: Django admin for data management

## Technology Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis
- **Machine Learning**:
  - mmaction2 (action recognition)
  - YOLOv8 (object detection)
  - OpenCV (video processing)
  - MoviePy (video editing)
- **Authentication**: JWT tokens
- **File Storage**: Local storage (configurable to AWS S3)

## Implementation Status

### ✅ Complete Backend Implementation (11/11 Features)

1. **✅ Django Project Setup**

   - Project structure with modular apps
   - Production-ready settings configuration
   - Environment variable management

2. **✅ Database Models & Admin**

   - Complete database schema (Video, Player, Action, Highlight, Stats, UserProfile)
   - Django admin interface for all models
   - Proper relationships and constraints

3. **✅ DRF Serializers**

   - Comprehensive serializers for all models
   - Validation and field handling
   - Nested relationships and filtering

4. **✅ REST API Views**

   - Complete API endpoints as per specification
   - ViewSets and generic views
   - Proper permissions and authentication

5. **✅ Celery Configuration**

   - Redis broker setup
   - Async task processing
   - Docker Compose integration

6. **✅ Video Processing Pipeline**

   - Complete Celery task workflow
   - Player detection → Action recognition → Stats → Highlights
   - Error handling and status tracking

7. **✅ mmaction2 Integration**

   - TSN and SlowFast model support
   - Basketball action recognition
   - Configurable confidence thresholds

8. **✅ Video Processing Utilities**

   - OpenCV and MoviePy integration
   - Video segmentation and optimization
   - Thumbnail generation and scene detection

9. **✅ ML Models Setup**

   - YOLOv8 + DeepSORT player detection
   - Player tracking and team identification
   - Configurable model paths

10. **✅ File Handling & Storage**

    - Media file management
    - Local and S3 storage support
    - Secure file upload validation

11. **✅ Documentation & Deployment**
    - Comprehensive README
    - Docker containerization
    - Environment configuration examples

**Result**: Production-ready backend with all features from the MVP specification implemented.

## API Endpoints

### Authentication

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `POST /api/auth/change-password/` - Change password

### Videos

- `POST /api/upload/` - Upload video
- `POST /api/process/` - Start video processing
- `GET /api/status/<video_id>/` - Get processing status
- `GET /api/videos/` - List user videos

### Actions

- `POST /api/actions/infer/` - Start mmaction2 inference
- `GET /api/actions/` - List actions (filterable)
- `GET /api/actions/<id>/` - Get action details
- `GET /api/actions/summary/` - Get action summary for video

### Highlights

- `GET /api/highlights/` - List highlights
- `POST /api/highlights/` - Create highlight
- `GET /api/highlights/<id>/download/` - Download highlight video
- `POST /api/highlights/auto_generate/` - Auto-generate highlights

### Statistics

- `GET /api/stats/<video_id>/` - Get video statistics
- `GET /api/stats/<video_id>/download/?format=csv` - Export stats as CSV/JSON
- `GET /api/stats/summary/` - Get statistics summary

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- FFmpeg

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd basketball-ai-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb basketball_ai

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 5. Download ML Models

```bash
# Create model directories
mkdir -p models configs checkpoints

# Download YOLOv8 model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt

# Download mmaction2 models (follow mmaction2 documentation)
# Place config files in configs/ directory
# Place checkpoint files in checkpoints/ directory
```

### 6. Start Services

```bash
# Start Redis
redis-server

# Start Celery worker (in a new terminal)
celery -A basketball_ai worker --loglevel=info

# Start Celery beat (optional, for scheduled tasks)
celery -A basketball_ai beat --loglevel=info

# Start Django development server
python manage.py runserver
```

## Configuration

### Key Settings

Edit `basketball_ai/settings.py` or use environment variables:

```python
# Video processing settings
VIDEO_SEGMENT_LENGTH = 3  # seconds
MAX_VIDEO_DURATION = 3600  # 1 hour
SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv']

# ML Model paths
MMACTION2_CONFIG_PATH = 'path/to/config.py'
MMACTION2_CHECKPOINT_PATH = 'path/to/checkpoint.pth'
YOLO_MODEL_PATH = 'path/to/yolo.pt'
```

### Celery Configuration

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

## Usage Examples

### 1. Upload and Process Video

```python
import requests

# Upload video
files = {'file': open('game.mp4', 'rb')}
response = requests.post('http://localhost:8000/api/upload/',
                        files=files,
                        headers={'Authorization': 'Bearer <token>'})
video_id = response.json()['id']

# Start processing
requests.post('http://localhost:8000/api/process/',
              json={'video_id': video_id},
              headers={'Authorization': 'Bearer <token>'})

# Check status
status_response = requests.get(f'http://localhost:8000/api/status/{video_id}/',
                              headers={'Authorization': 'Bearer <token>'})
```

### 2. Start Action Recognition

```python
# Start mmaction2 inference
requests.post('http://localhost:8000/api/actions/infer/',
              json={
                  'video_id': video_id,
                  'model_type': 'mmaction2_tsn',
                  'confidence_threshold': 0.5
              },
              headers={'Authorization': 'Bearer <token>'})
```

### 3. Generate Highlights

```python
# Auto-generate highlights
requests.post('http://localhost:8000/api/highlights/auto_generate/',
              json={
                  'video_id': video_id,
                  'type': 'shooting_highlights',
                  'min_confidence': 0.7,
                  'max_duration': 60
              },
              headers={'Authorization': 'Bearer <token>'})
```

## Data Models

### Video Processing Pipeline

1. **Video Upload** → `uploaded` status
2. **Player Detection** → `players_detected` status
3. **Ball Analysis** → `ball_analyzed` status
4. **Action Recognition** → `actions_done` status
5. **Stats Calculation** → `highlights_created` status
6. **Highlight Generation** → `done` status

### Database Schema

- **Video**: Video files and metadata
- **Player**: Detected players in videos
- **Action**: Recognized basketball actions
- **Highlight**: Generated highlight videos
- **Stats**: Player statistics
- **UserProfile**: Extended user information

## Development

### Running Tests

```bash
python manage.py test
```

### Code Quality

```bash
# Install development dependencies
pip install flake8 black

# Format code
black .

# Lint code
flake8 .
```

### Database Migrations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## Deployment

### Production Settings

1. Set `DEBUG=False`
2. Configure proper `SECRET_KEY`
3. Set up proper database (PostgreSQL)
4. Configure Redis for Celery
5. Set up file storage (AWS S3)
6. Configure proper CORS settings

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## Performance Optimization

### Video Processing

- Use optimized video formats (H.264)
- Resize videos for processing if too large
- Process videos in segments for memory efficiency

### Database

- Add indexes for frequently queried fields
- Use database connection pooling
- Optimize query patterns

### Celery

- Use multiple worker processes
- Configure proper task routing
- Monitor task performance

## Troubleshooting

### Common Issues

1. **mmaction2 not found**: Ensure mmaction2 is properly installed
2. **CUDA out of memory**: Reduce batch size or use CPU processing
3. **Video processing fails**: Check video format and codec
4. **Celery tasks stuck**: Restart Celery workers

### Logs

Check logs in:

- `basketball_ai.log` - Application logs
- Celery worker console output
- Django console output

## API Documentation

Full API documentation is available at `/api/docs/` when running the server with DRF spectacular.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

- Create an issue in the repository
- Check the documentation
- Review the logs for error details

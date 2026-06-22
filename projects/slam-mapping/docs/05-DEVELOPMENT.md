# 05 - Development: SLAM System Development Guide

## Development Environment Setup

### Prerequisites

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **pip package manager**
   ```bash
   pip --version
   ```

3. **Git** (optional)
   ```bash
   git --version
   ```

### Installation Steps

1. **Clone or download project**
   ```bash
   cd projects/slam-mapping
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python -c "import cv2; print('OpenCV:', cv2.__version__)"
   python -c "import numpy; print('NumPy:', numpy.__version__)"
   ```

## Project Structure

```
slam-mapping/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration classes
│   ├── feature_extractor.py  # ORB feature extraction
│   ├── pose_estimator.py  # Camera pose estimation
│   ├── map_manager.py     # Map management
│   ├── loop_closure.py    # Loop closure detection
│   ├── visualizer.py      # 3D visualization
│   └── slam_system.py    # Main SLAM pipeline
├── tests/                  # Unit tests
├── docs/                   # Documentation
├── config/                 # Configuration files
├── data/                   # Data directory
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
└── README.md              # Project README
```

## Development Workflow

### 1. Understanding the Codebase

**Read order**:
1. `config.py` - Understand configuration
2. `feature_extractor.py` - Core feature extraction
3. `pose_estimator.py` - Pose estimation
4. `map_manager.py` - Map management
5. `slam_system.py` - Main pipeline

### 2. Making Changes

**Best practices**:
- Make small, focused changes
- Write tests for new functionality
- Update documentation
- Run tests before committing

### 3. Testing Changes

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_feature_extractor.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Core Concepts

### 1. Feature Extraction

**ORB Features**:
- FAST corner detector for keypoints
- BRIEF descriptor for feature description
- Rotation invariance
- Scale invariance (with pyramid)

**Code location**: `src/feature_extractor.py`

**Key classes**:
- `Frame`: Stores image and features
- `FeatureExtractor`: Extracts and matches features

### 2. Pose Estimation

**Essential Matrix Method**:
- Computes relative pose from 2D-2D correspondences
- Uses RANSAC for robustness
- Recovers rotation and translation

**Code location**: `src/pose_estimator.py`

**Key classes**:
- `Pose`: Stores rotation and translation
- `PoseEstimator`: Estimates pose from correspondences

### 3. Map Management

**Map Points**:
- 3D positions in world frame
- ORB descriptors for matching
- Observations from multiple keyframes

**Keyframes**:
- Selected frames for mapping
- Camera pose
- Covisibility graph

**Code location**: `src/map_manager.py`

### 4. Loop Closure

**Detection**:
- Descriptor similarity
- Minimum interval check
- Geometric verification

**Code location**: `src/loop_closure.py`

## Adding New Features

### Example: Add New Feature Detector

1. **Create new detector class**:
   ```python
   class SIFTFeatureExtractor:
       def __init__(self, config):
           self.sift = cv2.SIFT_create()

       def extract(self, image):
           keypoints, descriptors = self.sift.detectAndCompute(image, None)
           return Frame(keypoints=keypoints, descriptors=descriptors)
   ```

2. **Update configuration**:
   ```python
   @dataclass
   class FeatureConfig:
       detector_type: str = "ORB"  # or "SIFT"
       n_features: int = 1000
   ```

3. **Modify FeatureExtractor**:
   ```python
   class FeatureExtractor:
       def __init__(self, config):
           if config.detector_type == "ORB":
               self.detector = cv2.ORB_create()
           elif config.detector_type == "SIFT":
               self.detector = cv2.SIFT_create()
   ```

4. **Add tests**:
   ```python
   def test_sift_extraction():
       config = FeatureConfig(detector_type="SIFT")
       extractor = FeatureExtractor(config)
       frame = extractor.extract(image)
       assert frame.num_features > 0
   ```

### Example: Add Bundle Adjustment

1. **Create optimization module**:
   ```python
   # src/optimizer.py
   class BundleAdjuster:
       def optimize(self, keyframes, map_points):
           # Implement bundle adjustment
           pass
   ```

2. **Integrate with SLAM system**:
   ```python
   # In slam_system.py
   def _optimize_map(self):
       if len(self.map_manager.keyframes) > 10:
           self.bundle_adjuster.optimize(
               self.map_manager.keyframes,
               self.map_manager.map_points
           )
   ```

3. **Add tests**:
   ```python
   def test_bundle_adjustment():
       adjuster = BundleAdjuster()
       # Test optimization
   ```

## Debugging

### Common Issues

1. **No features detected**
   ```python
   # Check image quality
   print(f"Image shape: {image.shape}")
   print(f"Image dtype: {image.dtype}")

   # Lower threshold
   config.features.fast_threshold = 10
   ```

2. **Pose estimation fails**
   ```python
   # Check point count
   print(f"Number of matches: {len(matches)}")

   # Lower RANSAC threshold
   config.features.ransac_threshold = 5.0
   ```

3. **Memory issues**
   ```python
   # Reduce max keyframes
   config.max_keyframes = 100

   # Enable map cleanup
   config.cleanup_orphaned_points = True
   ```

### Debug Visualization

```python
# Visualize features
frame = feature_extractor.extract(image)
feature_extractor.visualize_features(image, frame, show=True)

# Visualize matches
matches, _, _ = feature_extractor.match_frames(frame1, frame2)
feature_extractor.visualize_matches(image1, frame1, image2, frame2, matches)

# Visualize map
slam.visualize(show_cameras=True)
```

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_frame(self, image, timestamp):
    logger.info(f"Processing frame {self.frame_count}")
    # ...
    logger.info(f"Extracted {frame.num_features} features")
```

## Performance Optimization

### Profiling

```python
import cProfile

def profile_slam():
    slam = SLAMSystem(config)
    for frame in video_sequence:
        slam.process_frame(frame)

cProfile.run('profile_slam()')
```

### Bottleneck Identification

1. **Feature extraction**: Usually fast (~50ms)
2. **Feature matching**: Can be slow with many features
3. **Pose estimation**: Fast with RANSAC
4. **Map management**: Depends on map size

### Optimization Strategies

1. **Reduce feature count**:
   ```python
   config.features.n_features = 500  # Default: 1000
   ```

2. **Increase matching threshold**:
   ```python
   config.features.match_ratio_threshold = 0.8  # Default: 0.75
   ```

3. **Limit keyframes**:
   ```python
   config.max_keyframes = 100  # Default: 1000
   ```

4. **Use FLANN matcher**:
   ```python
   # In feature_extractor.py
   FLANN_INDEX_LSH = 6
   index_params = dict(
       algorithm=FLANN_INDEX_LSH,
       table_number=6,
       key_size=12,
       multi_probe_level=1
   )
   search_params = dict(checks=50)
   self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
   ```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions focused

### Example

```python
def extract_features(
    self,
    image: np.ndarray,
    timestamp: float = 0.0
) -> Frame:
    """
    Extract ORB features from image.

    Args:
        image: Input image (BGR or grayscale)
        timestamp: Frame timestamp

    Returns:
        Frame object with extracted features

    Raises:
        ValueError: If image is None
    """
    if image is None:
        raise ValueError("Image cannot be None")

    # Implementation
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    keypoints, descriptors = self.orb.detectAndCompute(gray, None)

    return Frame(
        id=self.frame_counter,
        image=gray,
        keypoints=keypoints,
        descriptors=descriptors,
        timestamp=timestamp
    )
```

## Documentation

### Code Documentation

- Module-level docstrings
- Class docstrings
- Method docstrings
- Inline comments for complex logic

### API Documentation

Generate API docs:
```bash
pip install sphinx
sphinx-quickstart docs/
sphinx-build -b html docs/ docs/_build/html
```

## Version Control

### Git Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "Add new feature"
   ```

3. **Push and create PR**:
   ```bash
   git push origin feature/new-feature
   ```

### Commit Messages

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring

Example:
```
feat(tracking): add feature tracking module

Implement feature tracking using optical flow for better
performance in smooth camera motion scenarios.

Closes #123
```

## Deployment

### Package Creation

1. **Create setup.py**:
   ```python
   from setuptools import setup, find_packages

   setup(
       name='slam-mapping',
       version='0.1.0',
       packages=find_packages(),
       install_requires=[
           'opencv-python',
           'numpy',
           'open3d',
       ],
   )
   ```

2. **Build package**:
   ```bash
   python setup.py sdist bdist_wheel
   ```

3. **Install locally**:
   ```bash
   pip install -e .
   ```

### Docker Deployment

```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "demo"]
```

## Contributing

### Guidelines

1. Fork the repository
2. Create feature branch
3. Write tests
4. Update documentation
5. Submit pull request

### Code Review Checklist

- [ ] Code follows style guide
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Performance acceptable

## Troubleshooting

### Common Problems

1. **Import errors**
   ```bash
   # Ensure src is in path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **OpenCV issues**
   ```bash
   # Reinstall OpenCV
   pip uninstall opencv-python
   pip install opencv-python-headless
   ```

3. **Open3D issues**
   ```bash
   # Install Open3D
   pip install open3d
   ```

4. **Memory errors**
   ```bash
   # Reduce max keyframes
   config.max_keyframes = 50
   ```

## Resources

### Learning Materials

1. **OpenCV Documentation**
   - https://docs.opencv.org/

2. **SLAM Tutorials**
   - Cyrill Stachniss YouTube channel
   - SLAM book by Sebastian Thrun

3. **Papers**
   - ORB-SLAM papers
   - Visual Odometry tutorial

### Tools

1. **IDE**: VS Code, PyCharm
2. **Debugger**: pdb, ipdb
3. **Profiler**: cProfile, line_profiler
4. **Visualization**: Open3D, Matplotlib

## Next Steps

### Advanced Features

1. **Bundle Adjustment**
   - Implement g2o or Ceres integration
   - Joint optimization of poses and points

2. **Dense Mapping**
   - TSDF integration
   - Mesh reconstruction

3. **Multi-Session SLAM**
   - Map saving/loading
   - Map merging

4. **Real-Time Performance**
   - Multi-threading
   - GPU acceleration

### Research Directions

1. **Deep Learning Features**
   - SuperPoint
   - SuperGlue

2. **Semantic SLAM**
   - Object detection integration
   - Semantic mapping

3. **Active SLAM**
   - Exploration strategies
   - Information-theoretic planning

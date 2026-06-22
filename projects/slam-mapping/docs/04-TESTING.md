# 04 - Testing: SLAM System Tests

## Testing Strategy

### Test Pyramid

```
         /\
        /  \  E2E Tests
       /    \
      /------\  Integration Tests
     /        \
    /----------\  Unit Tests
   /            \
  /--------------\
```

### Coverage Goals
- Unit tests: 90%+ coverage
- Integration tests: Core pipeline coverage
- E2E tests: Critical user flows

## Unit Tests

### Feature Extractor Tests

**Test File**: `tests/test_feature_extractor.py`

**Test Cases**:

1. **test_initialization**
   - Verify ORB detector creation
   - Verify matcher creation
   - Check initial counter state

2. **test_extract_features**
   - Extract features from sample image
   - Verify frame properties
   - Check feature count > 0

3. **test_extract_features_color_image**
   - Test with color input
   - Verify grayscale conversion
   - Check feature extraction

4. **test_match_features**
   - Match features from same image
   - Verify matches > 0
   - Check match structure

5. **test_match_frames**
   - Match frames with features
   - Verify point arrays
   - Check array shapes

6. **test_empty_descriptors**
   - Handle empty input gracefully
   - Return empty matches

**Fixtures**:
```python
@pytest.fixture
def feature_extractor():
    return FeatureExtractor()

@pytest.fixture
def sample_image():
    image = np.zeros((480, 640), dtype=np.uint8)
    cv2.rectangle(image, (100, 100), (200, 200), 255, -1)
    cv2.circle(image, (400, 300), 50, 255, -1)
    return image
```

### Pose Estimator Tests

**Test File**: `tests/test_pose_estimator.py`

**Test Cases**:

1. **test_initialization**
   - Verify camera matrix creation
   - Check intrinsic parameters

2. **test_pose_creation**
   - Create pose with R, t
   - Verify properties

3. **test_transformation_matrix**
   - Check 4x4 matrix structure
   - Verify rotation and translation

4. **test_euler_angles**
   - Identity rotation → zero angles
   - Verify angle computation

5. **test_estimate_pose_2d2d**
   - Estimate from point correspondences
   - Verify rotation matrix properties
   - Check determinant = 1

6. **test_triangulate_points**
   - Triangulate from two views
   - Verify 3D point output

7. **test_compute_reprojection_error**
   - Project and reproject points
   - Verify error is small

**Fixtures**:
```python
@pytest.fixture
def camera_config():
    return CameraConfig(fx=525.0, fy=525.0, cx=319.5, cy=239.5)

@pytest.fixture
def pose_estimator(camera_config):
    return PoseEstimator(camera_config)
```

### Map Manager Tests

**Test File**: `tests/test_map_manager.py`

**Test Cases**:

1. **test_initialization**
   - Verify empty state
   - Check counters

2. **test_add_keyframe**
   - Add keyframe
   - Verify storage
   - Check current keyframe

3. **test_add_map_point**
   - Add map point
   - Verify observation tracking

4. **test_get_map_points_in_frame**
   - Add points with observations
   - Query by frame ID
   - Verify correct points returned

5. **test_covisibility_update**
   - Add shared points
   - Update covisibility
   - Verify graph edges

6. **test_statistics**
   - Add data
   - Compute statistics
   - Verify values

7. **test_clear**
   - Add data
   - Clear all
   - Verify empty state

**Fixtures**:
```python
@pytest.fixture
def map_manager():
    return MapManager(max_keyframes=100)

@pytest.fixture
def sample_pose():
    return Pose(rotation=np.eye(3), translation=np.zeros(3))
```

### SLAM System Tests

**Test File**: `tests/test_slam_system.py`

**Test Cases**:

1. **test_initialization**
   - Verify initial state
   - Check flags

2. **test_initialize_with_frame**
   - Initialize with image
   - Verify initialization success

3. **test_process_frame**
   - Process sequence of frames
   - Verify frame count

4. **test_get_trajectory**
   - Process frames
   - Get trajectory
   - Verify shape

5. **test_get_map_points**
   - Process frames
   - Get map points
   - Verify structure

6. **test_statistics**
   - Process frames
   - Get statistics
   - Verify keys

7. **test_reset**
   - Process frames
   - Reset system
   - Verify clean state

8. **test_process_video**
   - Create test video
   - Process video
   - Verify results

**Fixtures**:
```python
@pytest.fixture
def slam_config():
    return SLAMConfig(
        camera=CameraConfig(fx=525.0, fy=525.0, cx=319.5, cy=239.5),
        features=FeatureConfig(n_features=500, min_matches=5),
        keyframe_interval=3,
        max_keyframes=10,
        loop_closure_enabled=False
    )

@pytest.fixture
def slam_system(slam_config):
    return SLAMSystem(slam_config)
```

## Integration Tests

### Full Pipeline Test

**Purpose**: Test complete SLAM pipeline with synthetic data.

```python
def test_full_pipeline(self, slam_config):
    slam = SLAMSystem(slam_config)

    # Create synthetic sequence with known motion
    base_image = create_base_image()
    for i in range(20):
        frame = apply_transformation(base_image, i)
        slam.process_frame(frame, timestamp=i/30.0)

    # Verify results
    stats = slam.get_statistics()
    assert stats['frames_processed'] == 20
    assert stats['is_initialized'] == True
```

### Keyframe Creation Test

**Purpose**: Verify keyframe creation criteria.

```python
def test_keyframe_creation(self, slam_config):
    slam = SLAMSystem(slam_config)

    # Process enough frames
    for i in range(15):
        frame = create_frame_with_motion(i)
        slam.process_frame(frame)

    # Verify keyframes created
    stats = slam.get_statistics()
    assert stats['num_keyframes'] > 0
```

### Feature Tracking Test

**Purpose**: Verify feature tracking across frames.

```python
def test_feature_tracking(self):
    extractor = FeatureExtractor()

    # Create similar images
    image1 = create_image_with_features()
    image2 = apply_small_transformation(image1)

    # Extract and match
    frame1 = extractor.extract(image1)
    frame2 = extractor.extract(image2)
    matches, _, _ = extractor.match_frames(frame1, frame2)

    # Verify tracking
    assert len(matches) > 10
```

## End-to-End Tests

### Video Processing Test

**Purpose**: Test video processing workflow.

```python
def test_video_processing(self, slam_system, tmp_path):
    # Create test video
    video_path = create_test_video(tmp_path)

    # Process video
    output_path = tmp_path / "map.ply"
    slam_system.process_video(str(video_path), str(output_path))

    # Verify outputs
    assert output_path.exists()
    assert slam_system.frame_count > 0
```

### Image Sequence Test

**Purpose**: Test image sequence processing.

```python
def test_image_sequence(self, slam_system, tmp_path):
    # Create test images
    image_dir = create_test_images(tmp_path)

    # Process sequence
    slam_system.process_image_sequence(str(image_dir))

    # Verify results
    assert slam_system.frame_count > 0
```

## Test Data Generation

### Synthetic Image Generator

```python
def create_synthetic_images(num_frames=10, base_features=True):
    """Create synthetic images with known features."""
    images = []

    # Base image with geometric shapes
    base = np.zeros((480, 640), dtype=np.uint8)
    if base_features:
        cv2.rectangle(base, (100, 100), (200, 200), 255, -1)
        cv2.circle(base, (400, 300), 50, 255, -1)
        cv2.line(base, (0, 0), (640, 480), 255, 2)

    # Generate sequence with known motion
    for i in range(num_frames):
        M = np.float32([
            [1, 0, i * 5],  # Translation in x
            [0, 1, i * 2]   # Translation in y
        ])
        transformed = cv2.warpAffine(base, M, (640, 480))
        images.append(transformed)

    return images
```

### Known Motion Generator

```python
def create_known_motion_sequence():
    """Create sequence with known camera motion."""
    # Define camera trajectory
    trajectory = []
    for i in range(20):
        # Forward motion with oscillation
        x = i * 0.1
        y = np.sin(i * 0.1) * 0.5
        z = 0
        trajectory.append(np.array([x, y, z]))

    # Generate images for each pose
    images = []
    for pose in trajectory:
        image = render_scene_from_pose(pose)
        images.append(image)

    return images, trajectory
```

## Test Configuration

### pytest Configuration

**File**: `pytest.ini` or `pyproject.toml`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### Coverage Configuration

**File**: `.coveragerc`

```ini
[run]
source = src
omit = tests/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_feature_extractor.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test

```bash
pytest tests/test_feature_extractor.py::TestFeatureExtractor::test_extract_features -v
```

## Test Results Interpretation

### Success Criteria

- All unit tests pass
- Integration tests pass
- Coverage > 90%
- No critical warnings

### Common Failures

1. **Feature extraction fails**
   - Image too simple
   - Threshold too high
   - Image size issues

2. **Pose estimation fails**
   - Insufficient points
   - Degenerate configuration
   - Noise too high

3. **Map management errors**
   - Invalid observations
   - Duplicate points
   - Memory issues

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=src
```

## Performance Benchmarks

### Benchmark Tests

```python
def test_feature_extraction_speed(benchmark):
    extractor = FeatureExtractor()
    image = create_test_image()

    result = benchmark(extractor.extract, image)
    assert result.num_features > 0

def test_matching_speed(benchmark):
    extractor = FeatureExtractor()
    frame1 = extractor.extract(create_test_image())
    frame2 = extractor.extract(create_test_image())

    result = benchmark(
        extractor.match_features,
        frame1.descriptors,
        frame2.descriptors
    )
    assert len(result) > 0
```

### Performance Targets

- Feature extraction: < 50ms per frame
- Feature matching: < 20ms per pair
- Pose estimation: < 10ms per frame
- Total pipeline: < 100ms per frame

## Summary

The testing strategy ensures:
1. **Correctness**: Unit tests verify individual components
2. **Integration**: Integration tests verify component interaction
3. **Performance**: Benchmark tests verify speed requirements
4. **Coverage**: High coverage ensures most code paths tested
5. **Reliability**: Consistent test results across runs

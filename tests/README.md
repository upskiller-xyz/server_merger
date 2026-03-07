# Test Suite Documentation

## Overview

This test suite provides comprehensive unit tests for the Daylight Factor Server Merger application, targeting **90% code coverage**.

## Directory Structure

The test directory structure mirrors the `src` directory:

```
tests/
├── conftest.py                          # Pytest configuration and shared fixtures
├── components/
│   ├── test_geometry_ops.py            # Geometry operations tests
│   ├── aggregation/                    # Room DF aggregator tests
│   └── processing/
│       ├── test_context.py             # Processing context tests
│       ├── test_window_processor.py     # Window processor tests
│       └── steps/
│           └── test_steps.py           # Processing pipeline steps tests
├── core/
│   ├── test_enums.py                   # Constants and enums tests
│   ├── test_exceptions.py              # Exception classes tests
│   └── utils/
│       ├── test_rotation_helper.py      # Rotation utilities tests
│       └── test_scale_converter.py      # Scale converter tests
├── models/
│   ├── test_simulation_data.py         # SimulationData model tests
│   ├── test_overlap_region.py          # OverlapRegion model tests
│   └── test_room_df_matrix.py          # RoomDFMatrix model tests
└── server/
    ├── services/                        # Service tests
    │   └── validation/                 # Validation tests
    │       └── request/
    └── controllers/                     # Controller tests
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Tests with Coverage Report
```bash
python -m pytest tests/ \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=90 \
    -v
```

Or use the provided script:
```bash
./run_tests_with_coverage.sh
```

### Run Specific Test File
```bash
pytest tests/core/test_enums.py -v
```

### Run Tests Matching a Pattern
```bash
pytest tests/ -k "overlap" -v
```

### Run with Markers
```bash
# Run only unit tests
pytest tests/ -m "unit" -v

# Run only integration tests
pytest tests/ -m "integration" -v
```

## Test Coverage Targets

- **Overall**: 90% coverage minimum
- **Core modules**: 95%+ coverage
- **Processing pipeline**: 90%+ coverage
- **Models**: 95%+ coverage
- **Utilities**: 90%+ coverage

## Shared Fixtures

The `conftest.py` file provides common fixtures used across tests:

- `sample_df_values` - 128x128 DF array
- `sample_mask` - 128x128 mask with white square
- `sample_large_df_values` - 384x384 DF array
- `sample_large_mask` - 384x384 mask
- `sample_window` - WindowGeometry instance
- `sample_room_polygon` - RoomPolygon instance
- `sample_simulation_data` - Complete SimulationData
- `temp_test_dir` - Temporary directory for file tests

## Test Organization

Tests are organized using:
- **Classes** - Group related test methods (e.g., `TestRotationHelper`)
- **Methods** - Individual test cases (e.g., `test_rotate_point_90_degrees`)
- **Fixtures** - Reusable test data and setup

## Coverage Report

After running tests with coverage, open the HTML report:
```bash
open htmlcov/index.html
```

## Adding New Tests

When adding new modules to `src`:
1. Create corresponding test file/directory under `tests`
2. Follow the naming pattern: `test_<module_name>.py`
3. Use test classes to organize related tests
4. Add shared fixtures to `conftest.py` if needed
5. Aim for 90%+ coverage of new code

## Key Test Modules

### Core Tests
- **test_exceptions.py**: Custom exception validation
- **test_enums.py**: Constant definitions
- **test_rotation_helper.py**: Image rotation operations
- **test_scale_converter.py**: Coordinate scaling

### Model Tests
- **test_room_df_matrix.py**: DF matrix accumulation logic
- **test_overlap_region.py**: Overlap calculation models
- **test_simulation_data.py**: Simulation data containers

### Component Tests
- **test_window_processor.py**: Image processing operations
- **test_context.py**: Processing context objects
- **test_steps.py**: Pipeline processing steps

## Requirements

Test dependencies:
- pytest >= 8.0
- pytest-cov >= 4.0
- numpy >= 1.20
- opencv-python >= 4.5

Install with:
```bash
pip install pytest pytest-cov
```

## CI/CD Integration

For continuous integration, use:
```bash
pytest tests/ --cov=src --cov-report=xml --cov-fail-under=90
```

This generates an XML report compatible with most CI/CD platforms (Jenkins, GitLab CI, GitHub Actions, etc.).

## Notes

- Tests use parametrization where appropriate for better coverage
- Fixtures are scope-controlled for independence
- Mock objects are used minimally - integration tests preferred
- All file operations use `tmp_path` fixture for isolation

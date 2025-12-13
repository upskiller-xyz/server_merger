# API Reference

## Endpoint

```
POST /merge
```

Aggregates daylight factor simulation results from multiple windows into a single room representation.

## Request

### Headers

```
Content-Type: application/json
```

### Body Schema

```json
{
  "room_polygon": [[x, y], ...],
  "windows": {
    "window_id": {
      "x1": float,
      "y1": float,
      "z1": float,
      "x2": float,
      "y2": float,
      "z2": float,
      "direction_angle": float
    }
  },
  "simulations": {
    "window_id": {
      "df_values": [[float, ...], ...],
      "mask": [[int, ...], ...]
    }
  }
}
```

### Parameters

#### `room_polygon` (required)
- **Type**: Array of [x, y] coordinate pairs
- **Description**: Room floor plan polygon in meters
- **Example**: `[[0, 0], [5, 0], [5, 4], [0, 4]]`
- **Constraints**:
  - Minimum 3 vertices
  - Coordinates in meters
  - Should form a closed polygon

#### `windows` (required)
- **Type**: Object mapping window IDs to window definitions
- **Description**: Window geometry for each window

**Window Definition:**
- `x1, y1, z1` (float, required): First corner coordinates (meters)
- `x2, y2, z2` (float, required): Opposite corner coordinates (meters)
- `direction_angle` (float, required): Window direction in radians (0 = east, π/2 = north)

**Example:**
```json
{
  "window_1": {
    "x1": 0.0, "y1": 0.0, "z1": 1.0,
    "x2": 1.5, "y2": 0.3, "z2": 2.5,
    "direction_angle": 0.0
  }
}
```

#### `simulations` (required)
- **Type**: Object mapping window IDs to simulation data
- **Description**: DF values and masks for each window

**Simulation Data:**
- `df_values` (2D array of floats, required): Daylight factor matrix (0-10+ range)
- `mask` (2D array of ints, required): Binary mask (0 or 1)

**Constraints:**
- `df_values` and `mask` must have identical dimensions
- Both must be square matrices (NxN)
- Common sizes: 64×64, 128×128, 256×256

**Example:**
```json
{
  "window_1": {
    "df_values": [[0.5, 0.6, ...], [0.4, 0.5, ...], ...],
    "mask": [[1, 1, ...], [1, 1, ...], ...]
  }
}
```

## Response

### Success (200 OK)

```json
{
  "result": [[float, ...], ...],
  "mask": [[int, ...], ...]
}
```

#### Response Fields

- `result` (2D array): Aggregated DF matrix for the room
  - Dimensions: Room bounding box / 0.1 m/px
  - Values: Summed DF contributions from all windows
  - Type: float (0-10+ range)

- `mask` (2D array): Room polygon mask
  - Same dimensions as `result`
  - Values: 1 inside room polygon, 0 outside
  - Type: int (0 or 1)

### Error Responses

#### 400 Bad Request

**Missing required field:**
```json
{
  "error": "Missing required field: room_polygon"
}
```

**Dimension mismatch:**
```json
{
  "error": "Window window_1: df_values shape (128, 128) does not match mask shape (64, 64)"
}
```

**Window not found:**
```json
{
  "error": "Window window_2 not found in windows_data"
}
```

#### 500 Internal Server Error

**Processing failure:**
```json
{
  "error": "Aggregation failed: <error message>"
}
```

## Python Client Example

```python
import requests
import numpy as np

# Prepare data
payload = {
    "room_polygon": [[0, 0], [5, 0], [5, 4], [0, 4]],
    "windows": {
        "window_1": {
            "x1": 1.0, "y1": 0.0, "z1": 1.0,
            "x2": 2.5, "y2": 0.3, "z2": 2.5,
            "direction_angle": 0.0
        }
    },
    "simulations": {
        "window_1": {
            "df_values": np.random.rand(128, 128).tolist(),
            "mask": np.ones((128, 128), dtype=int).tolist()
        }
    }
}

# Send request
response = requests.post('http://localhost:8081/merge', json=payload)

# Parse response
if response.status_code == 200:
    data = response.json()
    df_matrix = np.array(data['result'])
    room_mask = np.array(data['mask'])
    print(f"Result shape: {df_matrix.shape}")
    print(f"DF range: [{df_matrix.min():.2f}, {df_matrix.max():.2f}]")
else:
    print(f"Error {response.status_code}: {response.json()}")
```

## Notes

- All coordinates are in meters
- Direction angles are in radians
- DF values are unitless (typically 0-10 range, but can exceed 10)
- The service automatically handles rotation, scaling, and alignment
- Window IDs in `windows` and `simulations` must match exactly

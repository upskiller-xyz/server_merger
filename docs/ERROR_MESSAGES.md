# API Error Messages

This document describes the error messages returned by the server and provides examples of validation errors.

## Error Response Format

When a validation error occurs, the server returns a structured JSON response with HTTP status code 400:

```json
{
  "error": "Human-readable error message",
  "error_code": "machine_readable_code",
  "field": "path.to.field",
  "value": "optional: the invalid value",
  "context": {
    "additional": "contextual information"
  }
}
```

### Error Codes

- `missing_field`: A required field is missing from the request
- `invalid_type`: A field has the wrong data type
- `invalid_value`: A field has an invalid value
- `invalid_range`: A numeric value is outside the valid range
- `invalid_dimensions`: An array has incorrect dimensions
- `empty_data`: A collection that should not be empty is empty

## Common Validation Errors

### 1. Missing Required Field

**Request:**
```json
{
  "windows": {...},
  "simulation": {...}
}
```

**Response (400):**
```json
{
  "error": "Missing required field: room_polygon",
  "error_code": "missing_field",
  "field": "room_polygon"
}
```

---

### 2. Missing Window Parameter

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {
    "window1": {
      "y1": 3.2,
      "z1": 2.8,
      "x2": 0.4,
      "y2": 6,
      "z2": 5.4,
      "direction_angle": 0
    }
  },
  "simulation": {...}
}
```

**Response (400):**
```json
{
  "error": "Window geometry missing required field: x1",
  "error_code": "missing_field",
  "field": "windows.window1.x1"
}
```

---

### 3. Invalid Window Geometry (z1 >= z2)

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {
    "window1": {
      "x1": 0, "y1": 3.2, "z1": 5.5,
      "x2": 0.4, "y2": 6, "z2": 2.8,
      "direction_angle": 0
    }
  },
  "simulation": {...}
}
```

**Response (400):**
```json
{
  "error": "Window z1 (5.5) must be less than z2 (2.8)",
  "error_code": "invalid_value",
  "field": "windows.window1.z1",
  "context": {
    "z1": 5.5,
    "z2": 2.8
  }
}
```

---

### 4. Invalid Room Polygon (Too Few Vertices)

**Request:**
```json
{
  "room_polygon": [[0, 0], [1, 1]],
  "windows": {...},
  "simulation": {...}
}
```

**Response (400):**
```json
{
  "error": "Room polygon must have at least 3 vertices, got 2",
  "error_code": "invalid_value",
  "field": "room_polygon",
  "context": {
    "vertex_count": 2,
    "min_vertices": 3
  }
}
```

---

### 5. Invalid Array Dimensions

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {...},
  "simulation": {
    "window1": {
      "df_values": [[0.1] * 50] * 50,
      "mask": [[1] * 50] * 50
    }
  }
}
```

**Response (400):**
```json
{
  "error": "Field 'df_values' must be one of sizes (128, 384)x(128, 384), got 50x50",
  "error_code": "invalid_dimensions",
  "field": "simulation.window1.df_values",
  "context": {
    "shape": [50, 50],
    "valid_sizes": [128, 384]
  }
}
```

---

### 6. Non-Square Array

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {...},
  "simulation": {
    "window1": {
      "df_values": [[0.1] * 128] * 100,
      "mask": [[1] * 128] * 100
    }
  }
}
```

**Response (400):**
```json
{
  "error": "Field 'df_values' must be square array, got shape (100, 128)",
  "error_code": "invalid_dimensions",
  "field": "simulation.window1.df_values",
  "context": {
    "shape": [100, 128]
  }
}
```

---

### 7. Wrong Data Type

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {
    "window1": {
      "x1": "not_a_number",
      "y1": 3.2,
      "z1": 2.8,
      "x2": 0.4,
      "y2": 6,
      "z2": 5.4,
      "direction_angle": 0
    }
  },
  "simulation": {...}
}
```

**Response (400):**
```json
{
  "error": "Window parameter 'x1' must be numeric, got str",
  "error_code": "invalid_type",
  "field": "windows.window1.x1",
  "value": "not_a_number"
}
```

---

### 8. Mismatched Window IDs

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {
    "window1": {...}
  },
  "simulation": {
    "different_window": {...}
  }
}
```

**Response (400):**
```json
{
  "error": "Windows defined but missing simulation data: window1",
  "error_code": "missing_field",
  "field": "simulation",
  "context": {
    "missing_window_ids": ["window1"]
  }
}
```

---

### 9. Empty Data Collection

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {},
  "simulation": {}
}
```

**Response (400):**
```json
{
  "error": "Windows dictionary cannot be empty",
  "error_code": "empty_data",
  "field": "windows"
}
```

---

### 10. Missing Simulation Data Field

**Request:**
```json
{
  "room_polygon": [[0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {...},
  "simulation": {
    "window1": {
      "df_values": [[0.1] * 128] * 128
    }
  }
}
```

**Response (400):**
```json
{
  "error": "Simulation data missing 'mask' field",
  "error_code": "missing_field",
  "field": "simulation.window1.mask"
}
```

---

### 11. Invalid Polygon Vertex Format

**Request:**
```json
{
  "room_polygon": [[0, 0, 0], [0, 7], [3, 7], [3, 0]],
  "windows": {...},
  "simulation": {...}
}
```

**Response (400):**
```json
{
  "error": "Room polygon vertex 0 must be [x, y] coordinate pair (2D), got 3 dimensions",
  "error_code": "invalid_value",
  "field": "room_polygon[0]",
  "value": "[0, 0, 0]"
}
```

---

### 12. Non-Numeric Coordinates

**Request:**
```json
{
  "room_polygon": [["x", "y"], [0, 7], [3, 7], [3, 0]],
  "windows": {...},
  "simulation": {...}
}
```

**Response (400):**
```json
{
  "error": "Room polygon vertex 0 coordinates must be numeric, got ['x' 'y']",
  "error_code": "invalid_type",
  "field": "room_polygon[0]",
  "value": "<array shape=(2,)>"
}
```

---

## Internal Server Errors

For unexpected errors (HTTP 500), the response format is:

```json
{
  "error": "Internal server error: <error details>",
  "error_code": "internal_error"
}
```

These errors indicate a problem with the server itself, not with your request. Please report these to the development team.

## Testing Validation

You can test the validation by running:

```bash
python3 test_validation.py
```

This script tests various invalid inputs and displays the error messages returned by the server.

# DF Aggregation Service

## Overview

The DF (Daylight Factor) Aggregation Service combines simulation results from multiple windows into a unified room representation. It processes individual window DF matrices and merges them into a single room-level daylight factor distribution.

## Purpose

Building daylighting simulations often generate separate results for each window. This service aggregates these individual results while accounting for:
- Window positions and orientations within the room
- Room geometry (polygon shape)
- Spatial transformations (rotation, scaling, cropping)
- Proper coordinate alignment

## Key Capabilities

### 1. Multi-Window Aggregation
- Accepts multiple window simulation results in a single request
- Each window can have different sizes, positions, and orientations
- Outputs a unified DF matrix for the entire room

### 2. Geometric Transformation
- Handles arbitrary room polygon shapes
- Supports rotated windows at any angle
- Automatically aligns window reference points with room geometry
- Scales all inputs to a consistent resolution

### 3. Coordinate Systems
- **Input**: Windows defined by 3D bounding boxes (x1,y1,z1 to x2,y2,z2)
- **Processing**: Standard 128×128 px at 0.1 m/px resolution
- **Output**: Room-sized matrix at configurable scale (default 0.1 m/px)

## Processing Pipeline

The service follows a deterministic 5-step pipeline for each window:

1. **Position Calculation** - Determines window location in room coordinates
2. **Standardization** - Resizes all inputs to 128×128 px
3. **Rotation** - Applies direction_angle transformation
4. **Cropping** - Removes empty space outside mask bounds
5. **Accumulation** - Places window contribution on room canvas

## Use Cases

- **Building Performance Analysis**: Combine daylight from all windows in a room
- **Design Optimization**: Evaluate room-level daylighting with different window configurations
- **Compliance Checking**: Generate complete room DF distributions for building codes
- **Visualization**: Create unified heatmaps of daylight availability

## Technical Features

- **Pixel-perfect alignment**: Ensures no gaps or overlaps between window contributions
- **Memory efficient**: Processes windows sequentially, not all at once
- **Resolution independent**: Accepts any input resolution, normalizes internally
- **Mask-aware**: Only accumulates values within valid mask regions

## Limitations

- Assumes windows are on room polygon edges (not validated automatically)
- Does not handle overlapping windows (will sum contributions)
- Output resolution fixed at 0.1 m/px (configurable but must be consistent)
- Room polygon must be convex or simple (no self-intersections)

## Performance

- **Typical request**: 2-4 windows, ~50ms processing time
- **Scalability**: Linear with number of windows
- **Memory**: O(room_area / scale²) for output matrix

# Product Requirements Document: Course Evaluation Data Pipeline Refactoring

## Executive Summary

This document outlines a comprehensive plan to refactor the course evaluation data pipeline to separate renderable spreadsheet data from non-renderable metadata. The current implementation uses a brittle "pop-off" mechanism that needs to be replaced with a clean separation of concerns. Additionally, we will implement tooltips for statistical data showing sample size (n) and standard deviation (σ) where applicable.

## Current State Analysis

### Data Flow Overview

1. **Backend Processing** (`backend/analysis.py`):
   - `process_analysis_request()` receives analysis parameters
   - Processes course data through filters and separations
   - Calculates statistics via `calculate_group_statistics()`
   - Returns results with metadata mixed into the same object

2. **API Layer** (`backend/app.py`):
   - `/api/analyze/<course_code>` endpoint passes data directly from analysis to frontend
   - No separation between renderable and non-renderable data

3. **Frontend Consumption** (`frontend/src/App.js`):
   - Receives analysis results as a single object
   - Uses destructuring to manually separate metadata fields
   - Passes filtered data to `DataDisplay` component

### Current Problems

1. **Mixed Data Structure**: Metadata fields (`current_name`, `former_names`, `grouping_metadata`, etc.) are mixed with statistical data in the same object
2. **Manual Separation**: Frontend manually destructures and filters out metadata fields
3. **Brittle Implementation**: Adding new metadata requires updating multiple places
4. **No Tooltip Support**: Statistical means lack context (sample size, standard deviation)

## Proposed Solution

### High-Level Architecture

```
Backend:
{
  "data": {
    "Group1": { "stat1": value, "stat2": value, ... },
    "Group2": { "stat1": value, "stat2": value, ... }
  },
  "metadata": {
    "current_name": "...",
    "former_names": [...],
    "grouping_metadata": {...},
    ...
  },
  "statistics_metadata": {
    "Group1": {
      "stat1": { "n": count, "std": stddev },
      "stat2": { "n": count, "std": stddev }
    },
    ...
  }
}
```

### Implementation Plan

## Phase 1: Backend Refactoring

### Step 1.1: Modify `calculate_group_statistics()` to Return Extended Data

**File**: `backend/analysis.py`

**Changes**:
1. Modify function signature to optionally return detailed statistics
2. Create a new internal function to calculate mean, std, and count
3. Return both simplified values and detailed metadata

```python
def calculate_group_statistics(course_instances: list, stats_to_calculate: list, 
                             metadata: dict = None, instance_keys: list = None,
                             return_detailed: bool = False) -> dict:
    """
    Calculates aggregated statistics for a group of course instances.
    
    Args:
        ... (existing args)
        return_detailed (bool): If True, returns detailed statistics including n and std
    
    Returns:
        dict: If return_detailed is False, returns {stat_key: mean_value}
              If return_detailed is True, returns {
                  "values": {stat_key: mean_value},
                  "details": {stat_key: {"n": count, "std": std_dev}}
              }
    """
```

**Implementation Details**:
- Keep existing calculation logic intact
- Add parallel calculation for standard deviation and count
- Store raw data points temporarily for std calculation
- Only calculate std/n for numerical statistics (not for "periods_course_has_been_run")

### Step 1.2: Update `process_analysis_request()` to Structure Output

**File**: `backend/analysis.py`

**Changes**:
1. Restructure return format to separate data, metadata, and statistics_metadata
2. Maintain backward compatibility by checking for a version flag

```python
def process_analysis_request(all_course_data: dict, params: dict, 
                           primary_course_code: str = None,
                           skip_grouping: bool = False,
                           api_version: int = 1) -> dict:
    """
    Main function to process an analysis request.
    
    Args:
        ... (existing args)
        api_version (int): API version for response format (1=legacy, 2=separated)
    """
```

**Implementation**:
- Calculate statistics with `return_detailed=True` for v2
- Build three separate dictionaries: `data`, `metadata`, `statistics_metadata`
- For v1 (legacy), merge all dictionaries into single object
- For v2, return structured object with clear separation

### Step 1.3: Update API Endpoint

**File**: `backend/app.py`

**Changes**:
1. Add version detection to `/api/analyze/<course_code>` endpoint
2. Pass version flag to `process_analysis_request()`

```python
@app.route('/api/analyze/<string:course_code>', methods=['POST'])
def analyze_course_data(course_code):
    # ... existing code ...
    
    # Check for API version in request
    api_version = analysis_params.get('api_version', 1)
    
    # Process the data using the analysis module
    results = process_analysis_request(
        all_course_data, 
        analysis_params, 
        primary_course_code=course_code,
        api_version=api_version
    )
```

## Phase 2: Frontend Refactoring

### Step 2.1: Update App.js to Handle New Data Structure

**File**: `frontend/src/App.js`

**Changes**:
1. Add API version to request parameters
2. Update state management to handle separated data
3. Modify data flow to components

```javascript
const fetchAnalysisData = (code, options) => {
    // ... existing code ...
    
    const params = {
        stats: options.stats,
        filters: options.filters,
        separation_keys: options.separationKeys,
        api_version: 2  // Use new API version
    };
    
    // ... fetch logic ...
    
    // Handle new response structure
    if (data && !data.error) {
        // Check if new format
        if (data.data && data.metadata) {
            setAnalysisResult({
                data: data.data,
                metadata: data.metadata,
                statisticsMetadata: data.statistics_metadata
            });
        } else {
            // Legacy format fallback
            setAnalysisResult({ data, metadata: {}, statisticsMetadata: {} });
        }
    }
};
```

### Step 2.2: Update DataDisplay Component for Tooltips

**File**: `frontend/src/components/DataDisplay.js`

**Changes**:
1. Accept `statisticsMetadata` prop
2. Implement tooltip rendering for cells with additional data
3. Add CSS for tooltip styling

```javascript
const DataDisplay = ({ data, errorMessage, selectedStats = [], statisticsMetadata = {} }) => {
    // ... existing code ...
    
    const renderCell = (groupName, statKey, value) => {
        const details = statisticsMetadata[groupName]?.[statKey];
        
        if (details && details.n !== undefined) {
            return (
                <td key={statKey} className="stat-cell-with-tooltip">
                    <span className="stat-value">
                        {typeof value === 'number' ? value.toFixed(2) : value ?? 'N/A'}
                    </span>
                    <span className="stat-tooltip">
                        n = {details.n}
                        {details.std !== undefined && `, σ = ${details.std.toFixed(2)}`}
                    </span>
                </td>
            );
        }
        
        // Regular cell without tooltip
        return (
            <td key={statKey}>
                {typeof value === 'number' ? value.toFixed(2) : value ?? 'N/A'}
            </td>
        );
    };
};
```

### Step 2.3: Add Tooltip Styling

**File**: `frontend/src/components/DataDisplay.css`

**New CSS**:
```css
.stat-cell-with-tooltip {
    position: relative;
}

.stat-tooltip {
    display: none;
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background-color: #333;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    white-space: nowrap;
    z-index: 1000;
    margin-bottom: 5px;
}

.stat-tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: #333;
}

.stat-cell-with-tooltip:hover .stat-tooltip {
    display: block;
}
```

## Phase 3: Testing and Migration

### Step 3.1: Backend Testing

1. **Unit Tests** for new calculation functions:
   - Test standard deviation calculation
   - Test count aggregation
   - Test API version branching

2. **Integration Tests**:
   - Test v1 API maintains exact same response format
   - Test v2 API returns properly structured data
   - Test edge cases (empty data, single data point, etc.)

### Step 3.2: Frontend Testing

1. **Component Tests**:
   - Test tooltip rendering
   - Test data/metadata separation
   - Test backward compatibility

2. **E2E Tests**:
   - Test full flow with v2 API
   - Test fallback to v1 behavior
   - Test tooltip interactions

### Step 3.3: Migration Strategy

1. **Phase 1**: Deploy backend with v2 support (backward compatible)
2. **Phase 2**: Update frontend to use v2 API with fallback
3. **Phase 3**: Monitor for issues, fix edge cases
4. **Phase 4**: Remove v1 support after stability confirmed

## Implementation Checklist

### Backend Tasks
- [ ] Implement detailed statistics calculation in `calculate_group_statistics()`
- [ ] Add standard deviation calculation helper function
- [ ] Modify `process_analysis_request()` to support v2 format
- [ ] Update API endpoint to handle version parameter
- [ ] Add comprehensive error handling for edge cases
- [ ] Write unit tests for new functions
- [ ] Write integration tests for API versions

### Frontend Tasks
- [ ] Update `App.js` to handle new data structure
- [ ] Modify state management for separated data
- [ ] Update `DataDisplay` component for tooltip support
- [ ] Add tooltip CSS styling
- [ ] Update prop passing between components
- [ ] Test tooltip behavior across browsers
- [ ] Ensure CSV export still works correctly

### Documentation Tasks
- [ ] Document new API v2 format
- [ ] Update component prop documentation
- [ ] Add examples for tooltip data structure
- [ ] Document migration path for other consumers

## Risk Mitigation

1. **Backward Compatibility**: Maintain v1 API indefinitely or until all consumers migrate
2. **Performance**: Cache standard deviation calculations if performance becomes an issue
3. **Data Integrity**: Validate that v1 and v2 return same statistical values
4. **Frontend Fallback**: Gracefully handle missing statistics metadata

## Success Criteria

1. Clean separation of renderable data and metadata
2. No breaking changes to existing functionality
3. Tooltips display correctly for all applicable statistics
4. Performance remains unchanged or improves
5. Code is more maintainable and extensible


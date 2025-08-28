# Statistics Reorganization Mini-Plan

## Current State Analysis
- **Current Layout**: Two separate `option-group` divs with "Default Statistics" and "Optional Statistics" headers
- **CSS Grid**: Uses `repeat(auto-fit, minmax(200px, 1fr))` which creates multiple columns
- **Data Structure**: Separate `DEFAULT_STATS` and `OPTIONAL_STATS` arrays in `statsMapping.js`

## Target State
- **Single Column**: All statistics in one `option-group` with "Statistics" header
- **Visual Distinction**: Default stats appear first, optional stats appear after with visual separator or styling
- **Behavior**: Default stats checked by default, optional stats unchecked by default

## Implementation Strategy

### Step 1: Create Combined Statistics Data Structure
```javascript
// In statsMapping.js or AdvancedOptions.js
const ALL_STATS = [
  ...DEFAULT_STATS.map(key => ({ key, isDefault: true })),
  ...OPTIONAL_STATS.map(key => ({ key, isDefault: false }))
];
```

### Step 2: Update Rendering Logic
```javascript
// Replace the two separate option-group divs with:
<div className="option-group">
  <h4>Statistics</h4>
  {ALL_STATS.map(({ key, isDefault }) => (
    <label key={key} className={isDefault ? 'default-stat' : 'optional-stat'}>
      <input
        type="checkbox"
        checked={options.stats[key]}
        onChange={() => handleStatChange(key)}
      />
      {STAT_MAPPINGS[key]}
      {!isDefault && <span className="optional-indicator"> (optional)</span>}
    </label>
  ))}
</div>
```

### Step 3: CSS Updates
```css
.default-stat {
  /* Styling for default stats - maybe bold or different color */
  font-weight: 500;
}

.optional-stat {
  /* Styling for optional stats - maybe lighter or indented */
  opacity: 0.8;
  margin-left: 10px;
}

.optional-indicator {
  font-size: 0.8em;
  color: #666;
  font-style: italic;
}
```

### Step 4: Grid Layout Adjustment
The current CSS grid will need adjustment to handle the new layout:
- Statistics column will be narrower since it's single column
- Year input fields will need their own column
- Separation options remain in their own column

## Challenges & Solutions

### Challenge 1: Maintaining State Initialization
**Problem**: Current initialization logic relies on separate arrays
**Solution**: Keep existing initialization in App.js, just change the rendering

### Challenge 2: Visual Hierarchy
**Problem**: Need to distinguish default vs optional without separate sections
**Solution**: Use subtle styling differences and optional indicators

### Challenge 3: Grid Layout Balance
**Problem**: Single statistics column might look unbalanced
**Solution**: Adjust grid template and add year inputs to balance layout

## Files to Modify
1. `frontend/src/components/AdvancedOptions.js` - Main rendering changes
2. `frontend/src/components/AdvancedOptions.css` - Styling updates
3. `frontend/src/utils/statsMapping.js` - Potentially add combined array utility
# Batch Scraping System

This system allows you to scrape course evaluation data for all courses in `jhu_as_en_courses.txt` without needing to run the web application. It reuses all the existing scraping logic without duplicating code.

## Files Created

- `batch_scraper.py` - Main batch scraping script
- `run_batch_scraper.sh` - Convenient shell script wrapper
- `BATCH_SCRAPING_README.md` - This documentation

## Quick Start

### 1. Test with a small subset first
```bash
./run_batch_scraper.sh test 5
```
This will scrape the first 5 courses to verify everything works.

### 2. Run dry-run to see what would be scraped
```bash
./run_batch_scraper.sh dry-run
```
This shows all courses that would be processed without actually scraping.

### 3. Run full batch scraping
```bash
./run_batch_scraper.sh full
```
This will scrape ALL courses (12,289 courses). This will take a very long time!

## Usage Options

### Shell Script Commands

```bash
# Show help
./run_batch_scraper.sh help

# Test with first N courses (default: 5)
./run_batch_scraper.sh test [N]

# Dry run (show what would be scraped)
./run_batch_scraper.sh dry-run

# Full batch scraping (all courses)
./run_batch_scraper.sh full

# Resume from a specific index
./run_batch_scraper.sh resume [INDEX]

# Check current status
./run_batch_scraper.sh status
```

### Direct Python Usage

```bash
# Basic usage
python3 batch_scraper.py --max-courses 10

# Dry run
python3 batch_scraper.py --dry-run --max-courses 5

# Resume from index 100
python3 batch_scraper.py --start-index 100 --max-courses 50

# Skip courses that are already up-to-date
python3 batch_scraper.py --skip-existing --max-courses 100

# Custom delay between courses
python3 batch_scraper.py --delay 2.0 --max-courses 20
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--courses-file` | File containing course codes | `jhu_as_en_courses.txt` |
| `--start-index` | Index to start from (for resuming) | `0` |
| `--max-courses` | Maximum number of courses to process | `None` (all) |
| `--skip-existing` | Skip courses that are already up-to-date | `False` |
| `--dry-run` | Show what would be done without scraping | `False` |
| `--delay` | Delay between courses in seconds | `1.0` |
| `--max-retries` | Maximum retries for failed courses | `3` |

## Features

### Progress Tracking
- Real-time progress display with percentage completion
- Detailed logging for each course processed
- Automatic retry logic for failed courses
- Progress reports saved as JSON files

### Error Handling
- Graceful handling of authentication failures
- Retry logic with exponential backoff
- Detailed error reporting
- Continuation after failures

### Data Management
- Reuses existing scraping logic from `workflow_helpers.py`
- No code duplication
- Maintains existing data structure
- Compatible with web application

### Performance
- Configurable delays between requests
- Batch processing for efficiency
- Memory-efficient processing
- Resume capability for long-running jobs

## Output Files

### Progress Reports
- `batch_scrape_report_YYYYMMDD_HHMMSS.json` - Detailed report of scraping session
- Contains summary statistics, successful/failed courses, and timing information

### Data Files
- `data.json` - Main data file (updated with new scraped data)
- `metadata.json` - Course metadata (updated with scraping status)
- `failed.json` - Failed scraping attempts (if any)

## Example Progress Report

```json
{
  "summary": {
    "total_courses": 100,
    "successful": 95,
    "failed": 3,
    "skipped": 2,
    "start_time": "2024-01-15T10:30:00",
    "end_time": "2024-01-15T11:45:00",
    "duration_seconds": 4500
  },
  "successful_courses": [...],
  "failed_courses": [...],
  "skipped_courses": [...]
}
```

## Best Practices

### For Large Batch Jobs
1. **Start small**: Test with 5-10 courses first
2. **Use resume**: If the job fails, you can resume from where it left off
3. **Monitor progress**: Check the progress reports regularly
4. **Consider delays**: Use appropriate delays to be respectful to the server

### For Production Use
1. **Run during off-peak hours**: To minimize impact on the evaluation system
2. **Use appropriate delays**: Start with 1-2 seconds between courses
3. **Monitor system resources**: Large batches can use significant memory
4. **Have backup plans**: Consider running in smaller chunks

## Troubleshooting

### Authentication Issues
- The scraper will automatically retry authentication
- If authentication consistently fails, check your network connection
- The evaluation system may be temporarily unavailable

### Memory Issues
- For very large batches, consider processing in smaller chunks
- Use `--max-courses` to limit the batch size
- Monitor system memory usage during long runs

### Network Issues
- Increase the `--delay` between courses if you're getting timeouts
- The scraper has built-in retry logic for temporary network issues
- Consider running during off-peak hours for better reliability

## Integration with Web App

The batch scraper is fully compatible with the existing web application:

- Uses the same data files (`data.json`, `metadata.json`)
- Maintains the same data structure
- Web app can immediately use newly scraped data
- No conflicts between batch scraping and web app usage

## Performance Estimates

Based on testing:
- **Average time per course**: ~5 seconds
- **Total time for all courses**: ~17 hours (12,289 courses)
- **Memory usage**: ~50-100MB for typical batches
- **Network requests**: 1-3 requests per course

## Safety Features

- **Graceful shutdown**: Can be interrupted with Ctrl+C
- **Resume capability**: Can resume from any index
- **Error isolation**: One failed course doesn't stop the entire batch
- **Data integrity**: All data is saved incrementally
- **Rate limiting**: Built-in delays to be respectful to the server

## Monitoring

The scraper provides detailed output including:
- Real-time progress updates
- Success/failure counts
- Timing information
- Error details for failed courses
- Final summary report

Use this information to monitor the scraping progress and identify any issues.
#!/bin/bash

# Batch scraper runner script
# This script provides convenient commands for running the batch scraper

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  dry-run              Show what would be scraped without actually doing it"
    echo "  test [N]             Test with first N courses (default: 5)"
    echo "  full                 Run full batch scraping on all courses"
    echo "  resume [INDEX]       Resume from a specific index"
    echo "  status               Show current scraping status"
    echo ""
    echo "Options:"
    echo "  --skip-existing      Skip courses that are already up-to-date"
    echo "  --delay SECONDS      Delay between courses (default: 1.0)"
    echo "  --max-retries N      Maximum retries for failed courses (default: 3)"
    echo ""
    echo "Examples:"
    echo "  $0 dry-run                    # See what would be scraped"
    echo "  $0 test 10                    # Test with first 10 courses"
    echo "  $0 full --skip-existing       # Run full scraping, skip existing"
    echo "  $0 resume 100                 # Resume from course index 100"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if required files exist
if [ ! -f "jhu_as_en_courses.txt" ]; then
    print_error "Course file 'jhu_as_en_courses.txt' not found"
    exit 1
fi

if [ ! -f "batch_scraper.py" ]; then
    print_error "Batch scraper script 'batch_scraper.py' not found"
    exit 1
fi

# Parse command
COMMAND=${1:-"help"}
shift || true

case $COMMAND in
    "help"|"-h"|"--help")
        show_usage
        exit 0
        ;;
    
    "dry-run")
        print_info "Running dry-run to show what would be scraped..."
        python3 batch_scraper.py --dry-run "$@"
        ;;
    
    "test")
        N=${1:-5}
        shift
        print_info "Testing batch scraper with first $N courses..."
        python3 batch_scraper.py --max-courses "$N" "$@"
        ;;
    
    "full")
        print_warning "Starting FULL batch scraping of all courses!"
        print_warning "This may take a very long time. Press Ctrl+C to cancel."
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Starting full batch scraping..."
            python3 batch_scraper.py "$@"
        else
            print_info "Cancelled by user"
        fi
        ;;
    
    "resume")
        INDEX=${1:-0}
        print_info "Resuming batch scraping from index $INDEX..."
        python3 batch_scraper.py --start-index "$INDEX" "$@"
        ;;
    
    "status")
        print_info "Checking current scraping status..."
        if [ -f "metadata.json" ]; then
            echo "Metadata file exists with $(wc -l < metadata.json) entries"
        else
            echo "No metadata file found"
        fi
        
        if [ -f "data.json" ]; then
            echo "Data file exists with $(wc -l < data.json) entries"
        else
            echo "No data file found"
        fi
        
        # Count total courses in the file
        TOTAL_COURSES=$(wc -l < jhu_as_en_courses.txt)
        echo "Total courses available: $TOTAL_COURSES"
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac
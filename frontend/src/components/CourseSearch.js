import React, { useState } from 'react';
import './CourseSearch.css';
import { API_BASE_URL } from '../config';

const CourseSearch = ({ onDataReceived, onLoadingChange }) => {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [lastSearchedQuery, setLastSearchedQuery] = useState('');

    const handleSearch = async () => {
        if (!query.trim()) return;
        const trimmedQuery = query.trim().substring(0, 1000); // Ensure max 1000 chars to prevent abuse
        setLastSearchedQuery(trimmedQuery);
        setIsLoading(true);
        setError(null);

        // Case-insensitive check if it's a course code (e.g., AS.123.456 or as.123.456)
        const courseCodePattern = /^[A-Za-z]{2}\.\d{3}\.\d{3}$/;
        const isCourseCode = courseCodePattern.test(trimmedQuery);

        try {
            let courseCode;
            if (isCourseCode) {
                // Auto-uppercase the course code to match the stored format
                courseCode = trimmedQuery.toUpperCase();
            } else {
                // It's a course name search
                if (onLoadingChange) onLoadingChange(true);
                const searchResponse = await fetch(`${API_BASE_URL}/api/search/course_name/${trimmedQuery}`);
                if (!searchResponse.ok) throw new Error('Error searching for course name.');
                
                const courseCodes = await searchResponse.json();
                if (courseCodes.length === 0) throw new Error('No matching courses already downloaded, try using a course code.');

                // For now, just take the first result. UI for multiple matches will be added later.
                courseCode = courseCodes[0];
            }
            onDataReceived(courseCode);
        } catch (err) {
            setError(err.message);
            onDataReceived(null); // Clear previous data on error
        } finally {
            setIsLoading(false);
            if (!isCourseCode && onLoadingChange) onLoadingChange(false);
        }
    };

    return (
        <div className="course-search">
            <input
                type="text"
                value={query}
                maxLength="1000"
                onChange={(e) => {
                    const value = e.target.value;
                    if (value.length <= 1000) {
                        setQuery(value);
                    }
                }}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && query.trim() !== '' && query.trim() !== lastSearchedQuery) {
                        handleSearch();
                    }
                }}
                placeholder="Enter course code or name (e.g., AS.180.101 or Intro to Psych)"
            />
            <button onClick={handleSearch} disabled={isLoading}>
                {isLoading ? 'Searching...' : 'Search'}
            </button>
            {error && <p className="error-message">{error}</p>}
        </div>
    );
};

export default CourseSearch;
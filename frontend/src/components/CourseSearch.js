import React, { useState } from 'react';
import './CourseSearch.css';

const CourseSearch = ({ onDataReceived, onLoadingChange }) => {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = async () => {
        if (!query.trim()) return;
        setIsLoading(true);
        setError(null);

        // Basic check if it's a course code (e.g., AS.123.456)
        const isCourseCode = /^[A-Z]{2}\.\d{3}\.\d{3}$/.test(query.trim());

        try {
            let courseCode;
            if (isCourseCode) {
                courseCode = query.trim();
            } else {
                // It's a course name search
                if (onLoadingChange) onLoadingChange(true);
                const searchResponse = await fetch(`http://127.0.0.1:5000/api/search/course_name/${query.trim()}`);
                if (!searchResponse.ok) throw new Error('Error searching for course name.');
                
                const courseCodes = await searchResponse.json();
                if (courseCodes.length === 0) throw new Error('No matching courses found.');

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
                onChange={(e) => setQuery(e.target.value)}
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
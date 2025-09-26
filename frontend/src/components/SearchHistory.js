import React, { useState, useEffect, useMemo } from 'react';
import './SearchHistory.css';
import { getSearchHistory, clearSearchHistory, removeFromSearchHistory } from '../utils/storage';


const getFilteredHistory = (history, searchValue, currentCourseCode) => {
    let filtered = history.filter(item => item.code !== currentCourseCode);

    if (searchValue && searchValue.trim()) {
        const lowerSearch = searchValue.toLowerCase();
        filtered = filtered.filter(item => {
            const displayText = `${item.code} ${item.name}`.toLowerCase();
            return displayText.includes(lowerSearch);
        });
    }

    return filtered;
};

const SearchHistory = ({
    isOpen,
    onClose,
    onItemClick,
    searchValue,
    currentCourseCode,
    anchorRef
}) => {
    const [history, setHistory] = useState(getSearchHistory());
    const [displayCount, setDisplayCount] = useState(3);
    const [selectedIndex, setSelectedIndex] = useState(-1);

    // Effect to handle clicks outside the component to close it
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (isOpen && anchorRef.current && !anchorRef.current.contains(event.target)) {
                // A bit of a hack to check if the click was inside the dropdown itself
                const dropdown = document.querySelector('.search-history-dropdown');
                if (dropdown && !dropdown.contains(event.target)) {
                    onClose();
                }
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen, onClose, anchorRef]);

    const filteredHistory = useMemo(
        () => getFilteredHistory(history, searchValue, currentCourseCode),
        [history, searchValue, currentCourseCode]
    );

    // Keyboard navigation effect
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (!isOpen) return;

            const visibleItems = filteredHistory.slice(0, displayCount);
            let handled = false;

            switch (e.key) {
                case 'ArrowDown':
                    setSelectedIndex(prev => Math.min(prev + 1, visibleItems.length - 1));
                    handled = true;
                    break;
                case 'ArrowUp':
                    setSelectedIndex(prev => (prev > -1 ? prev - 1 : -1));
                    handled = true;
                    break;
                case 'Enter':
                    if (selectedIndex >= 0 && selectedIndex < visibleItems.length) {
                        onItemClick(visibleItems[selectedIndex].code);
                        handled = true;
                    }
                    break;
                case 'Escape':
                    onClose();
                    handled = true;
                    break;
                default:
                    if (!e.ctrlKey && !e.altKey && !e.metaKey && e.key.length === 1) {
                        setSelectedIndex(-1);
                    }
                    break;
            }

            if (handled) {
                e.preventDefault();
                e.stopPropagation();
            }
        };

        document.addEventListener('keydown', handleKeyDown, true); // Use capture phase
        return () => document.removeEventListener('keydown', handleKeyDown, true);
    }, [isOpen, selectedIndex, filteredHistory, displayCount, onItemClick, onClose]);


    if (!isOpen || filteredHistory.length === 0) {
        return null;
    }

    const handleRemoveItem = (e, courseCode) => {
        e.stopPropagation(); // Prevent the item click from firing
        const newHistory = removeFromSearchHistory(courseCode);
        setHistory(newHistory);
    };

    const handleClearAll = () => {
        if (window.confirm('Are you sure you want to clear all search history?')) {
            clearSearchHistory();
            setHistory([]);
            onClose();
        }
    };

    const visibleItems = filteredHistory.slice(0, displayCount);

    return (
        <div className="search-history-dropdown">
            <button className="search-history-close" onClick={onClose}>&times;</button>
            {visibleItems.map((item, index) => (
                <div
                    key={item.code}
                    className={`search-history-item ${index === selectedIndex ? 'selected' : ''}`}
                    onClick={() => onItemClick(item.code)}
                    onMouseEnter={() => setSelectedIndex(index)}
                >
                    <div className="search-history-item-text">
                        <span className="search-history-item-code">{item.code}</span>
                        <span className="search-history-item-name">{item.name}</span>
                    </div>
                    <button
                        className="search-history-item-remove"
                        onClick={(e) => handleRemoveItem(e, item.code)}
                    >
                        &times;
                    </button>
                </div>
            ))}
            <div className="search-history-footer">
                {filteredHistory.length > displayCount ? (
                    <span
                        className="search-history-show-more"
                        onClick={() => setDisplayCount(prev => prev + 5)}
                    >
                        Show more
                    </span>
                ) : <span>&nbsp;</span>}
                {displayCount > 3 && (
                     <span
                        className="search-history-clear-all"
                        onClick={handleClearAll}
                    >
                        Clear all history
                    </span>
                )}
            </div>
        </div>
    );
};

export default SearchHistory;
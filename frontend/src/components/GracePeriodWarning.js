import React, { useState } from 'react';
import './GracePeriodWarning.css';

const GracePeriodWarning = ({ courseCode, gracePeriodInfo, onRecheck }) => {
    const [isRechecking, setIsRechecking] = useState(false);

    if (!gracePeriodInfo || !gracePeriodInfo.needs_warning) {
        return null;
    }

    const handleRecheck = async () => {
        setIsRechecking(true);
        try {
            await onRecheck();
        } finally {
            setIsRechecking(false);
        }
    };

    return (
        <div className="grace-period-warning">
            <div className="warning-content">
                <span className="warning-text">
                    {gracePeriodInfo.current_period} period might have data but hasn't been checked since {gracePeriodInfo.last_scrape_date}, would you like to recheck?
                </span>
                <button 
                    className="recheck-button" 
                    onClick={handleRecheck}
                    disabled={isRechecking}
                >
                    {isRechecking ? 'Rechecking...' : 'Recheck'}
                </button>
            </div>
        </div>
    );
};

export default GracePeriodWarning;

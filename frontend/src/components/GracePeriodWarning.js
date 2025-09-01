import React, { useState } from 'react';
import './GracePeriodWarning.css';

const GracePeriodWarning = ({ courseCode, gracePeriodInfo, isDismissed, onRecheck }) => {
    const [isRechecking, setIsRechecking] = useState(false);

    if (!gracePeriodInfo || !gracePeriodInfo.needs_warning || isDismissed) {
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
                    {Array.isArray(gracePeriodInfo.future_course_periods) && gracePeriodInfo.future_course_periods.length > 0
                        ? (
                            <>
                                No evaluation data found for the most recent period. <br/>
                                However, the course is listed on SIS for {gracePeriodInfo.future_course_periods.join(', ')}.<br/>
                                That evaluation data is not available yet. Would you like to recheck?
                            </>
                        )
                        : (
                            <>
                                {gracePeriodInfo.current_period} period might have data but hasn't been checked since {gracePeriodInfo.last_scrape_date}, would you like to recheck?
                            </>
                        )
                    }
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

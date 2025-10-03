# GracePeriodWarning Component

## Overview

The `GracePeriodWarning` component is a UI element responsible for notifying the user when a course's evaluation data might be outdated. It specifically handles the "grace period" scenario, where new evaluations for a recent academic period may be available but have not yet been scraped.

## Core Functionality

- **Conditional Rendering**: The component only renders if it receives valid `gracePeriodInfo` indicating a warning is necessary (`needs_warning: true`) and if the warning has not been dismissed by the user (`isDismissed: false`).
- **Information Display**: It displays a user-friendly message indicating which academic period might have new data and the date of the last scrape attempt.
- **User-Initiated Action**: It provides a "Recheck" button that allows the user to trigger a new scrape for the course.

## Interaction Patterns

- The component is controlled by its parent. The parent determines its visibility through the `gracePeriodInfo` and `isDismissed` props.
- When the user clicks the "Recheck" button, the component invokes the `onRecheck` callback function passed down from the parent.
- While the `onRecheck` operation is in progress, the component enters a disabled state (`isRechecking`), preventing multiple clicks and providing visual feedback to the user (e.g., changing the button text to "Rechecking...").

## Props

- **`courseCode` (String)**: The course code (e.g., "AS.180.101") for which the warning is relevant.
- **`gracePeriodInfo` (Object)**: An object containing details about the grace period status from the backend. Expected keys include `needs_warning` (boolean), `current_period` (string), and `last_scrape_date` (string).
- **`isDismissed` (Boolean)**: A flag managed by the parent component to control whether the warning should be hidden even if `needs_warning` is true.
- **`onRecheck` (Function)**: A callback function that the parent component provides. This function is executed when the user clicks the "Recheck" button and is responsible for initiating the data re-scraping process.
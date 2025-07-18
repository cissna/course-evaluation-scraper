# Goal of this repo:
Create a scraper than can dynamically get all JHU course evaluation data for a given course in such a way that it can:
- scrape only partial data to start, and scrape new data on demand
- Run when new data comes out and not have to rescrape everything each time

## Data storage mechanism:
When a course is queried, if there is data and no discrepancy between the last period gathered and the current date, we just return the cached data. Otherwise we use requests to get the most up-to-date data, then return that along with any previous data.

`metadata.json` will have the following metadata for a given course code:
- first_period_gathered (null if no data)
- last_period_gathered (always is the last period we checked for data, even if there is no data)
- last_period_failed (defaults to true, only turned false once all data up to the present date is succesfully collected to avoid missed data. If it actually remains false, we will not parse any more periods so last_period_gathered may not be the present)
- relevant_periods (exact course codes with corresponding data in data.json)

`data.json` will have the actual data for each specific course code (XX.###.###.##.XX##)
Here is an example entry:
```
{
    "AS.200.312.01.FA21": {
        "course_name": "Substance Use and Mental Health",
        "instructor_name": "Chelsea Howe",
        "overall_quality_frequency": {
            "Poor": 0,
            "Weak": 0,
            "Satisfactory": 3,
            "Good": 6,
            "Excellent": 20
        },
        "instructor_effectiveness_frequency": {
            "Poor": 0,
            "Weak": 0,
            "Satisfactory": 0,
            "Good": 6,
            "Excellent": 22
        },
        "intellectual_challenge_frequency": {
            "Poor": 0,
            "Weak": 0,
            "Satisfactory": 1,
            "Good": 6,
            "Excellent": 21
        },
        "ta_frequency": {
            "Poor": 0,
            "Weak": 0,
            "Satisfactory": 0,
            "Good": 0,
            "Excellent": 0
        },
        "ta_names": [
            "NA",
            "N/A"
        ],
        "feedback_frequency": {
            "Disagree strongly": 0,
            "Disagree somewhat": 3,
            "Neither agree nor disagree": 2,
            "Agree somewhat": 6,
            "Agree strongly": 15
        },
        "workload_frequency": {
            "Much lighter": 2,
            "Somewhat lighter": 5,
            "Typical": 17,
            "Somewhat heavier": 3,
            "Much heavier": 0
        }
    },
}
```

## To be added:
- Resolving time conflicts
- dealing with 20+ search results


## Notes:
[I previously did this same project](https://github.com/cissna/jhu-course-evaluations-analysis) but gave up at a state very near completion (some minor bugs and some unimportant edge cases to deal with). I got bored because I found out someone else had already done it, however, they ended up not publishing their data. My flame of interest was reignited when I found out JHU made their evaluation search page **much** easier to navigate by actually putting the data on the web instead of making you download a PDF, meaning the project could be done with requests instead of Selenium, also meaning that it could be run as a website without a VM and just with a simple backend.

Since I already made this project, I have a very clear sense of how everything needs to be so I'm going to vibe code it completely using Roo Code (Gemini 2.5 Pro) with a memory bank extension called Context Portal that I'll be trying out for the first time right now.

# Goal of this repo:
Create a scraper than can dynamically get all JHU course evaluation data for a given course in such a way that it can:
- scrape only partial data to start, and scrape new data on demand
- Run when new data comes out and not have to rescrape everything each time

# Notes:
[I previously did this same project](https://github.com/cissna/jhu-course-evaluations-analysis) but gave up at a state very near completion (some minor bugs and some unimportant edge cases to deal with). I got bored because I found out someone else had already done it, however, they ended up not publishing their data. My flame of interest was reignited when I found out JHU made their evaluation search page **much** easier to navigate by actually putting the data on the web instead of making you download a PDF, meaning the project could be done with requests instead of Selenium, also meaning that it could be run as a website without a VM and just with a simple backend.

Since I already made this project, I have a very clear sense of how everything needs to be so I'm going to vibe code it completely using Roo Code (Gemini 2.5 Pro) with a memory bank extension called Context Portal that I'll be trying out for the first time right now.

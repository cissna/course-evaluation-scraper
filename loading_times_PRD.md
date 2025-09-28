Looking at your codebase, I can see the performance issues you're experiencing. The current architecture makes a full backend request for every filter change, which is inefficient. I'll create a comprehensive PRD to solve this with a hybrid approach that caches data intelligently on the frontend.

# Product Requirements Document: Frontend Data Caching & Performance Optimization

## 1. Executive Summary

This PRD outlines a solution to eliminate unnecessary delays when filtering course evaluation data by implementing intelligent frontend caching. The solution will store raw course data and perform filtering/analysis on the frontend while maintaining a 3-search history cache to enable instant switching between recent searches.

## 2. Problem Statement

### Current Issues:
1. Every filter change triggers a full backend request with 0.5-2 second delays
2. Users experience lag when toggling between professors, years, or other filters
3. No caching of previously fetched data, causing redundant API calls
4. Poor user experience when navigating between recent searches

### Root Cause:
The backend performs all data processing, requiring network round-trips for every interaction even when the underlying data hasn't changed.

## 3. Proposed Solution

### High-Level Architecture:
1. **Frontend Data Cache**: Store raw course data in memory after initial fetch
2. **Client-Side Processing**: Move filtering and statistical calculations to the frontend
3. **Search History Cache**: Maintain up to 3 complete course datasets for instant switching
4. **Smart Backend Requests**: Only fetch from backend when truly needed (new course, stale data, or cache miss)

## 4. Technical Design

### 4.1 Data Flow Architecture

```
User Action → Check Frontend Cache → 
  ├─ Cache Hit: Process Locally → Update UI (instant)
  └─ Cache Miss: Fetch from Backend → Store in Cache → Process Locally → Update UI
```

### 4.2 Frontend Cache Structure

```javascript
// In-memory cache structure
const courseDataCache = {
  // Course code -> raw data mapping
  'AS.180.101': {
    data: { /* raw course instances */ },
    metadata: { /* course metadata */ },
    timestamp: Date.now(),
    groupedCourses: ['AS.180.301'] // if applicable
  }
};

// Search history with full data (max 3 entries)
const searchHistoryCache = [
  {
    courseCode: 'AS.180.101',
    data: { /* processed analysis result */ },
    rawData: { /* raw course instances */ },
    metadata: { /* course metadata */ },
    timestamp: Date.now()
  }
  // ... up to 3 entries
];
```

### 4.3 New API Endpoint

Create a new endpoint that returns raw data without processing:

```
GET /api/course-raw/<course_code>
Returns: {
  instances: { /* all course instances */ },
  metadata: { /* course metadata */ },
  groupedCourses: [ /* array of grouped course codes */ ]
}
```

### 4.4 Frontend Processing Module

Port the Python analysis logic to JavaScript:

```javascript
// frontend/src/utils/analysisEngine.js

export function processAnalysisRequest(rawData, params) {
  // 1. Apply filters
  const filtered = filterInstances(rawData.instances, params.filters);
  
  // 2. Separate by keys
  const separated = separateInstances(filtered, params.separationKeys);
  
  // 3. Calculate statistics
  const results = calculateGroupStatistics(separated, params.stats);
  
  return {
    data: results.data,
    metadata: rawData.metadata,
    statistics_metadata: results.statistics_metadata
  };
}
```

## 5. Implementation Plan

### Phase 1: Backend Modifications (2 hours)

#### 5.1.1 Create Raw Data Endpoint

Create `backend/app.py` modification:

```python
@app.route('/api/course-raw/<string:course_code>')
def get_course_raw_data(course_code):
    """
    API endpoint to get raw course data without analysis.
    Returns all instances and metadata for frontend processing.
    """
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format"}), 400
    
    course_code = course_code.upper()
    
    try:
        # Get all course data
        all_course_data = get_course_data_and_update_cache(course_code)
        
        # Get metadata
        metadata = get_course_metadata(course_code)
        
        # Get grouping info
        group_info = grouping_service.get_group_info(course_code)
        grouped_courses = []
        
        if group_info and group_info.get("courses"):
            grouped_courses = group_info["courses"]
            
            # Fetch data for all grouped courses
            for grouped_code in grouped_courses:
                if grouped_code != course_code:
                    grouped_data = get_course_data_and_update_cache(grouped_code)
                    if grouped_data:
                        for key, value in grouped_data.items():
                            all_course_data[f"{grouped_code}_{key}"] = {
                                **value,
                                'course_code': grouped_code
                            }
        
        return jsonify({
            "instances": all_course_data,
            "metadata": extract_course_metadata(
                {k: v.get('course_name', '') for k, v in all_course_data.items()},
                course_code,
                {},
                course_code
            ),
            "groupedCourses": grouped_courses,
            "groupingMetadata": {
                "grouped_courses": grouped_courses,
                "group_description": group_info.get("description", ""),
                "is_grouped": bool(grouped_courses and len(grouped_courses) > 1)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Phase 2: Frontend Analysis Engine (4 hours)

#### 5.2.1 Create Analysis Engine Module

Create `frontend/src/utils/analysisEngine.js`:

```javascript
// Statistical mappings from Python
const STAT_MAPPINGS = {
  overall_quality: {
    name: "Overall Quality",
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  },
  instructor_effectiveness: {
    name: "Instructor Effectiveness", 
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  },
  intellectual_challenge: {
    name: "Intellectual Challenge",
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  },
  workload: {
    name: "Workload",
    mapping: {"Much lighter": 1, "Somewhat lighter": 2, "Typical": 3, "Somewhat heavier": 4, "Much heavier": 5}
  },
  feedback_frequency: {
    name: "Helpful Feedback",
    mapping: {"Disagree strongly": 1, "Disagree somewhat": 2, "Neither agree nor disagree": 3, "Agree somewhat": 4, "Agree strongly": 5}
  },
  ta_frequency: {
    name: "TA Quality",
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  }
};

// Utility functions
function simplifyName(name) {
  if (!name) return "";
  return name.replace(/[^a-zA-Z]/g, '').toLowerCase();
}

function parseInstanceKey(key) {
  const match = key.match(/\.((?:IN|SP|SU|FA))(\d{2})$/);
  if (match) {
    const [, semester, year] = match;
    const yearNum = parseInt('20' + year);
    const semesterOrder = {'IN': 0, 'SP': 1, 'SU': 2, 'FA': 3};
    return { year: yearNum, semesterNum: semesterOrder[semester] || 0, semester };
  }
  return { year: 0, semesterNum: 0, semester: null };
}

// Filter instances based on criteria
export function filterInstances(instances, filters) {
  const filtered = {};
  const minYear = filters.min_year ? parseInt(filters.min_year) : null;
  const maxYear = filters.max_year ? parseInt(filters.max_year) : null;
  
  for (const [key, instance] of Object.entries(instances)) {
    const { year } = parseInstanceKey(key);
    
    if (minYear && year < minYear) continue;
    if (maxYear && year > maxYear) continue;
    if (filters.seasons?.length && !filters.seasons.includes(getInstanceSeason(key))) continue;
    if (filters.instructors?.length && !filters.instructors.includes(instance.instructor_name)) continue;
    
    filtered[key] = instance;
  }
  
  return filtered;
}

// Separate instances into groups
export function separateInstances(instances, separationKeys = []) {
  if (!separationKeys.length) {
    return { "All Data": Object.values(instances) };
  }
  
  const groups = {};
  const instructorNameMap = buildInstructorNameMap(instances);
  
  for (const [key, instance] of Object.entries(instances)) {
    const groupParts = [];
    
    for (const sepKey of separationKeys) {
      let value = "Unknown";
      
      switch (sepKey) {
        case "instructor":
          const simplified = simplifyName(instance.instructor_name);
          value = instructorNameMap[simplified] || instance.instructor_name || "Unknown";
          break;
        case "year":
          value = String(parseInstanceKey(key).year);
          break;
        case "season":
          value = getInstanceSeason(key);
          break;
        case "exact_period":
          const match = key.match(/\.([A-Z]{2}\d{2})$/);
          value = match ? match[1] : "Unknown";
          break;
        case "course_code":
          value = instance.course_code || key.match(/^([A-Z]+\.\d+\.\d+)/)?.[1] || "Unknown";
          break;
        case "course_name":
          value = instance.course_name || "Unknown";
          break;
        default:
          value = String(instance[sepKey] || "Unknown");
      }
      
      groupParts.push(value);
    }
    
    const groupName = groupParts.join(", ");
    if (!groups[groupName]) groups[groupName] = [];
    groups[groupName].push(instance);
  }
  
  return groups;
}

// Calculate statistics for groups
export function calculateGroupStatistics(groups, selectedStats) {
  const results = { data: {}, statistics_metadata: {} };
  
  for (const [groupName, instances] of Object.entries(groups)) {
    const groupStats = {};
    const groupMetadata = {};
    
    // Aggregate frequency data
    const aggregated = {};
    for (const stat of selectedStats) {
      if (stat === 'periods_course_has_been_run') continue;
      aggregated[stat] = {};
    }
    
    for (const instance of instances) {
      for (const stat of selectedStats) {
        if (stat === 'periods_course_has_been_run') continue;
        
        const freqKey = stat.endsWith('_frequency') ? stat : stat + '_frequency';
        if (instance[freqKey]) {
          for (const [response, count] of Object.entries(instance[freqKey])) {
            if (!aggregated[stat][response]) aggregated[stat][response] = 0;
            aggregated[stat][response] += count;
          }
        }
      }
    }
    
    // Calculate statistics
    for (const stat of selectedStats) {
      if (stat === 'periods_course_has_been_run') {
        // Extract periods from instance keys
        const periods = new Set();
        for (const instance of instances) {
          // Find the key for this instance
          for (const [key, inst] of Object.entries(groups)) {
            if (inst === instance) {
              const match = key.match(/\.([A-Z]{2}\d{2})$/);
              if (match) periods.add(match[1]);
            }
          }
        }
        groupStats[stat] = periods.size > 0 ? Array.from(periods).sort().join(', ') : 'N/A';
        groupMetadata[stat] = { n: null, std: null };
      } else {
        const statConfig = STAT_MAPPINGS[stat];
        if (!statConfig) continue;
        
        const detailed = calculateDetailedStatistics(aggregated[stat], statConfig.mapping);
        groupStats[stat] = detailed.mean;
        groupMetadata[stat] = { n: detailed.n, std: detailed.std };
      }
    }
    
    results.data[groupName] = groupStats;
    results.statistics_metadata[groupName] = groupMetadata;
  }
  
  return results;
}

// Calculate detailed statistics
function calculateDetailedStatistics(frequencyDict, valueMapping) {
  const dataPoints = [];
  let totalResponses = 0;
  
  for (const [response, count] of Object.entries(frequencyDict)) {
    if (valueMapping[response] && count > 0) {
      const value = valueMapping[response];
      for (let i = 0; i < count; i++) {
        dataPoints.push(value);
      }
      totalResponses += count;
    }
  }
  
  if (totalResponses === 0) {
    return { mean: null, std: null, n: 0 };
  }
  
  const mean = dataPoints.reduce((a, b) => a + b, 0) / totalResponses;
  
  let std = 0;
  if (totalResponses > 1) {
    const variance = dataPoints.reduce((sum, x) => sum + Math.pow(x - mean, 2), 0) / (totalResponses - 1);
    std = Math.sqrt(variance);
  }
  
  return {
    mean: Math.round(mean * 100) / 100,
    std: Math.round(std * 100) / 100,
    n: totalResponses
  };
}

// Helper functions
function getInstanceSeason(key) {
  const { semester } = parseInstanceKey(key);
  const seasons = {"FA": "Fall", "SP": "Spring", "SU": "Summer", "IN": "Intersession"};
  return seasons[semester] || "Unknown";
}

function buildInstructorNameMap(instances) {
  const nameMap = {};
  const sortedKeys = Object.keys(instances).sort((a, b) => {
    const aInfo = parseInstanceKey(a);
    const bInfo = parseInstanceKey(b);
    if (aInfo.year !== bInfo.year) return aInfo.year - bInfo.year;
    return aInfo.semesterNum - bInfo.semesterNum;
  });
  
  for (const key of sortedKeys) {
    const name = instances[key].instructor_name;
    if (name) {
      const simplified = simplifyName(name);
      nameMap[simplified] = name; // Latest occurrence wins
    }
  }
  
  return nameMap;
}

// Main processing function
export function processAnalysisRequest(rawData, params) {
  const filtered = filterInstances(rawData.instances, params.filters);
  const separated = separateInstances(filtered, params.separation_keys || params.separationKeys);
  const results = calculateGroupStatistics(separated, 
    Object.keys(params.stats).filter(k => params.stats[k])
  );
  
  return {
    data: results.data,
    metadata: {
      ...rawData.metadata,
      grouping_metadata: rawData.groupingMetadata
    },
    statistics_metadata: results.statistics_metadata
  };
}
```


### Phase 3: Cache Management (3 hours)

#### 5.3.1 Create Cache Manager

Create `frontend/src/utils/cacheManager.js`:

```javascript
// Cache configuration
const CACHE_SIZE_LIMIT = 10; // Max courses in general cache
const SEARCH_HISTORY_CACHE_LIMIT = 3; // Max full datasets in history
const CACHE_DURATION_MS = 30 * 60 * 1000; // 30 minutes

class CacheManager {
  constructor() {
    this.courseDataCache = new Map();
    this.searchHistoryCache = [];
  this }Store if data
DataStale() return Date - cache_  // raw course data from  Data) const cached =Data(
cached;    (Datacached {..Code return    
;
  }

  // Store raw course data
  setCData,
Implement LRU eviction if
thisCache_{firstKey coursekeys value this.courseDataCache.delete first    
    courseset, ...data timestamp now });

  // Get from search  SearchCode    =Histfind =>Code);(entry !Dataentry {entry
    
  // to
SearchCode rawData, processedData)
existing entry
    this.searchHistoryCache = search.      .course);    front
    thisHistun      
      ,ed      .    
    maintain size limit (Histlength_LIMIT      Histpop }

  // Clear cclear() thisCache
    search= }  all search history entries
  Search
.Cache filter(
=> is()
  }  if need to fetch grouped courses
GroupseDataetchCode, groupses    (!oured. )
const =
const ofour
code !== !ourcode      missing code }
    ;
}defaultManager

. fetService

//.```{ API URL config c'../acheimport processysfrom analysisEngine';Service async fetchawData) // Check    =.Data);(
.cached course
;

    
.fetdataCode    response(`BASE api/course-raw/${courseCode}`
        .
error.      (|| to data }    await();    raw dataacheourcourse);    return
    ipl(eC
=.=>
fetchourcode catch(err => console.warn(`${code:
;));    results.all);results Boolean }getAnalys(analysisParams
search history    oryacheFromcourse    orythis.paramsMatchoryParamsParams {
log history for}`return.;

    raw data (from cache
Data.C(
    // if additional grouped courses missingGrouped =.edsF       DataC    
    if mis.0      (`${${ed',
edthisipl(ed
merge main dataset
      (Ced
group) for (, Object group.instances)) raw[${edcoursekey {
            ,_edcourse};
      }
    

    on frontend
edAnal(analys
// in search cadd(Code, process);    Data }ams1) return JSON params JSON params  

Data```Phase Update React Components hours .App.js

```javascript
// React Add imports importService/
Manager/';fetchAnalourys
fetchData = code,)  (!;

  Analys(  is(  Loading();try // Use new data service resultServiceyscode
:,:,_.ation});Anal(    courseName metadata current_||'data';TocodeeName
  (
error.'error if (Message No data') {error
Tocode No
const searchUrl = `://sen-jhu.ation.//?=${ode(
      ysNo evaluations code br></>evaluations found at this search: <search="_relener"}</
{Anal(`An error occurred, email icissna1@h.edu with the following information to prevent it from happening again:<br//}`}finally stop
  };

//ApplyAdvancedOptions to use locally
plyOptions ({AdvancedOptionsptions(  (!courseCode)

  validateYear = => if '') return    ed(10returnaNYeared2
  constYearValidYear filters.min_  earYear filters year ifearmax);Process locally we have data cached =.Data);(
    {processAnal(
options
options
        keys separ      setResult
    }) console.error processing, fetching from backend:', error fetchData,    }    No cached backendAnal(options }```52History Component

// quick-switch functionality
import cacheManager from '../utils/cacheManager';

In SearchupdateoryconstItemcourse{Check this in our cachedEntry =.History);() // instant switch - no

ItemClickCode cacprocess
{Fall back flow
Query(
Search course  
 .CourComponent
// modify support instant data loading
const handle({Received onLoadingChange, => currentC,ouronInstantData })  ... existing  handleory(instantData) => {
    if (instantData) {
      // From cache
      onInstcourseData);}    Query);Search);
  };};
Phase Testing & Optimization (1)51

//itor

class PerMon  
  this this = cacheH:
is0apiCalls,ProcessTime
ResponseTime:    CacheH{.ache
console.log(`Cache:.ache()}
  }  recordeM
metricsis  }Apiduration) this api
metricsTime duration }Local(
    metricsing(  getCRate    total metricsH.eM
> (this c/ Fixed);

vering
=.Time
.0      reduce, a times
0}Met
table({Cache Rate${ache()}      calls metricsalls'avg `${AingFixed)}ms`,
      avg `getApi().0
  }newance
 6Strategy Backend Changes1the new api raw` endpoint Keep existing endpoints for backward compatibility
###3to Vercel Frontend. feature flag `__false`
2Deploy cache disabled
with group of users Enable cache gradually

### Step: &
cache2usage Cache based on## 

Performance Goals:
- **Filter changes**: < 50ms → ms from 500-2000ms)- search switching**: ms1-000- hit % for repeat interactions
usage50MB user

Experience
instant feedback on all filter Spindata seamrecent Load %+

 

IndexedDB Storage**: cache across sessions
2**Worker offline.iveching-likely next. Updates**: changed data **Socket**:-updates

## Checklist

Tasks:
- [ ] Create `/api raw course_endpoint ] cors new endpoint ] with grouped courses
###- to

:] implementis
Implement.[ implement js ] js cache
- Update performance [ Searchinstant switching
Test all filter combinations ] loading states cache misses
###- with feature Testing [ testsis- tests- benchmarks
] leak tests

- [ ] Cross-## rollback Plan arise
disable cache via feature. back `/api//3client caches Monitor error rates

provides
Instant through frontend processing
- cminimize API calls
- **Search history** switching recent **backward compatibility backend
- **ualout

be in approximately 10of focused work tasks suitable for copy-AI-assisted Human't to the, that's too i'm to would interact with history period. think easiest thing to the the data, and then do all on Let you give me a simple implementationplerD that just does that?: Product Requirements Simple Frontend Processing for Course evaluations

1SummaryD simplified to eliminate filtering delays by fetching all raw data once and performing the performing all filtering and and calculations on the frontend.

##. Every filter change triggers a 0.5- second solution is to fetch
raw data once process client-side for instant.3

modify existing `/api/analyze` endpoint to optionally return raw
Python analysis to. all filtering/statistics on instant## Implementation Plan

1modification30

 .modify existing `backend.add raw data:```app api string:>','])_course data():
    endpoint filtering and analysis on

validate course
validate_():jsonerror course Expected format.###.###"}

    # normalize course to match stored format
    course
code code
(received analysis request: code try:
        Get the analysis parameters from        the
_.()not:jsonerror analysis request."}

        : for raw        analysis get_'):            data frontend processing____and___                        metadata
            from_=
:open metadata.'f    _.):
                
grouping
_ing.__            Collect all grouped courses
            _=
_update course
if group group_("courses"):grouped_code in["
grouped course
:grouped get data update grouped
grouped
key,_():    _"{}_{=
**value        course grouped                                

# course names
instances            = for, in.                 name'
_] course
            # raw data structure
            returnify "raw_instances":,metadata":__                _,
                _                from
_
all_
                
ing":
grouped__("]),"_":.",
is_grouped":(and group get
                })}
             

        existing continues for normal analysis
Phase Frontend Engine ( ####.`frontend utils/analys.

// Port of Python/analysis.py to JavaScript

const STAT_MAPP=ings  __frequency:
Name Overall    : Poor":, weak": "Satisfactory":, 5},__
    :    Poor,": "": "Good4excellent}
  _: display
{"1weak,actory, 5},load {Name work    Much lighter": "Lighter,": "Avier,avier}
  _: display    Disagree strongly": "somewhat": "disag3agree4agree5},_: displayName ",: 2satisf3": "Excellent   periods____: displayPeriods Run mapping
  }

simplify(
  (!typeof'"";
  .(/-]/g toLowerCase

eSemesterYearKey) const = match.((?:IN|U FA(\}));(
    const =];year20[
sem= IN,': ':      year,[||
  }
function  [0];
//}InstanceYear({match = match(?:|U(\})  ) return2000(]);
  return0

S({match..(:|IN)\})  seasons = FA Fall": "S"IN inters
seasons &&["
functionInstances(allInst) const filtered = {};
  const minYear = filters min parseInt min :;max.?.)
seasons = || [];
  constors instruct
  [key of() const year = get(        (year)    Year max;(&& !(eason continue if.instruct(.name
filtered =  
;exportateinstances, separation[  (!ationKeys === {
    All Data":.)}  Build instructor name map for consistent naming
  constifiedDisplayName = {};  (.instructor {tempMap    [key of Object(
      or.;(!instructcontinue
      =();(!)      periodTupleemkey if (!Map || periodTuple > temp][0]) temp]Tor      }    [, displayName] of Object temp
TosimplifiedName }
  
const groups = {};
  
  for [] entries {groupParts
for (KeyKeys      value = "Unknown
sepinstructor        simplified instance name "        simplinstruct
=Display]Name } sepyear") value = String((      ("
get(      elseKey_") value course "      (sep"_") const =(/([A-Z]{2}\$/d$/value =["      elseKey_code
instance code.(/([A-Z A\d+.\)?.["      } else {
        String(instanceKey Unknown }      .);
    const = group.", if (!Name[= groups].);
  return}calculateDetailedStat(isticsency,Mapping) constPoints  totalses;  [, Object frequ{(response && count > {value[
      ( <++) data(value }Respon;
    }    
  
  ifses)
mean:,::
  const data((, a total
  let std =
(> {variance = reduce((, x sum.-2)Respon1std sqrt
  
{    .* /
Math.round * /
total  

StatInstances,ToCalculinstanceKeys = [  Aggregate frequencies
all  ated = for ofTo{ated[{};
}  instance of) for (const stats) if (instance[{(, Object instance)) ifFrekey {
ated[];
          Frekey +=        }
    results =
details =
const ofate    Config = KEY
    key ===__") // Extract periods from instance keys
      periods Set for of {match match A22
match.[      values[replace_frequency', periods Array periods sort join '/      [('''n:,:
{detailed =Statated[Config
key_)] mean ;[('''n        :,.    }  ,}functionAnal(Instances,, metadata) {
  grouping{ 1filters filtered = filter(, filters
2into groups separated =ances params keys params.);
  
  // Calculate group
analysisResults = {};const statisticsMetadata = {};
  
  // Map frontend stat keys to backend keys
  const statsend=
const of(.filter =>.])    (stat ==='__
end(stat } (['_frequency''].includes {Backpush stat }      Keys stat');
  }  (Name of(separated
Get instance keys for this
KeysKeys keys).=>
[includes[
    result =istics stats,);    Map back to frontend keys
    isName
icsgroup{};    [end] entries values {
frontbackreplace',      [front=      adata][].end    }
  return  data data:,:
,ing group

metadataMet};``` App.js (1 #### { processAnalysisRequest }/';Add state for raw constoursetour= null// fetchAnalysisData constiscode, options, forceBackend = false)
(!code

  we raw not forcing locally
rawData &&C.Code === for) try {
      resultys
        se,
          :,:,_.ation},C.        seingMet);Anal(          error      ('processing:',      // Fall to    }Analys();Anal(  Loading();

// raw data on  const params = {
    stats: options,:,_.,
_: true NEW FLAG raw };(`API__/}    '     Type application },:(
    .response    data.catch{}if (!response {Handle handling unchanged
      (.404 {
        || data?.error === 'No data found this') addToFoundSearchHistory 'data
searchUrl = `://asen-jationjhu.evaluevaluation///?=${encodeURIComponent(code
Anal(`course evaluations found code br><br/>evalufoundations search: <a search="_rel="ener">${a      
detail = data error string.'
Anal(`error email ic@issnaport1@j.following information to br to prevent it occfrom br/);
      setawData
ysnull return;
    raw    C({Code
data instances metadata metadata group:ing    //
    resultys
raw
      stats stats filters filters separation optionsKeys
data
group
    is);const courseName =.?.current_||'data';';Tocode);
  .(
    setAnal(`,nah the prevent again><String(error);Analysnull setournull })finallyLo
// handleDataReceived to clear raw handle=Cour) => setCournewCode setawCData // when  setismissGraceWar(Set
fetchAnalysisData(seanctrue); fetch
checkGracePeriod(se};// handleplyancuse local processingApedoptions)  ed);(!courseCode);  validateYear = () = => if '')
ed(     Nedpars 
    YearValid =Year filters_.);max= options max

min||ear;Always process locally if we
rawData && rawData.course=== {{resultys
ourinstances {:,: options,_.
                se,C.adata
ysresult }) console Frontend error // fall
yscourse,    }  //, from fetchData,);
};Update recheck to raw handleRe()  (!return
  startLo  {response =${_/check}`, method POST });    (response {Dismr(=> prev add));RawData(null // to force
      Anal(adv,
else constData.catch{}setAnal(`re${error Unknown);
  (
    ysRe${)  finally stop
  
};
```Summary

This the simplified approach:1ches per. filtering/statistics on for frontend
3cache management complexity
4. with grace period warnings
5. Filter changes separation after initial load



implementation time3-4The key- Backend: Add `_mode endpoint
Port Python
js raw locally- changes to history warnings features

: looks! you give me complete backend/app.py file changes?and of can

:'s backend/py the raw

from flask jsonfrom flask_FLASK import request
from json .scraper service import__, find_courses__,_check get grace_status
_import_instructor_variants_find db
from .process_analysis_, extract_course
_ing service importse
json

app name static../',_='/')

def Define validate_course():
    that a course code the XX.######.###
    Returns
True False
    """    not or_ :# extremely long

Pattern:2dot, digits (case insensitive)
    pattern'^Za-z]{}\d{3.\}    re pattern code Define allowed origins CORS, including a regex for Vercel preview deployments This is compatible with Flask-Cors >= 4.0.
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:5000",
    "https://course-evaluation-scraper.vercel.app",
    re.compile(r"^https://course-evaluation-scraper-[a-z0-9]+-[a-z0-9-]+\.vercel\.app$")
]
CORS(app, origins=allowed_origins)  # Enable Cross-Origin Resource Sharing

grouping_service = CourseGroupingService()

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/api/course/<string:course_code>')
def get_course_data(course_code):
    """
    API endpoint to get course evaluation data.
    It triggers the scraper if the data is not up-to-date in the cache.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    print(f"Received request for course code: {course_code}")
    try:
        # Call the centralized scraping and caching logic
        data = get_course_data_and_update_cache(course_code)
        if not data:
            return jsonify({"error": "No data found for this course."}), 404
        # Check if the response contains an error
        if isinstance(data, dict) and "error" in data:
            return jsonify(data), 500
        return jsonify(data)
    except Exception as e:
        # Log the exception for debugging
        print(f"An error occurred: {e}")
        # Return a generic error message to the client
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/search/course_name/<string:search_query>')
def search_by_course_name(search_query):
    """
    API endpoint to search for courses by name.
    """
    # Prevent extremely long search queries that could cause performance issues
    if len(search_query) > 1000:
        return jsonify({"error": "Search query too long. Maximum 1000 characters allowed."}), 400

    print(f"Received search request for: {search_query}")
    try:
        course_codes = find_courses_by_name(search_query)
        return jsonify(course_codes)
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({"error": "An internal server error occurred during search."}), 500

@app.route('/api/search/instructor/<string:instructor_name>')
def search_by_instructor_name(instructor_name):
    """
    API endpoint to find variations of an instructor's name.
    """
    # Prevent extremely long instructor names that could cause performance issues
    if len(instructor_name) > 1000:
        return jsonify({"error": "Instructor name too long. Maximum 1000 characters allowed."}), 400

    print(f"Received instructor search for: {instructor_name}")
    try:
        variants = find_instructor_variants_db(instructor_name)
        return jsonify(variants)
    except Exception as e:
        print(f"An error occurred during instructor search: {e}")
        return jsonify({"error": "An internal server error occurred during instructor search."}), 500

@app.route('/api/grace-status/<string:course_code>')
def get_grace_status(course_code):
    """
    API endpoint to check if a course needs grace period warning.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    try:
        status = get_course_grace_status(course_code)
        return jsonify(status)
    except Exception as e:
        print(f"An error occurred checking grace status: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/recheck/<string:course_code>', methods=['POST'])
def recheck_course_data(course_code):
    """
    API endpoint to force recheck course data during grace periods.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    print(f"Received force recheck request for course: {course_code}")
    try:
        data = force_recheck_course(course_code)
        if not data:
            return jsonify({"error": "No data found for this course."}), 404
        # Check if the response contains an error
        if isinstance(data, dict) and "error" in data:
            return jsonify(data), 500
        return jsonify(data)
    except Exception as e:
        print(f"An error occurred during recheck: {e}")
        return jsonify({"error": "An internal server error occurred during recheck."}), 500

@app.route('/api/analyze/<string:course_code>', methods=['POST'])
def analyze_course_data(course_code):
    """
    API endpoint to perform filtering and separation analysis on course data.
    Modified to support raw data mode for frontend processing.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    print(f"Received analysis request for course: {course_code}")
    try:
        # Get the analysis parameters from the request body
        analysis_params = request.get_json()
        if not analysis_params:
            return jsonify({"error": "Missing analysis parameters in request body."}), 400

        # Check if requesting raw data for frontend processing
        if analysis_params.get('raw_data_mode'):
            print(f"Raw data mode requested for {course_code}")
            
            # Get all the data for the course
            all_course_data = get_course_data_and_update_cache(course_code)
            
            # Get metadata
            metadata_from_file = {}
            try:
                with open('metadata.json', 'r') as f:
                    metadata_from_file = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Get grouping info
            group_info = grouping_service.get_group_info(course_code)
            grouped_courses = []
            all_instances = {}
            
            if group_info and group_info.get("courses"):
                grouped_courses = group_info["courses"]
                
                # Add main course data
                if all_course_data:
                    all_instances.update(all_course_data)
                
                # Fetch data for all grouped courses
                for grouped_code in grouped_courses:
                    if grouped_code != course_code:
                        try:
                            grouped_data = get_course_data_and_update_cache(grouped_code)
                            if grouped_data and isinstance(grouped_data, dict):
                                # Add course_code field to each instance for separation
                                for instance_key, instance_data in grouped_data.items():
                                    if isinstance(instance_data, dict):
                                        instance_data_with_code = instance_data.copy()
                                        instance_data_with_code['course_code'] = grouped_code
                                        all_instances[f"{grouped_code}_{instance_key}"] = instance_data_with_code
                        except Exception as e:
                            print(f"Warning: Could not load grouped course {grouped_code}: {e}")
            else:
                # No grouping, just use the main course data
                if all_course_data:
                    all_instances.update(all_course_data)
            
            # Extract course names for metadata
            course_names = {}
            for instance_key, instance_data in all_instances.items():
                if 'course_name' in instance_data:
                    course_names[instance_key] = instance_data['course_name']
            
            # Get course metadata
            course_metadata = extract_course_metadata(
                course_names, 
                course_code, 
                metadata_from_file,
                primary_course_code=course_code,
                primary_course_has_no_data=not all_course_data
            )
            
            # Return raw data structure
            return jsonify({
                "raw_data": {
                    "instances": all_instances,
                    "metadata": {
                        "current_name": course_metadata.get("current_name"),
                        "former_names": course_metadata.get("former_names", []),
                        **{k: v for k, v in course_metadata.items() 
                           if k not in ["current_name", "former_names"]}
                    },
                    "grouping_metadata": {
                        "grouped_courses": grouped_courses,
                        "group_description": group_info.get("description", "") if group_info else "",
                        "is_grouped": bool(grouped_courses and len(grouped_courses) > 1)
                    }
                }
            })

        # Otherwise, use existing backend processing (backward compatibility)
        all_course_data = get_course_data_and_update_cache(course_code)

        # If no data, check for groupings before returning an error
        if not all_course_data:
            group_info = grouping_service.get_group_info(course_code)
            if not group_info or not group_info.get("courses"):
                return jsonify({"error": "No data found for this course."}), 404
            # If grouped, proceed with an empty dict; analysis module will fetch grouped data
            all_course_data = {}

        # Check if the response contains an error (e.g., from scraping)
        if isinstance(all_course_data, dict) and "error" in all_course_data:
            return jsonify(all_course_data), 500

        # Process the data using the analysis module
        results = process_analysis_request(
            all_course_data,
            analysis_params,
            primary_course_code=course_code
        )
        if results is None:
            return jsonify({"error": "No data found for this course."}), 404
        return jsonify(results)

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return jsonify({"error": "An internal server error occurred during analysis."}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

This implementation adds the `raw_data_mode` flag to the existing `/api/analyze` endpoint. When this flag is set to `true`, the endpoint returns all raw course data including grouped courses, without performing any analysis. This allows the frontend to:

1. Fetch all data once when a course is first searched
2. Perform all filtering and statistical calculations locally
3. Achieve instant response times for filter changes

The implementation maintains backward compatibility - existing functionality continues to work when `raw_data_mode` is not set.

"""One-time, read-only comparison of course and professor percentile populations.

    python3 one-time-scripts/analyze_professor_percentiles.py --database
    python3 one-time-scripts/analyze_professor_percentiles.py --input data.json
    python3 one-time-scripts/analyze_professor_percentiles.py --snapshot snapshot.json

Requires numpy/matplotlib; database mode also uses the backend dependencies.
Writes reports only; never updates application code or a saved benchmark.
Primary comparison uses equal entity weights (the app's default). Professor
means pool student responses, preserving literal trimmed instructor names.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.percentiles import build_benchmark, METRICS, PERIOD
from analyze_size_weighted_percentiles import aggregate, midrank_mapping, write_csv, table

LABELS = {'overall_quality': 'Overall quality', 'workload': 'Workload'}
CODE = re.compile(r'^([A-Z]{2,}\.\d{3}\.\d{3})(?:\.|$)')


def load_source(args):
    if args.database:
        from backend.db_utils import get_db_connection
        with get_db_connection() as conn:
            conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
            with conn.cursor() as cur:
                cur.execute('SELECT instance_key, course_code, data FROM courses ORDER BY instance_key')
                records = cur.fetchall()
                cur.execute("SELECT payload, pending_evaluations FROM percentile_benchmarks WHERE benchmark_id = 'current'")
                row = cur.fetchone()
        payload = {'records': records, 'saved_benchmark': row[0] if row else None,
                   'pending_evaluations': row[1] if row else None}
        source = 'Live database, repeatable-read read-only transaction'
    elif args.snapshot:
        payload = json.loads(args.snapshot.read_text())
        source = f'Read-only database snapshot: {args.snapshot.resolve()}'
    else:
        data = json.loads(args.input.read_text())
        payload = {'records': [(key, m[1], record) for key, record in data.items() if (m := CODE.match(key))],
                   'saved_benchmark': None, 'pending_evaluations': None}
        source = f'Local export: {args.input.resolve()}'
    return payload, source


def professor_totals(records, course_groups):
    membership = {code: codes for codes in course_groups for code in codes}
    professors, pairs = {}, {}
    audit = defaultdict(int)
    for key, code, record in records:
        if not isinstance(record, dict):
            audit['non_object_records'] += 1
            continue
        name = record.get('instructor_name')
        name = name.strip() if isinstance(name, str) else ''
        if not name:
            audit['reports_without_professor_name'] += 1
            continue
        if not PERIOD.search(key):
            audit['named_reports_without_parseable_period'] += 1
        for identity, collection in [(name, professors), ((name, membership[code]), pairs)]:
            entry = collection.setdefault(identity, {'reports': 0, 'courses': set(), 'metrics': {}})
            entry['reports'] += 1
            entry['courses'].add(membership[code])
            for metric in LABELS:
                frequency = record.get(metric + '_frequency') or {}
                tally = entry['metrics'].setdefault(metric, {'total': 0, 'n': 0})
                for label, count in frequency.items():
                    if label not in METRICS[metric] or not isinstance(count, (int, float)) or isinstance(count, bool):
                        continue
                    if not math.isfinite(count) or count <= 0 or count != int(count):
                        continue
                    if count > 2**53 - 1:
                        raise ValueError('Count exceeds the frontend safe-integer limit')
                    tally['total'] += METRICS[metric][label] * int(count)
                    tally['n'] += int(count)
    audit['literal_professor_names'] = len(professors)
    return professors, pairs, dict(audit)


def describe(means):
    return {'count': len(means), 'mean': float(np.mean(means)), 'sd': float(np.std(means, ddof=1)),
            **{key: float(value) for key, value in zip(['p05', 'p25', 'median', 'p75', 'p95'], np.quantile(means, [.05,.25,.5,.75,.95]))}}


def shift_summary(before, after):
    change = after - before
    absolute = np.abs(change)
    result = {'mean_signed_shift_pp': float(change.mean()), 'median_signed_shift_pp': float(np.median(change)),
              'median_absolute_shift_pp': float(np.median(absolute)), 'p95_absolute_shift_pp': float(np.quantile(absolute,.95)),
              'maximum_absolute_shift_pp': float(absolute.max()),
              'percent_increasing': float(100*np.mean(change > 1e-10)),
              'percent_decreasing': float(100*np.mean(change < -1e-10))}
    for threshold in (1,5,10):
        result[f'percent_moving_at_least_{threshold}_pp'] = float(100*np.mean(absolute >= threshold))
    for cutoff in (90,95,99):
        result[f'above_{cutoff}_before'] = int(np.sum(before >= cutoff))
        result[f'above_{cutoff}_after'] = int(np.sum(after >= cutoff))
        result[f'entering_{cutoff}'] = int(np.sum((before < cutoff) & (after >= cutoff)))
        result[f'leaving_{cutoff}'] = int(np.sum((before >= cutoff) & (after < cutoff)))
    return result


def format_display(values):
    # Use the app's actual rounding and extreme-percentile display function.
    module = ROOT / 'frontend/src/utils/percentiles.js'
    javascript = """import fs from 'node:fs';
const code = fs.readFileSync(process.argv[1], 'utf8');
const { formatPercentile } = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'));
const values = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(values.map(formatPercentile)));
"""
    result = subprocess.run(['node', '--input-type=module', '-e', javascript, str(module)],
                            input=json.dumps(values), text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def compare(courses, professors, pairs, fresh, saved):
    summaries, professor_rows, pair_rows, mappings = {}, [], [], []
    plot_data = {}
    for metric, label in LABELS.items():
        course_entries = [g['metrics'][metric] for g in courses.values() if metric in g['metrics']]
        course_means = np.array([g['total']/g['n'] for g in course_entries])
        eligible = [(name,g) for name,g in sorted(professors.items()) if g['metrics'][metric]['n']]
        means = np.array([g['metrics'][metric]['total']/g['metrics'][metric]['n'] for _,g in eligible])
        indices = np.floor(means*100+.5).astype(int)-100
        course_indices = np.floor(course_means*100+.5).astype(int)-100
        course_map = midrank_mapping(course_indices, np.ones(len(course_means)))
        if not np.allclose(course_map, fresh['metrics'][metric]['percentiles'], atol=1e-10, rtol=0):
            raise ValueError(f'Course mapping fails production parity for {metric}')
        professor_map = midrank_mapping(indices, np.ones(len(means)))
        if np.any(np.diff(professor_map) < -1e-10):
            raise ValueError('Professor mapping is not monotonic')
        after, before = professor_map[indices], course_map[indices]
        if not math.isclose(float(after.mean()), 50, abs_tol=1e-10):
            raise ValueError('Equal-professor midranks must average to 50')
        saved_map = np.array(saved['metrics'][metric]['percentiles']) if saved and saved.get('version') == 3 else course_map
        summary = {'label': label, 'course_distribution': describe(course_means), 'professor_distribution': describe(means),
                   'isolated_population_change': shift_summary(before, after),
                   'from_saved_benchmark': shift_summary(saved_map[indices], after),
                   'maximum_saved_vs_fresh_mapping_difference_pp': float(np.max(np.abs(saved_map-course_map)))}
        well_sampled = np.array([g['metrics'][metric]['n'] >= 20 for _,g in eligible])
        summary['professors_with_at_least_20_answers'] = int(well_sampled.sum())
        summary['change_for_professors_with_at_least_20_answers'] = shift_summary(before[well_sampled], after[well_sampled])
        for i,(name,g) in enumerate(eligible):
            professor_rows.append({'metric':metric,'professor':name,'mean_score':float(means[i]),
                                  'responses':g['metrics'][metric]['n'],'course_groups':len(g['courses']),
                                  'reports':g['reports'],'current_saved_percentile':float(saved_map[indices[i]]),
                                  'fresh_course_percentile':float(before[i]),'hypothetical_professor_percentile':float(after[i]),
                                  'change_pp':float(after[i]-before[i]),'change_from_saved_pp':float(after[i]-saved_map[indices[i]])})
        pb,pa=[],[]
        for (name,codes),g in sorted(pairs.items()):
            tally=g['metrics'][metric]
            if not tally['n']:
                continue
            mean=tally['total']/tally['n']
            index=math.floor(mean*100+.5)-100
            pb.append(course_map[index]); pa.append(professor_map[index])
            pair_rows.append({'metric':metric,'professor':name,'course_codes':'/'.join(codes),
                              'mean_score':mean,'responses':tally['n'],'current_saved_percentile':float(saved_map[index]),
                              'fresh_course_percentile':float(course_map[index]),'hypothetical_professor_percentile':float(professor_map[index]),
                              'change_pp':float(professor_map[index]-course_map[index])})
        summary['professor_course_rows']={'count':len(pb), **shift_summary(np.array(pb), np.array(pa))}
        for index in range(401):
            mappings.append({'metric':metric,'score':(index+100)/100,'current_saved_percentile':float(saved_map[index]),
                             'fresh_course_percentile':float(course_map[index]),'hypothetical_professor_percentile':float(professor_map[index]),
                             'change_pp':float(professor_map[index]-course_map[index])})
        summaries[metric]=summary
        plot_data[metric]={'courses':course_means,'professors':means,'course_map':course_map,'professor_map':professor_map,
                           'before':before,'after':after}
    for rows in (professor_rows,pair_rows,mappings):
        displays=format_display([row[key] for row in rows for key in ('current_saved_percentile','fresh_course_percentile','hypothetical_professor_percentile')])
        for i,row in enumerate(rows):
            row['current_saved_display'],row['fresh_course_display'],row['hypothetical_professor_display']=displays[3*i:3*i+3]
    for metric,summary in summaries.items():
        rows=[r for r in professor_rows if r['metric']==metric]
        summary['percent_display_strings_changed_from_saved']=100*sum(r['current_saved_display']!=r['hypothetical_professor_display'] for r in rows)/len(rows)
    return summaries,professor_rows,pair_rows,mappings,plot_data


def plots(out, data, years):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    colors=['#297c9b','#d77832']
    for col,(metric,label) in enumerate(LABELS.items()):
        d=data[metric]; ax=axes[0,col]
        bins=np.linspace(1,5,41)
        for kind,color,title in zip(('courses','professors'),colors,('Course averages','Professor averages')):
            values=d[kind]
            ax.hist(values,bins=bins,weights=np.full(len(values),100/len(values)),histtype='step',linewidth=2,color=color,
                    label=f'{title} (n={len(values):,})')
        ax.set(title=label,xlim=(1,5),xlabel='Average score (1–5)',ylabel='Share of population in each 0.10 bin (%)')
        ax.legend(frameon=False,fontsize=9)
        ax.grid(axis='y',alpha=.15)
        ax=axes[1,col]
        scores=np.linspace(1,5,401)
        ax.plot(scores,d['course_map'],color=colors[0],lw=2,label='Before: compared with courses')
        ax.plot(scores,d['professor_map'],color=colors[1],lw=2,label='After: compared with professors')
        ax.set(xlim=(1,5),ylim=(0,100),xlabel='Unchanged professor average score',ylabel='Displayed percentile (before rounding)')
        ax.legend(frameon=False,fontsize=9,loc='upper left')
        ax.grid(alpha=.15)
    fig.suptitle('What changes when professors are compared with professors?',fontsize=18,fontweight='bold',x=.07,ha='left',y=.98)
    fig.text(.07,.925,f'{years} • All stored years and seasons • Equal weight per course / professor',color='#475569')
    fig.text(.07,.025,'Means pool student responses. Names follow the app’s existing literal grouping. Higher workload percentile means heavier workload.\nOnly the comparison population changes; raw scores stay fixed.',fontsize=9,color='#475569')
    fig.subplots_adjust(left=.075,right=.98,bottom=.14,top=.86,hspace=.37,wspace=.23)
    fig.savefig(out/'comparison.png',dpi=180,facecolor='white')
    plt.close(fig)


def report(out, provenance, summaries, professors, mappings):
    lines=['# Course versus professor percentiles: one-time analysis','',
           f"Source: {provenance['source']}. {provenance['records']:,} reports; {provenance['year_coverage']}. Generated {provenance['generated_at']}.",'',
           'The primary hypothetical replaces the course reference population with one all-history average per recorded professor. Each entity counts equally, matching the default percentile weighting setting. The professor’s raw 1–5 score is unchanged: both versions pool valid student responses, rather than averaging course means. Quality means **overall course quality**, the existing quality metric; it is not instructor effectiveness.','',
           '## Distribution of average scores','',
           table(['Metric','Population','Count','Mean','SD','25th pct','Median','75th pct'],
                 [[s['label'],population,f"{d['count']:,}",*[f'{d[k]:.3f}' for k in ('mean','sd','p25','median','p75')]]
                  for s in summaries.values() for population,d in [('Courses',s['course_distribution']),('Professors',s['professor_distribution'])]]),'',
           '## Effect on each professor’s overall percentile','',
           'Positive changes mean a higher percentile. Changes below isolate the reference-population change using course and professor distributions built from the same snapshot.','',
           table(['Metric','Mean change (pp)','Median change (pp)','Median |change|','95th pct |change|','Max |change|','Move ≥5 pp','Move ≥10 pp'],
                 [[s['label'],f"{d['mean_signed_shift_pp']:+.2f}",f"{d['median_signed_shift_pp']:+.2f}",f"{d['median_absolute_shift_pp']:.2f}",f"{d['p95_absolute_shift_pp']:.2f}",f"{d['maximum_absolute_shift_pp']:.2f}",f"{d['percent_moving_at_least_5_pp']:.1f}%",f"{d['percent_moving_at_least_10_pp']:.1f}%"]
                  for s in summaries.values() for d in [s['isolated_population_change']]]),'',
           '![Distributions and percentile mappings](comparison.png)','',
           '## Example scores: what the app would show','',
           '“Current saved” uses the saved database mapping. “Fresh courses” rebuilds the same course method from this snapshot; “Professors” is the hypothetical mapping. Display text comes from the app’s actual formatter.','',
           table(['Metric','Raw score','Current saved','Fresh courses','Professors','Change from fresh (pp)'],
                 [[LABELS[r['metric']],f"{r['score']:.2f}",r['current_saved_display'],r['fresh_course_display'],r['hypothetical_professor_display'],f"{r['change_pp']:+.2f}"]
                  for r in mappings if r['score'] in ({3.5,4.,4.25,4.5,4.75,5.} if r['metric']=='overall_quality' else {2.5,3.,3.25,3.5,4.,4.5})]),'',
           '## Current saved benchmark and visible course rows','',
           f"The saved benchmark has {provenance['pending_evaluations']} pending new evaluation reports. Its generation time is {provenance['saved_generated_at']}. Comparing fresh populations isolates this hypothetical from routine benchmark refreshes. The CSVs also include exact before/after values from the saved mapping.",'',
           table(['Metric','Max saved/fresh map difference (pp)','Mean change from saved (pp)','Display strings changed'],
                 [[s['label'],f"{s['maximum_saved_vs_fresh_mapping_difference_pp']:.3f}",f"{s['from_saved_benchmark']['mean_signed_shift_pp']:+.2f}",f"{s['percent_display_strings_changed_from_saved']:.1f}%"] for s in summaries.values()]),'',
           'Professor views can separate results by course. Applying the same hypothetical professor benchmark to those course-specific scores has the following effects (all years, no filters):','',
           table(['Metric','Professor/course rows','Mean change (pp)','Median |change|','Move ≥5 pp'],
                 [[s['label'],f"{d['count']:,}",f"{d['mean_signed_shift_pp']:+.2f}",f"{d['median_absolute_shift_pp']:.2f}",f"{d['percent_moving_at_least_5_pp']:.1f}%"] for s in summaries.values() for d in [s['professor_course_rows']]]),'',
           '## Largest changes for well-sampled professors','',
           'One representative per hundredth-score bucket per metric, with at least 20 valid answers; choose the largest response count within a bucket. These are descriptive examples, not reliability rankings.','']
    for metric,label in LABELS.items():
        buckets={}
        for r in professors:
            if r['metric']==metric and r['responses']>=20:
                key=math.floor(r['mean_score']*100+.5)
                if key not in buckets or r['responses']>buckets[key]['responses']:
                    buckets[key]=r
        chosen=sorted(buckets.values(),key=lambda r:-abs(r['change_pp']))[:5]
        lines += [f'### {label}','',table(['Recorded professor','Score','Answers','Before (fresh)','After','Change (pp)'],
                   [[r['professor'],f"{r['mean_score']:.3f}",r['responses'],r['fresh_course_display'],r['hypothetical_professor_display'],f"{r['change_pp']:+.2f}"] for r in chosen]),'']
    lines += ['## Method and checks','',
              '- Course groups use the existing grouping service. Every course mapping entry is checked against the production benchmark builder.',
              '- Professor identities are exact trimmed recorded names; name variants and multi-instructor strings remain separate, matching the app. This counts recorded identities, not necessarily distinct people.',
              '- Both mappings use means rounded to the nearest hundredth and midranks: 100 × (number below + half the tied number) / population size. No smoothing or minimum-response cutoff is introduced.',
              '- SD above is the sample SD between entity averages, not the SD between individual student ratings. Quantiles use linear interpolation of unrounded entity means.',
              '- Equal-professor midranks are checked to average to 50; percentile mappings must be monotonic. Detailed results include a ≥20-answer sensitivity cohort.',
              '- Rank ordering by the same raw metric stays monotonic, although hundredth-score buckets can tie. Workload percentiles indicate heaviness, not desirability.',
              '- This evaluates the default equal-weight mode. The optional class-size weighting would require a separate choice of professor weight and is not changed or modeled here.',
              f"- Data audit: {json.dumps(provenance['audit'], sort_keys=True)}.",
              '- No application code, stored evaluations, or saved benchmark was changed. Database reads used an enforced read-only transaction.','',
              'Files: `professor_percentiles.csv` (every professor), `professor_course_percentiles.csv` (every professor/course row), `score_mappings.csv` (all 401 score buckets), `summary.json`, and `comparison.png`.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    source=parser.add_mutually_exclusive_group()
    source.add_argument('--input',type=Path,default=ROOT/'data.json')
    source.add_argument('--snapshot',type=Path)
    source.add_argument('--database',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'overnight-review/professor-percentiles')
    args=parser.parse_args()
    payload,source_label=load_source(args)
    records=payload['records']; saved=payload['saved_benchmark']
    courses,course_audit=aggregate(records)
    professors,pairs,audit=professor_totals(records,courses)
    fresh=build_benchmark(records)
    summaries,professor_rows,pair_rows,mappings,data=compare(courses,professors,pairs,fresh,saved)
    provenance={'source':source_label,'records':len(records),'generated_at':datetime.now(timezone.utc).isoformat(),
                'year_coverage':fresh['year_coverage'],'saved_generated_at':saved.get('generated_at') if saved else None,
                'pending_evaluations':payload['pending_evaluations'],'audit':{**course_audit,**audit},
                'records_sha256':hashlib.sha256(json.dumps(sorted(records,key=lambda r:r[0]),sort_keys=True).encode()).hexdigest()}
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'professor_percentiles.csv',professor_rows)
    write_csv(out/'professor_course_percentiles.csv',pair_rows)
    write_csv(out/'score_mappings.csv',mappings)
    (out/'summary.json').write_text(json.dumps({'provenance':provenance,'metrics':summaries},indent=2)+'\n')
    plots(out,data,fresh['year_coverage'])
    report(out,provenance,summaries,professor_rows,mappings)
    print(json.dumps({'output':str(out),'provenance':provenance,'metrics':summaries},indent=2))


if __name__=='__main__':
    main()

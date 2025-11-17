# Clinical Stage Classification Definition

## Summary
Based on analysis of 5,786 clinical trials across 1,080 companies, we define "Clinical Stage" companies as those with **active or recent clinical trial activity**.

## Classification Logic

### Clinical Stage Company
A company is classified as "Clinical Stage" if it meets ANY of these criteria:

1. **Active Trials**: Has at least one trial with status:
   - `RECRUITING`
   - `ACTIVE_NOT_RECRUITING`
   - `ENROLLING_BY_INVITATION`
   - `NOT_YET_RECRUITING`

2. **Recent Trials**: Has completed trials within the last 2 years
   - Completion date > (current date - 2 years)
   - Even if status is `COMPLETED` or `TERMINATED`

### NOT Clinical Stage
Companies should NOT be classified as "Clinical Stage" if they only have:
- Trials completed more than 2 years ago
- Trials with status `WITHDRAWN` or `SUSPENDED` (unless they have other active trials)

## Data Insights

### Current Distribution (from database analysis):
- **676 companies** have active trials
- **145 companies** have recent trials (completed < 2 years)
- **259 companies** have only old trials (> 2 years)
- Total: 1,080 companies with any trial history

### Trial Status Breakdown:
- Completed: 3,092 trials (53%)
- Recruiting: 849 trials (15%)
- Active (not recruiting): 421 trials (7%)
- Terminated: 626 trials (11%)
- Other statuses: 798 trials (14%)

## Implementation in Code

```python
def classify_clinical_stage(company_trials):
    """
    Determine if a company should be classified as Clinical Stage
    """
    # Check for active trials
    active_statuses = ['RECRUITING', 'ACTIVE_NOT_RECRUITING',
                      'ENROLLING_BY_INVITATION', 'NOT_YET_RECRUITING']

    has_active = any(trial.status in active_statuses for trial in company_trials)

    if has_active:
        return 'Clinical Stage', 'Has active trials'

    # Check for recent trials (within 2 years)
    two_years_ago = datetime.now() - timedelta(days=730)
    has_recent = any(
        trial.completion_date and trial.completion_date > two_years_ago
        for trial in company_trials
    )

    if has_recent:
        return 'Clinical Stage', 'Recent trials (< 2 years)'

    # Has trials but all are old
    if company_trials:
        return 'Private', 'Only old trials (> 2 years)'

    return None, 'No clinical trials'
```

## Rationale

This definition ensures:
1. **Accuracy**: Companies actively developing drugs are correctly identified
2. **Recency**: Companies that recently completed trials are still considered clinical stage
3. **Clarity**: Companies that haven't had trials in >2 years are not mislabeled
4. **Investor Relevance**: The classification reflects current clinical activity, which is most relevant for job seekers and investors

## Edge Cases

1. **Acquired Companies**: If a company was acquired but still has active trials under its name, it remains "Clinical Stage"
2. **Suspended Trials**: Companies with only suspended trials should be reviewed case-by-case
3. **Multiple Trial Phases**: Use the most recent/active trial to determine status

## Update Frequency

This classification should be refreshed:
- Monthly for active trial status changes
- Quarterly for comprehensive review
- Immediately when new trial data is imported

---

*Last Updated: November 2025*
*Based on analysis of Bay Area Biotech Database v5*
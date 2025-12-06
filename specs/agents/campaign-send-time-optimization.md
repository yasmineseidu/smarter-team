# Send Time Optimization Agent - Production Specification

## Agent Identity

**Name**: `campaign_send_time_optimization`

**Category**: Campaign & Outreach

**Purpose**: Automatically optimize email send times for each lead by detecting timezones, analyzing engagement patterns, and continuously learning from performance data to maximize open and reply rates.

## Role & Responsibilities

The Send Time Optimization Agent ensures emails are sent when recipients are most likely to engage, combining timezone awareness with data-driven pattern recognition and statistical rigor.

**Core Functions**:
- Detect accurate timezones from company location and email metadata
- Apply business hour rules and engagement-based timing windows
- Track individual lead engagement patterns over time
- Perform cohort analysis by industry, role, and company size
- Run A/B tests on send times with statistical significance
- Continuously optimize based on performance feedback
- Schedule sends through Instantly API with optimal timing

## System Prompt

```
You are a send time optimization specialist for cold email campaigns. Your mission is to maximize engagement by sending emails at the perfect time for each recipient.

**Your Expertise:**
- Timezone detection with confidence scoring
- Business hour optimization across industries
- Engagement pattern analysis and prediction
- Statistical A/B testing with chi-square significance
- Cohort-based timing recommendations

**Phase 1: Basic Timezone & Business Hours**
- Detect timezone from company location (city, country)
- Apply business hours: 9 AM - 5 PM local time
- Avoid Monday before 10 AM and Friday after 3 PM
- Default to 10:30 AM local time if no pattern exists

**Phase 2: Individual Pattern Recognition**
- Track when each lead opens/replies to emails
- Build engagement profiles (preferred days/times)
- Adjust send times based on personal patterns
- Weight recent engagement more heavily (last 90 days)

**Phase 3: Cohort Intelligence**
- Analyze patterns by industry (e.g., CFOs in SaaS respond 6-8 AM)
- Segment by role (C-level, VP, Director, Manager)
- Consider company size (startup vs enterprise)
- Apply geographic/cultural business norms

**Phase 4: Continuous Optimization**
- Run A/B tests on send times per campaign
- Use chi-square test, 95% confidence, min 100 samples
- Update patterns weekly based on performance
- Maintain statistical significance in recommendations

**Decision Logic:**
1. Use individual pattern if >5 engagements exist
2. Else use cohort pattern if enough data
3. Else use timezone + business hours
4. Always check for national holidays
5. Avoid sending during known vacation periods

**Quality Rules:**
- Never send outside 8 AM - 7 PM local time
- Require minimum 3-hour gap between sends to same lead
- Respect unsubscribe requests and quiet periods
- Validate timezone confidence before scheduling

Your optimizations directly impact campaign success rates. Be data-driven but practical - perfect is the enemy of good when timing matters.
```

## Input Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class LeadTimingData(BaseModel):
    """Input for optimizing send time for a lead."""

    lead_id: str = Field(..., description="UUID of lead")
    campaign_id: str = Field(..., description="Instantly campaign ID")
    company_location: Optional[str] = Field(None, description="Company location (city, country)")
    industry: Optional[str] = Field(None, description="Industry sector")
    role: Optional[str] = Field(None, description="Job title/role")
    company_size: Optional[str] = Field(None, description="Company size (e.g., '50-100', '1000+')")
    email_headers: Optional[dict] = Field(None, description="Email metadata for timezone hints")
    previous_engagements: list[dict] = Field(default_factory=list, description="Past opens/replies with timestamps")
    priority: Literal["critical", "high", "normal", "low"] = Field(default="normal")

class BatchTimingOptimization(BaseModel):
    """Batch of leads for timing optimization."""

    batch_id: str = Field(..., description="UUID for this optimization batch")
    leads: list[LeadTimingData] = Field(..., min_items=1, max_items=500)
    optimization_level: Literal["basic", "individual", "cohort", "full"] = Field(default="basic")
    ab_test_enabled: bool = Field(default=False)
```

## Output Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class OptimizedSendTime(BaseModel):
    """Optimal send time for a single lead."""

    lead_id: str
    suggested_send_time: datetime = Field(..., description="UTC datetime to send")
    local_send_time: str = Field(..., description="Formatted local time")
    timezone: str = Field(..., description="IANA timezone")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this timing")
    reasoning: str = Field(..., description="Why this time was chosen")
    data_sources: list[str] = Field(default_factory=list, description=["timezone", "individual", "cohort"])
    should_ab_test: bool = Field(default=False)
    ab_test_variant: Optional[Literal["A", "B"]] = None

class BatchOptimizationResult(BaseModel):
    """Results from batch timing optimization."""

    batch_id: str
    optimized_count: int
    skipped_count: int  # Insufficient data
    ab_test_count: int
    optimizations: list[OptimizedSendTime]
    processing_time_ms: float
    optimization_summary: dict[str, int]  # Breakdown by reasoning type
    processed_at: datetime = Field(default_factory=datetime.utcnow)
```

## Tools

### 1. `detect_timezone`

**Purpose**: Accurately detect lead's timezone with confidence scoring.

**Parameters**:
```python
class TimezoneDetectionParams(BaseModel):
    lead_id: str
    company_location: Optional[str]  # "San Francisco, CA" or "London, UK"
    email_headers: Optional[dict]    # Email metadata
    ip_address: Optional[str]        # For geolocation fallback
```

**Returns**:
```python
class TimezoneDetectionResult(BaseModel):
    timezone: str                    # IANA timezone (e.g., "America/New_York")
    confidence: float               # 0.0 - 1.0
    source: Literal["company_location", "email_headers", "ip_geolocation", "memory", "default"]
    utc_offset: str                 # "+/-HH:MM"
    country_code: str               # "US", "GB", etc.
```

**Implementation**:
- Check Zep memory first for previously confirmed timezone
- Parse company_location using geocoding API (e.g., OpenStreetMap Nominatim)
- Extract timezone hints from email headers (Date header, etc.)
- Use IP geolocation as last resort (ipinfo.io or ipapi.co)
- Default to "America/New_York" if all else fails
- Cache results for 7 days

**Error Handling**:
- Invalid location format → Try parsing parts, then default
- Geocoding API down → Use email headers, then default
- Rate limit → Cache results, use secondary sources

### 2. `get_business_hours`

**Purpose**: Calculate valid business hours for a timezone with industry-specific adjustments.

**Parameters**:
```python
class BusinessHoursParams(BaseModel):
    timezone: str
    industry: Optional[str]
    role: Optional[str]
    date: datetime                 # Date to check for holidays
```

**Returns**:
```python
class BusinessHoursResult(BaseModel):
    start_hour_local: int          # 9 for 9 AM
    end_hour_local: int            # 17 for 5 PM
    valid_days: list[int]          # [0, 1, 2, 3, 4] for Mon-Fri
    exceptions: list[str]          # ["Avoid Monday before 10 AM"]
    holidays: list[datetime]       # Holidays on this date
    optimal_window: dict           # {"start": "10:30", "end": "11:30"}
```

**Implementation**:
- Base hours: 9 AM - 5 PM local time
- Industry adjustments:
  - Finance: Avoid market open/close (9:30 AM, 4 PM)
  - Healthcare: Avoid lunch (12-1 PM)
  - Tech: Later start (10 AM), later end (6 PM)
- Role adjustments:
  - C-level: Earlier (8 AM) or later (6 PM)
  - Sales: Mid-morning best (10-11 AM)
- Check national holidays using holidays API
- Avoid Monday <10 AM and Friday >3 PM

### 3. `analyze_engagement_patterns`

**Purpose**: Build individual engagement profile from historical data.

**Parameters**:
```python
class EngagementAnalysisParams(BaseModel):
    lead_id: str
    engagement_history: list[dict]  # [{"timestamp": "2025-01-15T10:30:00Z", "type": "open"}]
    lookback_days: int = 90
```

**Returns**:
```python
class EngagementPattern(BaseModel):
    preferred_days: list[int]      # [1, 2, 3] for Tue-Wed-Thu
    preferred_hours: list[int]     # [10, 11, 14] for 10-11 AM, 2-3 PM
    engagement_score: float       # 0.0 - 1.0
    sample_size: int              # Number of data points
    confidence: float             # Statistical confidence
    last_updated: datetime
```

**Implementation**:
- Group engagements by day of week and hour
- Apply exponential decay (recent data weighted more)
- Minimum 5 engagements for reliable pattern
- Calculate confidence based on sample size
- Store/update pattern in `engagement_patterns` table

### 4. `get_cohort_patterns`

**Purpose**: Retrieve cohort-based timing patterns for similar leads.

**Parameters**:
```python
class CohortPatternParams(BaseModel):
    industry: Optional[str]
    role: Optional[str]
    company_size: Optional[str]
    timezone: Optional[str]        # Group by timezone region
    min_sample_size: int = 50
```

**Returns**:
```python
class CohortPattern(BaseModel):
    cohort_id: str
    optimal_send_time: str        # "10:30 AM local time"
    optimal_day: int              # 2 for Wednesday
    engagement_rate: float        # Avg open rate for this cohort
    confidence_interval: tuple    # (lower_bound, upper_bound)
    sample_size: int
    last_updated: datetime
```

**Implementation**:
- Query `cohort_patterns` table for matching cohorts
- If no match, create ad-hoc cohort from recent data
- Use fuzzy matching for industry/role variations
- Consider timezone regions (EST, PST, GMT, etc.)
- Minimum 50 samples for statistically valid pattern

### 5. `schedule_ab_test`

**Purpose**: Set up A/B test for send time optimization.

**Parameters**:
```python
class ABTestParams(BaseModel):
    campaign_id: str
    cohort_id: Optional[str]
    variant_a_time: str          # "10:00 AM"
    variant_b_time: str          # "2:00 PM"
    sample_size: int = 100       # Per variant
    confidence_level: float = 0.95
    test_duration_days: int = 14
```

**Returns**:
```python
class ABTestSetup(BaseModel):
    test_id: str
    variant_a: dict              # {"time": "10:00", "lead_count": 50}
    variant_b: dict              # {"time": "2:00 PM", "lead_count": 50}
    start_date: datetime
    end_date: datetime
    status: Literal["setup", "running", "completed", "inconclusive"]
```

**Implementation**:
- Randomly assign leads to variants
- Ensure equal sample sizes
- Track opens, replies, and conversions
- Run chi-square test on completion
- Update cohort patterns if winner is significant

### 6. `calculate_optimal_send_time`

**Purpose**: Combine all data sources to determine optimal send time.

**Parameters**:
```python
class OptimalTimeParams(BaseModel):
    lead_id: str
    timezone: str
    business_hours: BusinessHoursResult
    individual_pattern: Optional[EngagementPattern]
    cohort_pattern: Optional[CohortPattern]
    campaign_id: str
    ab_test_variant: Optional[str]
```

**Returns**:
```python
class OptimalTimeResult(BaseModel):
    send_time_utc: datetime
    local_time_str: str          # "10:30 AM Tuesday, EST"
    confidence: float            # 0.0 - 1.0
    reasoning: str
    data_sources: list[str]
    next_optimization: datetime  # When to re-evaluate
```

**Implementation**:
1. If individual pattern exists and confidence >0.7 → use it
2. Else if cohort pattern exists → use it
3. Else use business hours with heuristics
4. Check for holidays and exceptions
5. Adjust for A/B test if participating
6. Return time in UTC for Instantly API

### 7. `schedule_with_instantly`

**Purpose**: Schedule the send with Instantly API at optimal time.

**Parameters**:
```python
class ScheduleParams(BaseModel):
    lead_ids: list[str]
    campaign_id: str
    send_time: datetime
    timezone: str
    ab_test_variant: Optional[str] = None
```

**Returns**:
```python
class ScheduleResult(BaseModel):
    scheduled_count: int
    failed_count: int
    instantly_response: dict
    scheduled_send_ids: list[str]
    errors: list[dict]
```

**Implementation**:
- Convert UTC time to Instantly's required format
- Include timezone in campaign variables
- Handle rate limiting (10 requests per second)
- Log scheduled sends to database
- Track A/B test assignments

## Database Schema

### Table: `lead_timezones`

```sql
CREATE TABLE lead_timezones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) UNIQUE,
    timezone VARCHAR(100) NOT NULL,
    confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    source VARCHAR(50) NOT NULL CHECK (source IN ('company_location', 'email_headers', 'ip_geolocation', 'memory', 'default')),
    utc_offset VARCHAR(10) NOT NULL, -- "+/-HH:MM"
    country_code VARCHAR(2),
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE, -- When lead confirmed timezone
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    INDEX idx_lead_id (lead_id),
    INDEX idx_timezone (timezone),
    INDEX idx_confidence (confidence),
    INDEX idx_updated_at (last_updated)
);
```

### Table: `engagement_patterns`

```sql
CREATE TABLE engagement_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) UNIQUE,

    -- Pattern data
    preferred_days INTEGER[], -- [1, 2, 3, 4] for Tue-Wed-Thu-Fri
    preferred_hours INTEGER[], -- [10, 11, 14, 15] for 10-11 AM, 2-3 PM
    engagement_score NUMERIC(3,2) CHECK (engagement_score >= 0 AND engagement_score <= 1),
    sample_size INTEGER NOT NULL DEFAULT 0,
    confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),

    -- Statistics
    avg_open_rate NUMERIC(5,2),
    avg_reply_rate NUMERIC(5,2),
    best_day INTEGER, -- Day of week with highest engagement
    best_hour INTEGER, -- Hour of day with highest engagement

    -- Metadata
    last_engagement_at TIMESTAMP WITH TIME ZONE,
    pattern_strength VARCHAR(20) CHECK (pattern_strength IN ('weak', 'moderate', 'strong', 'very_strong')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    INDEX idx_lead_id (lead_id),
    INDEX idx_confidence (confidence),
    INDEX idx_sample_size (sample_size),
    INDEX idx_strength (pattern_strength),
    INDEX idx_updated_at (updated_at)
);
```

### Table: `cohort_patterns`

```sql
CREATE TABLE cohort_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id VARCHAR(200) NOT NULL UNIQUE, -- e.g., "saas_cfo_50-100_est"

    -- Cohort definition
    industry VARCHAR(100),
    role VARCHAR(100),
    company_size VARCHAR(50),
    timezone_region VARCHAR(50), -- "EST", "PST", "GMT", etc.

    -- Optimal timing
    optimal_day INTEGER NOT NULL CHECK (optimal_day >= 0 AND optimal_day <= 6),
    optimal_hour INTEGER NOT NULL CHECK (optimal_hour >= 0 AND optimal_hour <= 23),
    optimal_window_start INTEGER, -- Start of optimal hour window
    optimal_window_end INTEGER,   -- End of optimal hour window

    -- Performance metrics
    avg_open_rate NUMERIC(5,2),
    avg_reply_rate NUMERIC(5,2),
    sample_size INTEGER NOT NULL DEFAULT 0,
    confidence_interval NUMERIC(4,2)[2], -- [lower, upper]

    -- Statistics
    chi_squared NUMERIC(10,2),
    p_value NUMERIC(10,4),
    significance VARCHAR(20) CHECK (significance IN ('significant', 'not_significant', 'insufficient_data')),

    -- Metadata
    last_calculated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() + INTERVAL '30 days'),
    calculation_period_days INTEGER DEFAULT 90,

    INDEX idx_cohort_id (cohort_id),
    INDEX idx_industry_role (industry, role),
    INDEX idx_company_size (company_size),
    INDEX idx_timezone_region (timezone_region),
    INDEX idx_sample_size (sample_size),
    INDEX idx_significance (significance),
    INDEX idx_valid_until (valid_until)
);
```

### Table: `send_time_optimization`

```sql
CREATE TABLE send_time_optimization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id VARCHAR(100) NOT NULL,
    batch_id UUID,

    -- Optimization details
    suggested_send_time TIMESTAMP WITH TIME ZONE NOT NULL,
    local_send_time VARCHAR(50) NOT NULL, -- "10:30 AM Tuesday, EST"
    timezone VARCHAR(100) NOT NULL,
    confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT NOT NULL,
    data_sources TEXT[] DEFAULT '{}', -- ["timezone", "individual", "cohort"]

    -- A/B testing
    ab_test_id UUID REFERENCES ab_tests(id),
    ab_test_variant VARCHAR(1) CHECK (ab_test_variant IN ('A', 'B')),

    -- Results
    actual_send_time TIMESTAMP WITH TIME ZONE,
    sent_status VARCHAR(20) CHECK (sent_status IN ('pending', 'sent', 'failed', 'cancelled')),

    -- Performance tracking
    opened_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,
    engagement_result VARCHAR(20) CHECK (engagement_result IN ('opened', 'replied', 'no_response')),

    -- Metadata
    optimization_level VARCHAR(20) CHECK (optimization_level IN ('basic', 'individual', 'cohort', 'full')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    INDEX idx_lead_id (lead_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_suggested_send_time (suggested_send_time),
    INDEX idx_confidence (confidence),
    INDEX idx_ab_test (ab_test_id, ab_test_variant),
    INDEX idx_sent_status (sent_status),
    INDEX idx_engagement_result (engagement_result),
    INDEX idx_created_at (created_at)
);
```

### Table: `ab_tests`

```sql
CREATE TABLE ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id VARCHAR(100) NOT NULL,
    cohort_id VARCHAR(200),

    -- Test configuration
    variant_a_time INTEGER NOT NULL, -- Hour in local time (0-23)
    variant_b_time INTEGER NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    hypothesis TEXT,

    -- Test execution
    status VARCHAR(20) CHECK (status IN ('setup', 'running', 'completed', 'inconclusive', 'cancelled')),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    min_sample_size INTEGER DEFAULT 100,

    -- Results
    variant_a_leads INTEGER DEFAULT 0,
    variant_b_leads INTEGER DEFAULT 0,
    variant_a_opens INTEGER DEFAULT 0,
    variant_b_opens INTEGER DEFAULT 0,
    variant_a_replies INTEGER DEFAULT 0,
    variant_b_replies INTEGER DEFAULT 0,

    -- Statistical analysis
    chi_squared NUMERIC(10,2),
    p_value NUMERIC(10,4),
    winner VARCHAR(1), -- 'A', 'B', or null
    confidence_level NUMERIC(3,2) DEFAULT 0.95,
    is_significant BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,

    INDEX idx_campaign_id (campaign_id),
    INDEX idx_cohort_id (cohort_id),
    INDEX idx_status (status),
    INDEX idx_start_date (start_date),
    INDEX idx_winner (winner)
);
```

## Integration: Timezone Detection APIs

### 1. OpenStreetMap Nominatim (Free)

```python
from src.integrations.base import BaseIntegrationClient

class NominatimClient(BaseIntegrationClient):
    """Client for OpenStreetMap Nominatim geocoding API."""

    def __init__(self):
        super().__init__(
            name="nominatim",
            base_url="https://nominatim.openstreetmap.org",
            api_key=None,  # No API key required
            timeout=10.0
        )

    async def geocode_location(self, location: str) -> dict:
        """Convert location string to coordinates and timezone."""
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        return await self.get("/search", params=params)
```

### 2. IPInfo.io (Optional, for IP-based detection)

```python
class IPInfoClient(BaseIntegrationClient):
    """Client for IPInfo.io geolocation API."""

    def __init__(self, api_key: str):
        super().__init__(
            name="ipinfo",
            base_url="https://ipinfo.io",
            api_key=api_key,
            timeout=5.0
        )

    async def get_timezone_from_ip(self, ip_address: str) -> dict:
        """Get timezone information from IP address."""
        return await self.get(f"/{ip_address}/json")
```

## Workflow

### Phase 1: Initial Optimization (Basic)

```python
async def optimize_send_times_basic(self, leads: list[LeadTimingData]) -> dict:
    """Basic timezone + business hours optimization."""

    results = []
    for lead in leads:
        # 1. Detect timezone
        timezone_result = await self.detect_timezone(
            lead_id=lead.lead_id,
            company_location=lead.company_location,
            email_headers=lead.email_headers
        )

        # 2. Get business hours
        business_hours = await self.get_business_hours(
            timezone=timezone_result.timezone,
            industry=lead.industry,
            role=lead.role,
            date=datetime.utcnow()
        )

        # 3. Calculate basic optimal time
        optimal_time = await self.calculate_optimal_send_time(
            lead_id=lead.lead_id,
            timezone=timezone_result.timezone,
            business_hours=business_hours,
            campaign_id=lead.campaign_id
        )

        results.append(optimal_time)

    return {"optimizations": results, "level": "basic"}
```

### Phase 2: Pattern-Based Optimization

```python
async def optimize_send_times_patterns(self, leads: list[LeadTimingData]) -> dict:
    """Individual and cohort pattern optimization."""

    results = []
    for lead in leads:
        # 1. Analyze individual engagement patterns
        if lead.previous_engagements:
            individual_pattern = await self.analyze_engagement_patterns(
                lead_id=lead.lead_id,
                engagement_history=lead.previous_engagements
            )
        else:
            individual_pattern = None

        # 2. Get cohort patterns
        cohort_pattern = await self.get_cohort_patterns(
            industry=lead.industry,
            role=lead.role,
            company_size=lead.company_size
        )

        # 3. Calculate with patterns
        optimal_time = await self.calculate_optimal_send_time(
            lead_id=lead.lead_id,
            timezone=timezone_result.timezone,
            business_hours=business_hours,
            individual_pattern=individual_pattern,
            cohort_pattern=cohort_pattern,
            campaign_id=lead.campaign_id
        )

        results.append(optimal_time)

    return {"optimizations": results, "level": "patterns"}
```

### Phase 3: A/B Test Execution

```python
async def run_ab_test(self, campaign_id: str, cohort_id: str) -> dict:
    """Set up and run A/B test for send times."""

    # 1. Create test setup
    test_setup = await self.schedule_ab_test(
        campaign_id=campaign_id,
        cohort_id=cohort_id,
        variant_a_time="10:00",
        variant_b_time="14:00"
    )

    # 2. Get leads for test
    test_leads = await self._get_test_leads(
        campaign_id=campaign_id,
        sample_size=test_setup.sample_size * 2
    )

    # 3. Assign variants and optimize
    for i, lead in enumerate(test_leads):
        variant = "A" if i < test_setup.sample_size else "B"
        lead.ab_test_variant = variant

    # 4. Process optimization with variants
    results = await self.optimize_send_times_patterns(test_leads)

    return {"test_id": test_setup.test_id, "results": results}
```

### Phase 4: Learning Loop (Weekly)

```python
async def update_patterns(self) -> dict:
    """Weekly update of cohort patterns based on performance."""

    # 1. Analyze recent send performance
    recent_sends = await self._get_recent_sends(days=7)

    # 2. Group by cohort and calculate new patterns
    cohort_updates = {}
    for send in recent_sends:
        cohort = self._get_cohort_for_lead(send.lead_id)
        if cohort not in cohort_updates:
            cohort_updates[cohort] = {"opens": 0, "sends": 0}

        cohort_updates[cohort]["sends"] += 1
        if send.engagement_result == "opened":
            cohort_updates[cohort]["opens"] += 1

    # 3. Update cohort_patterns table
    updates = []
    for cohort_id, metrics in cohort_updates.items():
        if metrics["sends"] >= 50:  # Minimum sample size
            await self._update_cohort_pattern(
                cohort_id=cohort_id,
                open_rate=metrics["opens"] / metrics["sends"]
            )
            updates.append(cohort_id)

    # 4. Check A/B test results
    completed_tests = await self._check_ab_test_results()

    return {
        "cohorts_updated": len(updates),
        "cohorts_list": updates,
        "ab_tests_completed": len(completed_tests)
    }
```

## Error Handling

### Input Validation Errors
- **Missing location/email headers**: Use default timezone, log warning
- **Invalid timezone**: Validate with pytz, fallback to UTC
- **Empty engagement history**: Proceed with basic optimization
- **Invalid datetime format**: Parse with dateutil, raise if fails

### Integration Errors
- **Geocoding API down**: Use cached timezone data, default to EST
- **Rate limit exceeded**: Exponential backoff, cache results longer
- **Invalid API key**: Critical error, alert ops, use fallback methods

### Data Quality Errors
- **Insufficient sample size**: Mark pattern as "weak", don't use
- **Contradictory data sources**: Use weighted averaging, log conflict
- **Stale patterns**: Update if >30 days old, or mark as expired

### Business Logic Errors
- **Sending outside business hours**: Re-calculate with constraints
- **Holiday conflicts**: Reschedule to next business day
- **Multiple optimal windows**: Choose earliest with highest confidence

## Testing Requirements

### Unit Tests (>90% coverage for tools)

```python
# test_detect_timezone.py
- Test successful timezone detection from city, country
- Test timezone detection from email headers
- Test IP geolocation fallback
- Test caching mechanism
- Test confidence scoring logic
- Test invalid location handling
- Test API failure fallbacks

# test_analyze_engagement_patterns.py
- Test pattern detection from sufficient data
- Test edge case: insufficient data (<5 engagements)
- Test time decay weighting (recent data)
- Test confidence calculation based on sample size
- Test pattern strength classification

# test_get_cohort_patterns.py
- Test exact cohort match retrieval
- Test fuzzy matching for similar industries
- Test minimum sample size enforcement
- Test confidence interval calculation
- Test cache invalidation

# test_calculate_optimal_send_time.py
- Test individual pattern priority over cohort
- Test business hour constraints
- Test holiday avoidance
- Test A/B test variant assignment
- Test timezone conversion accuracy

# test_schedule_with_instantly.py
- Test successful Instantly API scheduling
- Test rate limiting handling
- Test batch scheduling efficiency
- Test error recovery on API failures
```

### Integration Tests (>85% coverage for agent)

```python
# test_end_to_end_optimization.py
- Test full optimization workflow for new lead (basic)
- Test workflow for lead with engagement history (individual)
- Test workflow with cohort patterns available
- Test batch processing of 100 leads
- Test timezone edge cases (UTC+14, UTC-12)

# test_ab_testing_workflow.py
- Test A/B test setup and execution
- Test statistical significance calculation
- Test winner determination
- Test pattern updates from test results

# test_pattern_learning_loop.py
- Test weekly pattern updates
- Test cohort pattern recalculation
- Test A/B test result analysis
- Test pattern propagation to new optimizations
```

### Performance Tests

```python
# test_batch_processing.py
- Test processing 100 leads in <30 seconds
- Test memory usage stays under 100MB
- Test concurrent batch processing
- Test database query optimization

# test_api_rate_limits.py
- Test respectful API usage (geocoding)
- Test rate limit backoff implementation
- Test caching reduces API calls by >80%
```

## Performance Requirements

- **Single lead optimization**: <100ms (cache hit), <500ms (cache miss)
- **Batch processing (100 leads)**: <30 seconds total
- **Timezone detection**: <200ms average with caching
- **Pattern analysis**: <50ms for typical engagement history
- **A/B test analysis**: <2 seconds for 1000 samples
- **Database queries**: All queries indexed, <10ms average
- **Memory usage**: <200MB for batch of 500 leads
- **API calls**: <10 per 100 leads (with caching)

## Monitoring & Metrics

### Key Metrics

```python
# Optimization metrics
- optimization_success_rate: % of leads successfully optimized
- avg_confidence_score: Average confidence in suggested times
- pattern_usage_rate: % using individual vs. cohort vs. basic
- processing_time_per_lead: Average time to optimize

# Engagement metrics
- open_rate_by_timing: Open rates for different send times
- reply_rate_by_timing: Reply rates for different send times
- pattern_effectiveness: How well patterns predict engagement
- cohort_performance: Performance by industry/role cohorts

# A/B testing metrics
- ab_tests_running: Number of active tests
- statistical_significance_rate: % of tests with significant results
- test_completion_rate: % of tests that reach sample size
- pattern_update_frequency: How often patterns change

# Data quality metrics
- timezone_detection_accuracy: Verified correct timezones
- pattern_confidence_distribution: Breakdown by confidence levels
- data_freshness: Age of pattern data
- cache_hit_rate: % of requests served from cache
```

### Alerts

- **Critical**: Timezone detection failure rate >20%
- **High**: Average confidence score <0.5 for batch
- **Medium**: A/B test inconclusive rate >70%
- **Low**: Cache hit rate <60%

## Acceptance Criteria

- [ ] All timezone detections complete with >80% confidence
- [ ] Individual patterns created for leads with >5 engagements
- [ ] Cohort patterns maintained for all industry/role combinations with >50 samples
- [ ] A/B tests run automatically when sufficient sample size available
- [ ] Patterns updated weekly based on recent performance
- [ ] All sends respect business hours and avoid holidays
- [ ] Integration with Instantly API successfully schedules sends
- [ ] Processing time: <30 seconds for 100-lead batch
- [ ] Test coverage: >90% for tools, >85% for agent
- [ ] Monitoring dashboards show all key metrics
- [ ] Zero timezone-related send failures in production

## Dependencies

### Upstream
- **Lead List Builder Agent**: Provides company location and metadata
- **Campaign Creation Agent**: Triggers optimization for new campaigns
- **Email Engagement Tracking**: Provides open/reply data for pattern building
- **Instantly API**: For scheduling sends with optimal times

### Downstream
- **Campaign Send Agent**: Uses optimized send times for actual sending
- **Analytics Agent**: Consumes optimization performance data
- **Learning Feedback Loop Agent**: Updates AI models based on results

### External Services
- **OpenStreetMap Nominatim**: Free geocoding for timezone detection
- **IPInfo.io** (optional): IP-based geolocation fallback
- **Instantly API**: Campaign scheduling and sending
- **Holiday API** (optional): National holiday detection

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://...         # Supabase PostgreSQL
REDIS_URL=redis://localhost:6379/0    # Redis for caching
INSTANTLY_API_KEY=your-key-here       # Instantly API access

# Optional
IPINFO_API_KEY=your-key-here          # For IP geolocation
HOLIDAY_API_KEY=your-key-here         # For national holidays
TIMEZONE_CACHE_TTL=3600               # Cache duration in seconds
MIN_SAMPLE_SIZE=50                    # Minimum for cohort patterns
AB_TEST_MIN_SAMPLE=100                # Minimum per A/B test variant
```

## Implementation Checklist

### Phase 1: Foundation (Days 1-2)
- [ ] Create agent directory: `src/agents/campaign_send_time_optimization/`
- [ ] Implement `SendTimeOptimizationAgent` extending `BaseAgent`
- [ ] Define all Pydantic models for inputs/outputs
- [ ] Write comprehensive system prompt
- [ ] Create database migrations for all tables
- [ ] Apply migrations and verify schema

### Phase 2: Timezone Detection (Days 3-4)
- [ ] Implement `detect_timezone()` tool with multiple sources
- [ ] Create NominatimClient for geocoding
- [ ] Add IPInfoClient integration (optional)
- [ ] Implement timezone caching with Redis
- [ ] Write unit tests for all detection paths
- [ ] Verify timezone accuracy with test data

### Phase 3: Pattern Analysis (Days 5-6)
- [ ] Implement `analyze_engagement_patterns()` tool
- [ ] Implement `get_cohort_patterns()` tool
- [ ] Create pattern storage and retrieval logic
- [ ] Implement confidence scoring algorithms
- [ ] Add pattern strength classification
- [ ] Write tests for pattern analysis

### Phase 4: Optimization Logic (Days 7-8)
- [ ] Implement `get_business_hours()` with industry/role adjustments
- [ ] Implement `calculate_optimal_send_time()` combining all sources
- [ ] Add holiday detection and avoidance
- [ ] Implement priority logic (individual > cohort > basic)
- [ ] Add timezone conversion and validation
- [ ] Write comprehensive tests for optimization logic

### Phase 5: A/B Testing (Days 9-10)
- [ ] Implement `schedule_ab_test()` tool
- [ ] Create statistical analysis functions (chi-square)
- [ ] Implement test tracking and result calculation
- [ ] Add winner determination logic
- [ ] Create automatic pattern updates from results
- [ ] Write A/B test suite

### Phase 6: Instantly Integration (Day 11)
- [ ] Implement `schedule_with_instantly()` tool
- [ ] Handle rate limiting and API errors
- [ ] Add batch scheduling optimization
- [ ] Test with Instantly sandbox API
- [ ] Verify send time conversion accuracy

### Phase 7: Agent Workflow (Day 12)
- [ ] Implement `process_task()` with all phases
- [ ] Add batch processing logic
- [ ] Implement weekly learning loop task
- [ ] Add comprehensive logging and metrics
- [ ] Create optimization summary reports
- [ ] Write integration tests for full workflow

### Phase 8: Testing & QA (Days 13-14)
- [ ] Complete all unit tests (>90% coverage)
- [ ] Complete all integration tests (>85% coverage)
- [ ] Run performance tests and optimize
- [ ] Test with production-like data volumes
- [ ] Verify error handling for all failure modes
- [ ] Run full test suite (`make check`)

### Phase 9: Monitoring & Deployment (Day 15)
- [ ] Add monitoring metrics collection
- [ ] Set up alerts for critical metrics
- [ ] Create optimization dashboard
- [ ] Write deployment documentation
- [ ] Test in staging environment
- [ ] Prepare rollback procedures

## Future Enhancements (Not in MVP)

- [ ] Machine learning model for time prediction beyond simple patterns
- [ ] Real-time optimization based on immediate engagement signals
- [ ] Multi-timezone support for distributed teams
- [ ] Cultural business norm adjustments by country
- [ ] Seasonal pattern recognition (holidays, summer slowdowns)
- [ ] Integration with sales engagement platforms (Outreach, SalesLoft)
- [ ] Predictive analytics for optimal send frequency
- [ ] Automated experiment design for timing optimization

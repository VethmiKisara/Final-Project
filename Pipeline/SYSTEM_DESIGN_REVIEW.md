# Real-Time Multimodal Disaster Detection Pipeline - System Design Review

**Project:** Real-Time Multimodal Disaster Detection Using Social Media  
**Review Date:** January 26, 2026  
**Scope:** Real-time data processing pipeline + Misinformation filtering module  
**Status:** REQUIRES SIGNIFICANT CORRECTIONS

---

## EXECUTIVE SUMMARY

**CRITICAL FINDINGS:**
- ❌ **Pipeline is NOT real-time** (batch processing of 100 pre-loaded rows)
- ❌ **Credibility filtering is BYPASSED** (only affects post-processing labels, not upstream flow)
- ❌ **No incremental/streaming ingestion** (entire dataset loads into DataFrame)
- ⚠️ **Filtering logic is inconsistent** (multiple implementations, unclear enforcement)
- ⚠️ **No enforced misinformation gating** (low-credibility posts NOT removed before downstream)

---

## COMPONENT-BY-COMPONENT ANALYSIS

### 1. DATA INGESTION LAYER
**Classification: ❌ INCORRECT**

#### Issues:
- **Line 85-99 (Cell 10):** Batch loading via `pd.read_csv()` → entire dataset into memory
- **Line 435-452 (Cell 21):** Re-loads full TSV file (batch)
- **No streaming mechanism:** No generators, queues, async loops, or polling
- **No incremental processing:** All rows fetched before any processing begins

#### Evidence:
```python
train_df = pd.read_csv(train_path, sep='\t')  # Batch load entire dataset
```

#### Requirement Violation:
- ✗ "No full-dataset loading into memory"
- ✗ "Incremental processing of incoming data"
- ✗ "Evidence of near real-time behavior (streaming loop, generator, queue)"

---

### 2. TEXT PREPROCESSING MODULE
**Classification: ✓ CORRECT**

#### What Works:
- Proper URL/mention/hashtag removal (Line 102-120)
- Stopword filtering via NLTK
- Consistent cleaning via `clean_text()` function
- Applied before credibility evaluation

#### Minor Issue:
- Preprocessing happens uniformly; no streaming optimization for large volumes

---

### 3. CREDIBILITY FILTERING MODULE
**Classification: ❌ INCORRECT (Critical Design Flaw)**

#### Problem 1: Multiple Conflicting Implementations
The notebook contains **THREE different credibility scoring functions**:

1. **Line 130-146 (Cell 12):** `basic_credibility_score()` - Simple heuristic
   ```python
   score -= 0.35 if 'fake' in text else...
   ```

2. **Line 183-213 (Cell 15):** `improved_credibility_score()` - Heuristic v2
   ```python
   score = 1.0; score -= 0.5 if 'fake' in text...
   ```

3. **Line 216-246 (Cell 16):** `get_credibility_score()` - RoBERTa model (never called in final pipeline)
   ```python
   cred_pipe = pipeline("text-classification", model="roberta-base-openai-detector")
   ```

#### Problem 2: **THRESHOLD NOT ENFORCED**
- **Line 249-255 (Cell 17):** Mentions "Likely Real if score > 0.6" but **does NOT filter**
- **Line 298-321 (Cell 19):** Full pipeline returns credibility score but **processes ALL posts regardless**
- **Line 356-390 (Cell 21):** `member4_pipeline()` function computes score but makes no filtering decision
- **Line 593-610 (Cell 31):** Final pipeline uses credibility only for labeling, **not filtering**

#### Problem 3: **Low-Credibility Posts NOT Removed**
```python
# Line 356-390: Pipeline returns credibility but continues processing ALL posts
def member4_pipeline(post):
    cred = get_credibility_score(processed['cleaned_text'])  # ← Score computed
    # ... but then continues with ALL posts regardless of cred value
    informative = "informative" if cred > 0.6 else "not_informative"
    # ← Only LABELS posts as "not_informative", does NOT FILTER/REMOVE them
    return {..., "credibility_score": cred}  # ← Returns all posts
```

**What Should Happen:**
```python
# CORRECT (not currently implemented):
if cred < THRESHOLD:
    return None  # or filter_queue.put(post) for logging
    # Do NOT continue processing this post
# else:
#     continue to next stage
```

#### Problem 4: Inconsistent Thresholds
- No single, clearly defined threshold across the pipeline
- Different functions use different criteria
- RoBERTa model loads but is **never actually used** in execution flow

#### Requirement Violations:
- ✗ "A social media post must be discarded if its credibility score falls below a defined threshold"
- ✗ "Low-credibility posts must not continue through the pipeline"
- ✗ "Low-credibility posts must not be emitted as valid events"
- ✗ "The filtering logic prevents misinformation from influencing later stages"

---

### 4. LOCATION EXTRACTION & GEOCODING
**Classification: ✓ PARTIALLY CORRECT**

#### What Works:
- Named Entity Recognition via spaCy (Line 324-353)
- Mock GDIS dictionary lookup (reasonable placeholder)
- Extracts location before downstream processing

#### Issues:
- Only returns first detected location (no multi-location support)
- Mock GDIS is hardcoded (acceptable for scope, but noted)

---

### 5. DISASTER TYPE CLASSIFICATION
**Classification: ⚠️ PARTIALLY CORRECT**

#### Current Implementation (Line 356-390):
```python
disaster_type = "flood" if "flood" in processed['cleaned_text'] else "unknown"
```
- Simple keyword matching, not ML-based
- Acceptable as placeholder, but noted as not production-ready
- Correctly positioned after credibility (though credibility doesn't filter)

---

### 6. OUTPUT EMISSION
**Classification: ❌ INCORRECT**

#### Issues:
- Returns ALL posts regardless of credibility (Line 414-432, Line 613-644)
- No distinction between "valid events" and "filtered low-credibility" outputs
- No event-driven emission (no streaming, events, or queues)
- Batch results collection (line 493-520: `for idx, row in train_df.iloc[:100]`)

#### What's Missing:
- Filter queue for rejected posts (for logging/analytics)
- Valid event stream separate from rejected stream
- Real-time emission callbacks/hooks

---

### 7. END-TO-END PIPELINE EXECUTION ORDER
**Classification: ❌ INCORRECT**

Current (Broken) Order:
```
1. Load entire dataset (batch) ←― NOT REAL-TIME
2. Preprocess text ✓
3. Compute credibility score ✓
4. Extract location ✓
5. Classify disaster type ✓
6. EMIT ALL POSTS (including low-credibility) ←― WRONG! Should filter here
```

Required Order (SDS):
```
1. Ingest social media data (stream/async/polling) ←― Currently: Batch load
2. Perform basic preprocessing ✓
3. Apply credibility filtering ←― Currently: Computed but NOT applied
4. Forward ONLY CREDIBLE posts ←― Currently: ALL posts forwarded
5. Emit processed outputs ✓
```

---

## SPECIFIC CODE VIOLATIONS

| Line/Cell | Issue | Severity |
|-----------|-------|----------|
| 85-99 | Batch `pd.read_csv()` loads entire dataset | CRITICAL |
| 102-120 | Preprocessing ✓ (correct) | — |
| 130-146 | First credibility implementation (unused) | Medium |
| 183-213 | Second credibility implementation (unused) | Medium |
| 216-246 | Third credibility impl (RoBERTa, never called) | Medium |
| 249-255 | Prints "Likely Real if score > 0.6" but does NOT filter | CRITICAL |
| 298-321 | `member4_pipeline()` computes score but processes ALL posts | CRITICAL |
| 356-390 | Full pipeline continues with ALL posts regardless of credibility | CRITICAL |
| 414-432 | Returns tracking info for ALL posts (no credibility gate) | CRITICAL |
| 493-520 | Batch processing loop: `for idx in [:100]` | CRITICAL |
| 593-610 | Final pipeline uses credibility only for LABELING, not FILTERING | CRITICAL |

---

## DESIGN VIOLATIONS SUMMARY

### Real-Time Processing Violations
| Requirement | Status | Evidence |
|---|---|---|
| Incremental processing | ✗ FAIL | Batch `pd.read_csv()` loads all rows |
| No full-dataset loading | ✗ FAIL | `train_df = pd.read_csv(...)` in memory |
| No blocking in ingestion | ✗ FAIL | Entire dataset fetched before processing |
| Streaming/async mechanism | ✗ FAIL | No generators, queues, or async loops |
| Near real-time evidence | ✗ FAIL | Batch processing loop `[:100]` |

### Misinformation Filtering Violations
| Requirement | Status | Evidence |
|---|---|---|
| Posts discarded if credibility < threshold | ✗ FAIL | Scores computed but all posts continue |
| Low-cred posts must NOT continue | ✗ FAIL | `member4_pipeline()` processes all |
| Low-cred posts must NOT be emitted | ✗ FAIL | All posts returned by pipeline |
| Filtering prevents misinformation influence | ✗ FAIL | Low-cred posts passed to next stage |
| Clearly defined threshold | ⚠️ PARTIAL | Multiple thresholds (0.6, 0.2, etc.), none enforced |

---

## RECOMMENDATIONS

### IMMEDIATE FIXES (Critical Path)

#### Fix 1: Implement Enforced Credibility Gate (HIGHEST PRIORITY)
**Lines 356-390 and 593-610 → Replace with:**

```python
CREDIBILITY_THRESHOLD = 0.6

def member4_pipeline(post, row_index):
    """Process post only if it passes credibility check."""
    try:
        processed = full_preprocess(post)
        cred_score = get_credibility_score(processed['cleaned_text'])
        
        # ← ENFORCED CREDIBILITY GATE (NEW)
        if cred_score < CREDIBILITY_THRESHOLD:
            train_df.at[row_index, 'filtered_reason'] = 'low_credibility'
            train_df.at[row_index, 'credibility_score'] = cred_score
            train_df.at[row_index, 'processed_success'] = False
            return {
                "success": False,
                "filtered": True,
                "credibility": cred_score,
                "reason": "credibility_below_threshold"
            }
        # ← END GATE
        
        # Only continue if credible
        loc_name = extract_location(processed['cleaned_text'])
        gdis = mock_gdis_match(loc_name)
        disaster_type = classify_disaster_type(processed['cleaned_text'])
        
        train_df.at[row_index, 'processed_success'] = True
        train_df.at[row_index, 'credibility_score'] = cred_score
        train_df.at[row_index, 'processing_error'] = None
        
        return {
            "success": True,
            "filtered": False,
            "credibility_score": cred_score,
            "cleaned_text": processed['cleaned_text'][:150],
            "location": loc_name,
            "disaster_type": disaster_type,
            "lat": gdis['lat'],
            "lon": gdis['lon']
        }
    except Exception as e:
        train_df.at[row_index, 'processed_success'] = False
        train_df.at[row_index, 'processing_error'] = str(e)
        return {"success": False, "error": str(e)}
```

#### Fix 2: Replace Batch Processing with Streaming Simulation
**Lines 493-520 → Replace with:**

```python
import queue
import time

# Simulate real-time stream
credible_queue = queue.Queue()
rejected_queue = queue.Queue()

def streaming_processor(data_source, batch_size=10):
    """Process posts incrementally (simulates real-time stream)."""
    total_rows = len(data_source)
    
    for idx in range(0, total_rows, 1):  # Process one at a time (not batch)
        post = data_source.iloc[idx].to_dict()
        result = member4_pipeline(post, idx)
        
        # Route to appropriate queue
        if result.get("filtered"):
            rejected_queue.put({
                "index": idx,
                "reason": result.get("reason"),
                "credibility": result.get("credibility")
            })
        elif result.get("success"):
            credible_queue.put({
                "index": idx,
                **result
            })
        
        time.sleep(0.1)  # Simulate 100ms ingestion delay (real-time)
    
    return {
        "credible_posts": credible_queue.qsize(),
        "filtered_posts": rejected_queue.qsize()
    }

# Process first 100 (or all)
stats = streaming_processor(train_df.iloc[:100], batch_size=1)
print(f"Results: {stats['credible_posts']} credible, {stats['filtered_posts']} rejected")
```

#### Fix 3: Consolidate Single Credibility Function
**Delete Lines 130-146, 183-213 and choose ONE implementation:**

Option A (Recommended): Use RoBERTa (Line 216-246) — most robust
```python
CREDIBILITY_THRESHOLD = 0.6
# Use get_credibility_score() from Line 216-246
```

Option B: If GPU unavailable, use improved heuristic (Line 183-213)
```python
CREDIBILITY_THRESHOLD = 0.6
# Use improved_credibility_score() with clear threshold
```

**Document the choice:**
```python
"""
CREDIBILITY FILTERING CONFIGURATION
------------------------------------
Model: RoBERTa base OpenAI detector
Threshold: 0.6 (posts < 0.6 score are rejected)
Application: ENFORCED GATE before location/classification stages
Posts below threshold are emitted to rejection queue for logging/analysis
"""
```

#### Fix 4: Add Output Separation
**Lines 414-432 → Add credibility-aware output:**

```python
def emit_processed_outputs(credible_queue, rejected_queue, output_mode='both'):
    """Emit outputs with clear separation of credible vs rejected."""
    
    credible_events = []
    while not credible_queue.empty():
        credible_events.append(credible_queue.get())
    
    rejected_events = []
    while not rejected_queue.empty():
        rejected_events.append(rejected_queue.get())
    
    if output_mode in ['both', 'credible']:
        print(f"\n=== VALID EVENTS ({len(credible_events)}) ===")
        for event in credible_events:
            print(f"✓ Credibility {event['credibility_score']}: {event['cleaned_text'][:80]}")
    
    if output_mode in ['both', 'rejected']:
        print(f"\n=== REJECTED POSTS ({len(rejected_events)}) ===")
        for event in rejected_events:
            print(f"✗ {event['reason']}: Cred={event['credibility']}")
    
    return {
        "valid": credible_events,
        "rejected": rejected_events,
        "total_processed": len(credible_events) + len(rejected_events)
    }
```

---

### SECONDARY IMPROVEMENTS (Best Practice)

#### Improvement 1: Define Config Object
```python
class PipelineConfig:
    """Configuration for real-time disaster detection pipeline."""
    CREDIBILITY_THRESHOLD = 0.6
    STREAMING_DELAY_MS = 100  # Simulated real-time delay
    BATCH_SIZE = 1  # Process one post at a time (not batch)
    LOCATION_MODEL = "spacy_en_core_web_sm"
    CREDIBILITY_MODEL = "roberta-base-openai-detector"
    MAX_RETRIES = 3
```

#### Improvement 2: Add Pipeline Metrics
```python
class PipelineMetrics:
    def __init__(self):
        self.posts_ingested = 0
        self.posts_filtered = 0
        self.posts_processed = 0
        self.processing_errors = 0
    
    def report(self):
        total = self.posts_ingested
        return {
            "ingested": self.posts_ingested,
            "filtered": self.posts_filtered,
            "passed": self.posts_processed,
            "errors": self.processing_errors,
            "filter_rate": f"{self.posts_filtered/total*100:.1f}%"
        }
```

#### Improvement 3: Async Pipeline (Advanced)
```python
import asyncio

async def async_streaming_pipeline(post_generator):
    """Truly async streaming pipeline."""
    async for post in post_generator:
        # Preprocess
        processed = full_preprocess(post)
        
        # Credibility gate
        if get_credibility_score(processed['cleaned_text']) < THRESHOLD:
            await emit_filtered(post)
            continue
        
        # Process credible post
        await emit_credible(post)
```

---

## TESTING RECOMMENDATIONS

Before final submission, add tests:

```python
def test_credibility_filtering():
    """Verify low-credibility posts are actually filtered."""
    
    # Create fake posts
    high_cred_post = {"tweet_text": "Urgent: evacuate Negombo area now"}
    low_cred_post = {"tweet_text": "This earthquake hoax is a prank! lol"}
    
    result_high = member4_pipeline(high_cred_post, 0)
    result_low = member4_pipeline(low_cred_post, 1)
    
    # Test assertions
    assert result_high['success'] == True, "High-credibility post should pass"
    assert result_low['filtered'] == True, "Low-credibility post MUST be filtered"
    assert result_high['credibility_score'] > THRESHOLD
    assert result_low['credibility_score'] < THRESHOLD

def test_incremental_processing():
    """Verify posts are processed one at a time (not batch)."""
    # Check that streaming_processor yields control between posts
    # (Add timing assertions)

def test_no_credible_bypass():
    """Verify filtering gate CANNOT be bypassed."""
    # Confirm NO path through pipeline skips credibility check
```

---

## CURRENT vs REQUIRED STATE

| Aspect | Current | Required | Status |
|--------|---------|----------|--------|
| Ingestion | Batch load all rows | Stream/async/polling | ❌ |
| Credibility Check | Computed but not applied | Applied as enforced gate | ❌ |
| Post Filtering | All posts continue | Only credible continue | ❌ |
| Output Emission | Single stream (all posts) | Separate valid/rejected streams | ❌ |
| Threshold Definition | Multiple, unclear | Single, enforced (0.6 suggested) | ❌ |
| Preprocessing | Before credibility | Before credibility | ✓ |
| Location Extraction | After preprocessing | After credibility gate | ⚠️ (minor) |
| Error Handling | Present | Present | ✓ |

---

## CONCLUSION

**Current Assessment: DOES NOT MEET SDS REQUIREMENTS**

The pipeline currently implements:
- ✓ Preprocessing (correct)
- ✗ Real-time ingestion (batch)
- ✗ Enforced credibility filtering (computed but not applied)
- ✗ Misinformation gating (posts not filtered)
- ✗ Modular streaming flow (monolithic batch loop)

**Required Actions:**
1. Replace batch loading with streaming simulation (CRITICAL)
2. Implement enforced credibility filtering gate (CRITICAL)
3. Separate output streams for credible vs rejected (HIGH)
4. Consolidate multiple credibility functions (MEDIUM)
5. Add test cases to verify filtering enforcement (MEDIUM)

**Estimated Effort:** 4-6 hours for complete fixes  
**Impact:** Changes turn a batch preprocessing script into a proper real-time filtered pipeline

---


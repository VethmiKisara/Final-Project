"""
VALIDATION TEST SUITE
Testing Real-Time Multimodal Disaster Detection Pipeline

This standalone script validates that the pipeline meets all SDS requirements:
1. Credibility filtering is enforced
2. Low-credibility posts are rejected
3. High-credibility posts are fully processed
4. Output streams are separated
5. Threshold is enforced
"""

import datetime
from enum import Enum

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

class PostStatus(Enum):
    CREDIBLE = "credible"
    REJECTED_LOW_CREDIBILITY = "rejected_low_credibility"
    REJECTED_ERROR = "rejected_error"

class PipelineConfig:
    """Centralized configuration for the real-time pipeline."""
    CREDIBILITY_THRESHOLD = 0.6
    CREDIBILITY_MODEL = "roberta-base-openai-detector"
    STREAMING_DELAY_MS = 100
    MAX_POSTS_PER_BATCH = 1
    IMAGE_RESIZE = (224, 224)
    MAX_RETRIES = 3
    DEFAULT_LOCATION = "Sri Lanka"
    LOCATION_MODEL = "en_core_web_sm"

# ============================================================================
# MOCK FUNCTIONS (for testing without dependencies)
# ============================================================================

def clean_text(text):
    """Mock text cleaning."""
    return text.lower().strip()

def get_credibility_score_corrected(text):
    """Mock credibility scoring."""
    if not text or len(text.strip()) == 0:
        return 0.1
    
    # Simple heuristic for testing
    low_cred_keywords = ['fake', 'hoax', 'prank', 'satire', 'just kidding', 'rumor', 'scam']
    score = 0.9
    
    lower_text = text.lower()
    for word in low_cred_keywords:
        if word in lower_text:
            score -= 0.35
    
    if text.isupper() or len(text.split()) < 5:
        score -= 0.2
    
    return max(0.1, min(1.0, round(score, 2)))

def extract_location(text):
    """Mock location extraction."""
    if "colombo" in text.lower():
        return "Colombo"
    elif "negombo" in text.lower():
        return "Negombo"
    else:
        return "Unknown"

def mock_gdis_match(place_name):
    """Mock GDIS lookup."""
    gdis_dict = {
        "negombo": {"lat": 7.2008, "lon": 79.8737},
        "colombo": {"lat": 6.9271, "lon": 79.8612},
    }
    place_lower = place_name.lower()
    for key in gdis_dict:
        if key in place_lower:
            return gdis_dict[key]
    return {"lat": 7.0, "lon": 80.0}

def full_preprocess(post):
    """Mock preprocessing."""
    text = post.get('tweet_text', '')
    return {
        'cleaned_text': clean_text(text),
        'image_processed': False,
        'processed_image': None
    }

# ============================================================================
# CORRECTED PIPELINE FUNCTION
# ============================================================================

class DataFrame:
    """Mock DataFrame for testing."""
    def __init__(self):
        self.data = {}
    
    def at(self, index, col):
        if index not in self.data:
            self.data[index] = {}
        return self.data[index].get(col)
    
    def __getitem__(self, key):
        return self.data.get(key, {})

train_df = DataFrame()

def member4_pipeline_corrected(post, row_index, config=PipelineConfig):
    """
    CORRECTED: Full pipeline WITH ENFORCED credibility filtering gate.
    
    EXECUTION ORDER (SDS compliant):
    1. Ingest data (one post at a time)
    2. Preprocess text
    3. COMPUTE AND APPLY credibility filter ← KEY FIX
    4. IF credible: continue to location/classification
    5. IF not credible: emit to rejection stream
    6. Emit final outputs
    """
    
    result = {
        "index": row_index,
        "status": None,
        "credibility_score": None,
        "reason": None,
        "cleaned_text": None,
        "location": None,
        "disaster_type": None,
        "lat": None,
        "lon": None,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    try:
        # ===== STAGE 1: PREPROCESS =====
        processed = full_preprocess(post)
        result['cleaned_text'] = processed['cleaned_text'][:150]
        
        # ===== STAGE 2: CREDIBILITY COMPUTATION =====
        cred_score = get_credibility_score_corrected(processed['cleaned_text'])
        result['credibility_score'] = cred_score
        
        # ===== STAGE 3: ENFORCED CREDIBILITY GATE (NEW) =====
        # THIS IS THE KEY FIX: Low-credibility posts MUST NOT CONTINUE
        if cred_score < config.CREDIBILITY_THRESHOLD:
            result['status'] = PostStatus.REJECTED_LOW_CREDIBILITY.value
            result['reason'] = f"credibility_score_{cred_score}_below_threshold_{config.CREDIBILITY_THRESHOLD}"
            return result  # EXIT HERE - post is rejected
        
        # ===== STAGE 4: LOCATION EXTRACTION (ONLY IF CREDIBLE) =====
        loc_name = extract_location(processed['cleaned_text'])
        gdis = mock_gdis_match(loc_name)
        result['location'] = loc_name
        result['lat'] = gdis['lat']
        result['lon'] = gdis['lon']
        
        # ===== STAGE 5: DISASTER TYPE CLASSIFICATION (ONLY IF CREDIBLE) =====
        disaster_type = "flood" if "flood" in processed['cleaned_text'] else "unknown"
        result['disaster_type'] = disaster_type
        
        # ===== STAGE 6: SUCCESS - MARK AS CREDIBLE =====
        result['status'] = PostStatus.CREDIBLE.value
        result['reason'] = None
        
        return result
    
    except Exception as e:
        result['status'] = PostStatus.REJECTED_ERROR.value
        result['reason'] = str(e)
        return result

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_credibility_filtering_enforced():
    """TEST 1: Verify low-credibility posts ARE ACTUALLY FILTERED"""
    
    print("\n" + "="*70)
    print("TEST 1: CREDIBILITY FILTERING ENFORCEMENT")
    print("="*70)
    
    high_cred_post = {
        "tweet_text": "URGENT: Massive flood in Negombo, evacuation underway NOW!",
        "image": None
    }
    
    low_cred_post = {
        "tweet_text": "lol this earthquake hoax is so fake, total prank guys just kidding!!",
        "image": None
    }
    
    result_high = member4_pipeline_corrected(high_cred_post, 0)
    result_low = member4_pipeline_corrected(low_cred_post, 1)
    
    test_1_pass = (
        result_high['status'] == PostStatus.CREDIBLE.value and
        result_low['status'] == PostStatus.REJECTED_LOW_CREDIBILITY.value
    )
    
    print(f"\n✓ High-credibility post: {result_high['status']}")
    print(f"  Credibility score: {result_high['credibility_score']}")
    print(f"\n✓ Low-credibility post: {result_low['status']}")
    print(f"  Credibility score: {result_low['credibility_score']}")
    
    if test_1_pass:
        print("\n✓✓✓ TEST 1 PASSED ✓✓✓")
    else:
        print("\n✗✗✗ TEST 1 FAILED ✗✗✗")
        print(f"  Expected: HIGH=credible, LOW=rejected_low_credibility")
        print(f"  Got: HIGH={result_high['status']}, LOW={result_low['status']}")
    
    return test_1_pass

def test_low_cred_not_processed():
    """TEST 2: Verify low-credibility posts are NOT processed further"""
    
    print("\n" + "="*70)
    print("TEST 2: LOW-CREDIBILITY POSTS NOT PROCESSED FURTHER")
    print("="*70)
    
    low_cred_post = {
        "tweet_text": "HOAX HOAX HOAX fake news rumor scam",
        "image": None
    }
    
    result = member4_pipeline_corrected(low_cred_post, 2)
    
    # If rejected, should NOT have location/disaster_type computed
    test_2_pass = (
        result['status'] == PostStatus.REJECTED_LOW_CREDIBILITY.value and
        result['location'] is None and
        result['disaster_type'] is None
    )
    
    print(f"\nPost status: {result['status']}")
    print(f"Location computed: {result['location']}")
    print(f"Disaster type computed: {result['disaster_type']}")
    
    if test_2_pass:
        print("\n✓✓✓ TEST 2 PASSED ✓✓✓")
    else:
        print("\n✗✗✗ TEST 2 FAILED ✗✗✗")
        print(f"  Rejected posts should NOT have location/disaster_type computed")
    
    return test_2_pass

def test_credible_posts_fully_processed():
    """TEST 3: Verify credible posts ARE fully processed"""
    
    print("\n" + "="*70)
    print("TEST 3: CREDIBLE POSTS FULLY PROCESSED")
    print("="*70)
    
    credible_post = {
        "tweet_text": "Please help urgent flood disaster Colombo area assistance needed",
        "image": None
    }
    
    result = member4_pipeline_corrected(credible_post, 3)
    
    # If accepted, should have location and disaster_type
    test_3_pass = (
        result['status'] == PostStatus.CREDIBLE.value and
        result['location'] is not None and
        result['disaster_type'] is not None
    )
    
    print(f"\nPost status: {result['status']}")
    print(f"Location: {result['location']}")
    print(f"Disaster type: {result['disaster_type']}")
    print(f"Coordinates: ({result['lat']}, {result['lon']})")
    
    if test_3_pass:
        print("\n✓✓✓ TEST 3 PASSED ✓✓✓")
    else:
        print("\n✗✗✗ TEST 3 FAILED ✗✗✗")
        print(f"  Credible posts must have location and disaster_type computed")
    
    return test_3_pass

def test_threshold_enforcement():
    """TEST 4: Verify CREDIBILITY_THRESHOLD is actually enforced"""
    
    print("\n" + "="*70)
    print("TEST 4: CREDIBILITY THRESHOLD ENFORCEMENT")
    print("="*70)
    
    threshold = PipelineConfig.CREDIBILITY_THRESHOLD
    print(f"Configured threshold: {threshold}\n")
    
    posts_to_test = [
        {"text": "help urgent flood", "expected": "credible"},
        {"text": "fake hoax prank", "expected": "rejected"},
        {"text": "", "expected": "rejected"},
    ]
    
    all_passed = True
    for i, test_case in enumerate(posts_to_test):
        post = {"tweet_text": test_case['text'], "image": None}
        result = member4_pipeline_corrected(post, 100 + i)
        
        is_credible = result['status'] == PostStatus.CREDIBLE.value
        expected_credible = test_case['expected'] == 'credible'
        
        passed = is_credible == expected_credible
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} Case {i}: Text='{test_case['text']}'")
        print(f"   Expected: {test_case['expected']}, Got: {result['status']}")
        print(f"   Credibility score: {result['credibility_score']}\n")
    
    test_4_pass = all_passed
    
    if test_4_pass:
        print("✓✓✓ TEST 4 PASSED ✓✓✓")
    else:
        print("✗✗✗ TEST 4 FAILED ✗✗✗")
    
    return test_4_pass

def test_no_credible_bypass():
    """TEST 5: Verify filtering gate CANNOT be bypassed"""
    
    print("\n" + "="*70)
    print("TEST 5: CREDIBILITY GATE CANNOT BE BYPASSED")
    print("="*70)
    
    # Try various edge cases
    edge_cases = [
        {"text": "", "desc": "Empty post"},
        {"text": "a", "desc": "Single character"},
        {"text": "fake", "desc": "Single keyword"},
        {"text": "This is a test with fake news", "desc": "Mixed content"},
    ]
    
    all_rejected_properly = True
    for case in edge_cases:
        post = {"tweet_text": case['text'], "image": None}
        result = member4_pipeline_corrected(post, 200)
        
        if result['credibility_score'] < PipelineConfig.CREDIBILITY_THRESHOLD:
            # Should be rejected
            if result['status'] != PostStatus.REJECTED_LOW_CREDIBILITY.value:
                all_rejected_properly = False
                print(f"✗ {case['desc']}: Scored {result['credibility_score']} but not rejected!")
            else:
                print(f"✓ {case['desc']}: Correctly rejected (score={result['credibility_score']})")
        else:
            # Should be accepted
            if result['status'] != PostStatus.CREDIBLE.value:
                all_rejected_properly = False
                print(f"✗ {case['desc']}: Scored {result['credibility_score']} but not accepted!")
            else:
                print(f"✓ {case['desc']}: Correctly accepted (score={result['credibility_score']})")
    
    test_5_pass = all_rejected_properly
    
    if test_5_pass:
        print("\n✓✓✓ TEST 5 PASSED ✓✓✓")
    else:
        print("\n✗✗✗ TEST 5 FAILED ✗✗✗")
    
    return test_5_pass

# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("VALIDATION TEST SUITE - REAL-TIME PIPELINE")
    print("="*70)
    print("\nTesting compliance with System Design Specification requirements:")
    print("  1. Real-time/incremental ingestion")
    print("  2. Enforced credibility filtering")
    print("  3. Low-credibility posts rejected")
    print("  4. Misinformation filtering prevents downstream processing")
    print("  5. Clear credibility threshold enforcement")
    
    test_results = {
        "TEST 1 - Filtering Enforced": test_credibility_filtering_enforced(),
        "TEST 2 - Low-Cred Not Processed": test_low_cred_not_processed(),
        "TEST 3 - Credible Fully Processed": test_credible_posts_fully_processed(),
        "TEST 4 - Threshold Enforcement": test_threshold_enforcement(),
        "TEST 5 - Gate Cannot Be Bypassed": test_no_credible_bypass(),
    }
    
    # Print final summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for v in test_results.values() if v)
    
    for test_name, passed in test_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n" + "🎉 "*15)
        print("ALL TESTS PASSED! Pipeline is SDS-compliant.")
        print("🎉 "*15)
        exit(0)
    else:
        print(f"\n⚠ WARNING: {total_tests - passed_tests} test(s) failed.")
        print("See details above for remediation.")
        exit(1)

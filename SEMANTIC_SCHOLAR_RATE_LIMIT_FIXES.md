# Semantic Scholar API Rate Limit Fixes

## Problem
The Semantic Scholar API was returning 429 errors (rate limited) because:
1. Only 0.5 second delay between requests (120 requests/minute)
2. No retry mechanism for rate limits
3. Semantic Scholar free tier limit is ~100 requests/minute

## Solutions Implemented

### 1. Increased Delay
- Changed from 0.5 seconds to 1.0 second between requests
- This ensures max 60 requests/minute, staying within limits

### 2. Added Rate Limiting Logic
```python
# Track last request time
self.last_request_time = 0

# Wait if needed before making request
current_time = time.time()
time_since_last = current_time - self.last_request_time
if time_since_last < self.rate_limit_delay:
    time.sleep(self.rate_limit_delay - time_since_last)
```

### 3. Exponential Backoff Retry
- Added retry mechanism with exponential backoff
- Wait times: 5s, 10s, 20s for retries
- Max 3 retries before giving up

### 4. Better Error Handling
- Clear error messages for rate limit issues
- Graceful fallback when rate limit is hit
- Informative user feedback

## Current Rate Limits
- **Free Tier**: ~100 requests/minute
- **Our Implementation**: 60 requests/minute (1 second delay)
- **Safety Margin**: 40 requests/minute buffer

## Usage Tips
1. Don't run multiple searches simultaneously
2. Wait between batch searches
3. If rate limited, wait at least 1 minute before retrying
4. Consider using fewer keywords to reduce API calls

## Future Improvements
1. Add API key for higher limits (if available)
2. Cache results to avoid repeated requests
3. Implement request queuing for batch operations
4. Add visual rate limit indicator in UI

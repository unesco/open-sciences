# Multi-Filter Survey Responses Search API

## Overview

The multi-filter search endpoint allows you to find countries that satisfy multiple question/answer combinations with support for OR logic within each filter.

## Endpoint

```
GET /api/search/survey-responses-multi-filter
```

## Parameters

The endpoint accepts a `filters` array parameter where each filter specifies:
- `question`: Question number (e.g., "2.8", "1.1")
- `answer`: One or more answer short codes, comma-separated for OR logic

URL format: `filters[N][question]` and `filters[N][answer]` where N is the filter index (0, 1, 2, ...)

### Valid Answer Codes
- `Y` - Yes
- `N` - No
- `P` - Partly
- `U` - Under Development
- `X` - Not applicable

## Examples

### Example 1: Single answer per filter
Find countries that answered "Yes" to question 2.8 AND "No" to question 2.9:

```bash
curl "http://localhost/api/search/survey-responses-multi-filter?filters[0][question]=2.8&filters[0][answer]=Y&filters[1][question]=2.9&filters[1][answer]=N"
```

### Example 2: Multiple answers per filter (OR logic)
Find countries that answered (Yes OR Partly) to question 2.8 AND (No OR Not applicable) to question 2.9:

```bash
curl "http://localhost/api/search/survey-responses-multi-filter?filters[0][question]=2.8&filters[0][answer]=Y,P&filters[1][question]=2.9&filters[1][answer]=N,X"
```

### Example 3: Three filters
Find countries matching three conditions:

```bash
curl "http://localhost/api/search/survey-responses-multi-filter?filters[0][question]=1.1&filters[0][answer]=Y&filters[1][question]=2.1&filters[1][answer]=Y,P&filters[2][question]=3.5&filters[2][answer]=N"
```

### Example 4: Using curl with -G and --data-urlencode (recommended)
```bash
curl -G "http://localhost/api/search/survey-responses-multi-filter" \
  --data-urlencode "filters[0][question]=2.8" \
  --data-urlencode "filters[0][answer]=Y,P" \
  --data-urlencode "filters[1][question]=2.9" \
  --data-urlencode "filters[1][answer]=N"
```

## Response Format

### Success Response (200 OK)

```json
{
  "countries": [
    {
      "iso3": "ALB",
      "name": "Albania",
      "responses": [
        {
          "question_number": "2.8",
          "question_text": "Question text here...",
          "question_type": "Closed",
          "answer_short": "Y",
          "answer": "Yes"
        },
        {
          "question_number": "2.9",
          "question_text": "Another question...",
          "question_type": "Closed",
          "answer_short": "N",
          "answer": "No"
        }
      ]
    },
    {
      "iso3": "BRA",
      "name": "Brazil",
      "responses": [...]
    }
  ],
  "filters_applied": [
    {
      "question": "2.8",
      "answers": ["Y"]
    },
    {
      "question": "2.9",
      "answers": ["N"]
    }
  ],
  "total_countries": 2
}
```

### No Results (200 OK)

```json
{
  "countries": [],
  "filters_applied": [...],
  "total_countries": 0
}
```

### Error Responses

#### Missing filters (400 Bad Request)
```json
{
  "error": "At least one filter is required"
}
```

#### Invalid question format (400 Bad Request)
```json
{
  "error": "Filter 0: Invalid question number format 'abc'"
}
```

#### Invalid answer code (400 Bad Request)
```json
{
  "error": "Filter 0: Invalid answer 'Z'. Valid values: Y, N, P, U, X"
}
```

#### Missing required parameter (400 Bad Request)
```json
{
  "error": "Filter 1: 'answer' parameter is required"
}
```

#### Server error (500 Internal Server Error)
```json
{
  "error": "OpenSearch client not available"
}
```

## Key Features

1. **Unlimited Filters**: Add as many filters as needed
2. **OR Logic Within Filters**: Use comma-separated answers for "any of" logic
3. **AND Logic Between Filters**: Countries must satisfy ALL filters
4. **Filtered Results**: Returns only responses for the specified questions, not all survey data
5. **Sorted Output**: Countries sorted alphabetically by name
6. **Case Insensitive**: Answer codes are case-insensitive (y, Y, yes all convert to Y)

## Logic Flow

1. **Parse & Validate**: Validate all filter parameters
2. **Query Per Filter**: Execute OpenSearch query for each filter to get matching countries
3. **Intersection**: Calculate countries appearing in ALL filter results
4. **Fetch Responses**: Retrieve only the filtered questions for matching countries
5. **Group & Format**: Group responses by country and return formatted JSON

## Implementation Details

- **Controller**: `MultiFilterSearchController.php`
- **Route**: `open_science_survey.multi_filter`
- **Indexed Fields Used**:
  - `question_number` (string)
  - `answer_closed_short_name` (string)
  - `country_iso3` (string)
  - `country_name` (string)
  - `question_text` (string)
  - `question_type` (string)
  - `answer_closed_name` (string)


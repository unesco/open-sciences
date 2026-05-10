<?php

namespace Drupal\open_science_survey\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Drupal\search_api\Entity\Server;

/**
 * REST controller for multi-filter country search.
 */
class MultiFilterSearchController extends ControllerBase {

  /**
   * Valid answer short names.
   */
  const VALID_ANSWERS = ['Y', 'N', 'P', 'U', 'X'];

  /**
   * Get OpenSearch client.
   *
   * @return object|null
   *   OpenSearch client or NULL on error.
   */
  protected function getOpenSearchClient() {
    try {
      /** @var \Drupal\search_api\ServerInterface $server */
      $server = Server::load('open_search');

      if (!$server) {
        return NULL;
      }

      /** @var \Drupal\search_api_opensearch\Plugin\search_api\backend\SearchApiOpensearchBackend $backend */
      $backend = $server->getBackend();

      return $backend->getClient();
    }
    catch (\Exception $e) {
      $this->getLogger('open_science_survey')->error('Failed to get OpenSearch client: @message', ['@message' => $e->getMessage()]);
      return NULL;
    }
  }

  /**
   * Get index name with prefix.
   *
   * @return string
   *   Full index name.
   */
  protected function getIndexName() {
    try {
      $server = Server::load('open_search');
      $backend_config = $server->getBackendConfig();
      $prefix = $backend_config['advanced']['prefix'] ?? '';
      return $prefix . 'survey_responses';
    }
    catch (\Exception $e) {
      return 'cms_survey_responses';
    }
  }

  /**
   * Validate and parse filters from request.
   *
   * @param array $filters
   *   Raw filters array from query parameters.
   *
   * @return array
   *   Array with 'valid' => bool, 'filters' => parsed array, 'error' => string.
   */
  protected function parseFilters(array $filters) {
    $parsed = [];

    if (empty($filters)) {
      return [
        'valid' => FALSE,
        'error' => 'At least one filter is required',
      ];
    }

    foreach ($filters as $index => $filter) {
      // Validate question field.
      if (empty($filter['question'])) {
        return [
          'valid' => FALSE,
          'error' => "Filter {$index}: 'question' parameter is required",
        ];
      }

      $question = trim($filter['question']);

      // Validate question number format (digits and dots).
      if (!preg_match('/^[\d.]+$/', $question)) {
        return [
          'valid' => FALSE,
          'error' => "Filter {$index}: Invalid question number format '{$question}'",
        ];
      }

      // Validate answer field.
      if (empty($filter['answer'])) {
        return [
          'valid' => FALSE,
          'error' => "Filter {$index}: 'answer' parameter is required",
        ];
      }

      // Parse comma-separated answers.
      $answers = array_map('trim', explode(',', $filter['answer']));
      $answers = array_filter($answers); // Remove empty values.

      if (empty($answers)) {
        return [
          'valid' => FALSE,
          'error' => "Filter {$index}: At least one answer is required",
        ];
      }

      // Validate each answer.
      foreach ($answers as $answer) {
        $answer_upper = strtoupper($answer);
        if (!in_array($answer_upper, self::VALID_ANSWERS, TRUE)) {
          return [
            'valid' => FALSE,
            'error' => "Filter {$index}: Invalid answer '{$answer}'. Valid values: " . implode(', ', self::VALID_ANSWERS),
          ];
        }
      }

      // Store parsed filter.
      $parsed[] = [
        'question' => $question,
        'answers' => array_map('strtoupper', $answers),
      ];
    }

    return [
      'valid' => TRUE,
      'filters' => $parsed,
    ];
  }

  /**
   * Build OpenSearch query for a single filter criterion.
   *
   * @param string $question
   *   Question number.
   * @param array $answers
   *   Array of answer short names.
   *
   * @return array
   *   OpenSearch query structure.
   */
  protected function buildFilterQuery($question, array $answers) {
    $must_clauses = [
      [
        'term' => ['question_number.keyword' => $question],
      ],
    ];

    // If multiple answers, use terms query for OR logic.
    if (count($answers) === 1) {
      $must_clauses[] = [
        'term' => ['answer_closed_short_name.keyword' => $answers[0]],
      ];
    }
    else {
      $must_clauses[] = [
        'terms' => ['answer_closed_short_name.keyword' => $answers],
      ];
    }

    return [
      'bool' => [
        'must' => $must_clauses,
      ],
    ];
  }

  /**
   * Get countries matching multiple filter criteria using multi-search.
   *
   * @param object $client
   *   OpenSearch client.
   * @param array $filters
   *   Array of parsed filters with 'question' and 'answers' keys.
   *
   * @return array|null
   *   Array of country sets (one per filter) or NULL on error.
   */
  protected function getCountriesForFiltersMultiSearch($client, array $filters) {
    if (empty($filters)) {
      return [];
    }

    $index_name = $this->getIndexName();
    $body = [];

    // Build multi-search request body.
    foreach ($filters as $filter) {
      $query = $this->buildFilterQuery($filter['question'], $filter['answers']);

      // Header line for this search.
      $body[] = ['index' => $index_name];

      // Body line for this search.
      $body[] = [
        'size' => 0,
        'query' => $query,
        'aggs' => [
          'countries' => [
            'terms' => [
              'field' => 'country_iso3.keyword',
              'size' => 1000,
            ],
          ],
        ],
      ];
    }

    $params = ['body' => $body];

    try {
      $response = $client->msearch($params);
      $responses = $response['responses'] ?? [];

      if (count($responses) !== count($filters)) {
        $this->getLogger('open_science_survey')->error(
          'Multi-search returned unexpected number of responses: expected @expected, got @actual',
          ['@expected' => count($filters), '@actual' => count($responses)]
        );
        return NULL;
      }

      $country_sets = [];

      foreach ($responses as $index => $single_response) {
        // Check for errors in individual response.
        if (isset($single_response['error'])) {
          $this->getLogger('open_science_survey')->error(
            'Multi-search response @index returned error: @error',
            [
              '@index' => $index,
              '@error' => json_encode($single_response['error']),
            ]
          );
          return NULL;
        }

        $buckets = $single_response['aggregations']['countries']['buckets'] ?? [];

        $country_sets[] = array_map(function($bucket) {
          return $bucket['key'];
        }, $buckets);
      }

      return $country_sets;

    }
    catch (\Exception $e) {
      $this->getLogger('open_science_survey')->error(
        'Failed to execute multi-search query: @message',
        ['@message' => $e->getMessage()]
      );
      return NULL;
    }
  }

  /**
   * Get responses for specific countries and questions.
   *
   * @param object $client
   *   OpenSearch client.
   * @param array $country_iso_codes
   *   Array of country ISO3 codes.
   * @param array $question_numbers
   *   Array of question numbers.
   *
   * @return array|null
   *   Array of response documents or NULL on error.
   */
  protected function getResponsesForCountries($client, array $country_iso_codes, array $question_numbers) {
    $params = [
      'index' => $this->getIndexName(),
      'body' => [
        'size' => 10000, // Adjust as needed.
        'query' => [
          'bool' => [
            'must' => [
              [
                'terms' => ['country_iso3.keyword' => $country_iso_codes],
              ],
              [
                'terms' => ['question_number.keyword' => $question_numbers],
              ],
            ],
          ],
        ],
        '_source' => [
          'country_iso3',
          'country_name',
          'question_number',
          'question_text',
          'question_type',
          'answer_closed_name',
          'answer_closed_short_name',
          'answer_open_text_raw',
        ],
        'sort' => [
          ['country_iso3.keyword' => 'asc'],
          ['question_number.keyword' => 'asc'],
        ],
      ],
    ];

    try {
      $response = $client->search($params);
      return $response['hits']['hits'] ?? [];

    }
    catch (\Exception $e) {
      $this->getLogger('open_science_survey')->error(
        'Failed to fetch responses for countries: @message',
        ['@message' => $e->getMessage()]
      );
      return NULL;
    }
  }

  /**
   * Extract string value from OpenSearch field (handles array or string).
   *
   * @param mixed $value
   *   The value from OpenSearch source.
   *
   * @return string
   *   Extracted string value.
   */
  protected function extractValue($value) {
    if (is_array($value)) {
      return (string) ($value[0] ?? '');
    }
    return (string) $value;
  }

  /**
   * Multi-filter country search endpoint.
   *
   * GET /api/search/survey-responses-multi-filter
   * Query params:
   *   - filters[0][question]: Question number (e.g., "2.8")
   *   - filters[0][answer]: Answer(s), comma-separated (e.g., "Y,P")
   *   - filters[1][question]: Another question number
   *   - filters[1][answer]: Answer(s) for second criterion
   *   - ... (unlimited filters)
   *
   * @param \Symfony\Component\HttpFoundation\Request $request
   *   The request object.
   *
   * @return \Symfony\Component\HttpFoundation\JsonResponse
   *   JSON response with matching countries and their responses.
   */
  public function search(Request $request) {
    $client = $this->getOpenSearchClient();

    if (!$client) {
      return new JsonResponse([
        'error' => 'OpenSearch client not available',
      ], 500);
    }

    // Get and parse filters from query parameters.
    $all_params = $request->query->all();
    $raw_filters = $all_params['filters'] ?? [];

    $validation = $this->parseFilters($raw_filters);

    if (!$validation['valid']) {
      return new JsonResponse([
        'error' => $validation['error'],
      ], 400);
    }

    $filters = $validation['filters'];

    // Step 1 & 2: Get countries matching each filter using multi-search.
    $country_sets = $this->getCountriesForFiltersMultiSearch($client, $filters);

    if ($country_sets === NULL) {
      return new JsonResponse([
        'error' => 'Failed to process filters',
      ], 500);
    }

    // Find intersection of all country sets.
    $matching_countries = empty($country_sets) ? [] :
      (count($country_sets) === 1 ? $country_sets[0] :
      array_values(array_intersect(...$country_sets)));

    // If no matching countries, return early.
    if (empty($matching_countries)) {
      return new JsonResponse([
        'countries' => [],
        'filters_applied' => array_map(function($filter) {
          return [
            'question' => $filter['question'],
            'answers' => $filter['answers'],
          ];
        }, $filters),
        'total_countries' => 0,
      ]);
    }

    // Step 3: Fetch responses for matching countries (only for filtered questions).
    $question_numbers = array_map(function($filter) {
      return $filter['question'];
    }, $filters);

    $hits = $this->getResponsesForCountries(
      $client,
      $matching_countries,
      $question_numbers
    );

    if ($hits === NULL) {
      return new JsonResponse([
        'error' => 'Failed to fetch survey responses',
      ], 500);
    }

    // Step 4: Group responses by country.
    $countries_data = [];

    foreach ($hits as $hit) {
      $source = $hit['_source'] ?? [];

      $country_iso = $this->extractValue($source['country_iso3'] ?? '');

      if (empty($country_iso)) {
        continue;
      }

      if (!isset($countries_data[$country_iso])) {
        $countries_data[$country_iso] = [
          'iso3' => $country_iso,
          'name' => $this->extractValue($source['country_name'] ?? ''),
          'responses' => [],
        ];
      }

      // Extract response fields - handle array cases.
      $response_data = [
        'question_number' => $this->extractValue($source['question_number'] ?? ''),
        'question_text' => $this->extractValue($source['question_text'] ?? ''),
        'question_type' => $this->extractValue($source['question_type'] ?? ''),
      ];

      // Include appropriate answer field based on question type.
      if (!empty($source['answer_closed_short_name'])) {
        $response_data['answer_short'] = $this->extractValue($source['answer_closed_short_name']);
        $response_data['answer'] = $this->extractValue($source['answer_closed_name'] ?? '');
      }

      if (!empty($source['answer_open_text_raw'])) {
        $response_data['answer_open'] = $this->extractValue($source['answer_open_text_raw']);
      }

      $countries_data[$country_iso]['responses'][] = $response_data;
    }

    // Convert to indexed array and sort by country name.
    $countries_list = array_values($countries_data);
    usort($countries_list, function($a, $b) {
      return strcmp($a['name'], $b['name']);
    });

    return new JsonResponse([
      'countries' => $countries_list,
      'filters_applied' => array_map(function($filter) {
        return [
          'question' => $filter['question'],
          'answers' => $filter['answers'],
        ];
      }, $filters),
      'total_countries' => count($countries_list),
    ]);
  }

}

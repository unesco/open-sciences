<?php

namespace Drupal\open_science_survey_search\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Drupal\search_api\Entity\Server;

/**
 * REST controller for word cloud endpoint.
 */
class WordCloudController extends ControllerBase {

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
    } catch (\Exception $e) {
      $this->getLogger('open_science_survey_search')->error('Failed to get OpenSearch client: @message', ['@message' => $e->getMessage()]);
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
    } catch (\Exception $e) {
      return 'cms_survey_responses';
    }
  }

  /**
   * Word cloud endpoint using significant_terms aggregation.
   *
   * GET /api/wordcloud
   * Query params:
   *   - question_number: Filter by question number
   *   - country_iso3: Filter by country ISO3 code
   *
   * @param \Symfony\Component\HttpFoundation\Request $request
   *   The request object.
   *
   * @return \Symfony\Component\HttpFoundation\JsonResponse
   *   JSON response with word cloud data.
   */
  public function wordcloud(Request $request) {
    $client = $this->getOpenSearchClient();

    if (!$client) {
      return new JsonResponse([
        'error' => 'OpenSearch client not available',
      ], 500);
    }

    // Get filter parameters.
    $question_number = $request->query->get('question_number');
    $country_iso3 = $request->query->get('country_iso3');

    // Get configuration.
    $config = $this->config('open_science_survey_search.settings');
    $terms_config = $config->get('significant_terms') ?? [
      'min_doc_count' => 2,
      'shard_size' => 100,
      'size' => 50,
      'max_entries' => 50,
      'min_weight_percent' => 0,
    ];

    $max_entries = max(1, (int) ($terms_config['max_entries'] ?? $terms_config['size'] ?? 50));
    $min_weight_percent = (float) ($terms_config['min_weight_percent'] ?? 0);
    $min_weight_percent = max(0, min(100, $min_weight_percent));

    // Build query.
    $query = ['bool' => ['must' => []]];

    // Add filters if provided.
    if ($question_number) {
      $query['bool']['must'][] = [
        'term' => ['question_number' => $question_number],
      ];
    }

    if ($country_iso3) {
      $query['bool']['must'][] = [
        'term' => ['country_iso3' => $country_iso3],
      ];
    }

    // Determine if we have filters.
    $has_filters = !empty($query['bool']['must']);

    // If no filters, match all.
    if (!$has_filters) {
      $query = ['match_all' => (object) []];
    }

    // Use terms aggregation to get most frequently occurring words.
    // This gives us word frequency, which is what you want for a word cloud.
    // Use the wordcloud sub-field which has no stemming (readable words).
    $aggregation = [
      'top_terms' => [
        'terms' => [
          'field' => 'answer_open_text.wordcloud',
          'min_doc_count' => $terms_config['min_doc_count'],
          'size' => $terms_config['size'],
          'order' => ['_count' => 'desc'],
        ],
      ],
    ];

    // Build search request.
    $params = [
      'index' => $this->getIndexName(),
      'body' => [
        'size' => 0,
        'query' => $query,
        'aggs' => $aggregation,
      ],
    ];

    try {
      $response = $client->search($params);

      // Extract terms from response.
      $buckets = $response['aggregations']['top_terms']['buckets'] ?? [];

      $total = 0;
      foreach ($buckets as $bucket) {
        $total += $bucket['doc_count'];
      }
      if ($total == 0) {
        $buckets = [];
      }

      $terms = array_map(function($bucket) use ($total) {
        return [
          'term' => $bucket['key'],
          'percent' => 100 * $bucket['doc_count'] / $total, // Normalize count to total documents for relative size.
        ];
      }, $buckets);

      if (count($terms) > $max_entries) {
        $terms = array_slice($terms, 0, $max_entries);
      }

      return new JsonResponse([
        'filters' => [
          'question_number' => $question_number,
          'country_iso3' => $country_iso3,
        ],
        'terms' => $terms,
      ]);

    } catch (\Exception $e) {
      $this->getLogger('open_science_survey_search')->error('Word cloud query failed: @message', ['@message' => $e->getMessage()]);

      return new JsonResponse([
        'error' => 'Failed to generate word cloud',
        'message' => $e->getMessage(),
      ], 500);
    }
  }

}

<?php

namespace Drupal\open_science_survey_search\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Drupal\search_api\Entity\Server;

/**
 * REST controller for word cloud and term-in-context endpoints.
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
    ];

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
      
      $terms = array_map(function($bucket) {
        return [
          'term' => $bucket['key'],
          'count' => $bucket['doc_count'],
        ];
      }, $buckets);

      return new JsonResponse([
        'total' => $response['hits']['total']['value'] ?? 0,
        'terms' => $terms,
        'filters' => [
          'question_number' => $question_number,
          'country_iso3' => $country_iso3,
        ],
      ]);

    } catch (\Exception $e) {
      $this->getLogger('open_science_survey_search')->error('Word cloud query failed: @message', ['@message' => $e->getMessage()]);
      
      return new JsonResponse([
        'error' => 'Failed to generate word cloud',
        'message' => $e->getMessage(),
      ], 500);
    }
  }

  /**
   * Term-in-context endpoint.
   *
   * GET /api/term-context
   * Query params:
   *   - term: The term to search for (required)
   *   - question_number: Filter by question number
   *   - country_iso3: Filter by country ISO3 code
   *
   * @param \Symfony\Component\HttpFoundation\Request $request
   *   The request object.
   *
   * @return \Symfony\Component\HttpFoundation\JsonResponse
   *   JSON response with matching documents and highlighted snippets.
   */
  public function termContext(Request $request) {
    $client = $this->getOpenSearchClient();
    
    if (!$client) {
      return new JsonResponse([
        'error' => 'OpenSearch client not available',
      ], 500);
    }

    $term = $request->query->get('term');
    
    if (!$term) {
      return new JsonResponse([
        'error' => 'Missing required parameter: term',
      ], 400);
    }

    // Get filter parameters.
    $question_number = $request->query->get('question_number');
    $country_iso3 = $request->query->get('country_iso3');

    // Build query with filters.
    $must_clauses = [
      [
        'match' => [
          'answer_open_text' => $term,
        ],
      ],
    ];
    
    if ($question_number) {
      $must_clauses[] = [
        'term' => ['question_number' => $question_number],
      ];
    }
    
    if ($country_iso3) {
      $must_clauses[] = [
        'term' => ['country_iso3' => $country_iso3],
      ];
    }

    // Build search request with highlighting.
    $params = [
      'index' => $this->getIndexName(),
      'body' => [
        'size' => 50,
        'query' => [
          'bool' => [
            'must' => $must_clauses,
          ],
        ],
        'highlight' => [
          'fields' => [
            'answer_open_text' => [
              'type' => 'unified',
              'fragment_size' => 200,
              'number_of_fragments' => 1,
              'pre_tags' => ['<mark>'],
              'post_tags' => ['</mark>'],
            ],
          ],
        ],
        '_source' => [
          'answer_open_text_raw',
          'question_number',
          'question_text',
          'country_name',
          'country_iso3',
        ],
      ],
    ];

    try {
      $response = $client->search($params);
      
      // Extract hits with highlights.
      $hits = $response['hits']['hits'] ?? [];
      
      $results = array_map(function($hit) {
        $source = $hit['_source'] ?? [];
        $highlight = $hit['highlight']['answer_open_text'][0] ?? null;
        
        return [
          'id' => $hit['_id'],
          'text' => $source['answer_open_text_raw'] ?? '',
          'highlight' => $highlight,
          'question_number' => $source['question_number'] ?? null,
          'question_text' => $source['question_text'] ?? null,
          'country_name' => $source['country_name'] ?? null,
          'country_iso3' => $source['country_iso3'] ?? null,
        ];
      }, $hits);

      return new JsonResponse([
        'total' => $response['hits']['total']['value'] ?? 0,
        'term' => $term,
        'results' => $results,
        'filters' => [
          'question_number' => $question_number,
          'country_iso3' => $country_iso3,
        ],
      ]);

    } catch (\Exception $e) {
      $this->getLogger('open_science_survey_search')->error('Term context query failed: @message', ['@message' => $e->getMessage()]);
      
      return new JsonResponse([
        'error' => 'Failed to search term in context',
        'message' => $e->getMessage(),
      ], 500);
    }
  }

}

<?php

namespace Drupal\open_science_survey\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\StreamedResponse;

/**
 * REST controller for challenge context export endpoint.
 */
class TermContextController extends ControllerBase {

  /**
   * Challenge context endpoint.
   *
   * GET /api/term-context
   * Query params:
   *   - challenge: Challenge term label (required)
   *   - question_number: Filter by question number
   *   - region: Filter by country region
   *
   * @param \Symfony\Component\HttpFoundation\Request $request
   *   The request object.
   *
   * @return \Symfony\Component\HttpFoundation\JsonResponse|\Symfony\Component\HttpFoundation\StreamedResponse
   *   CSV download response or JSON error response.
   */
  public function termContext(Request $request) {
    $challenge = $this->normalizeFilterValue($request->query->get('challenge'));
    if ($challenge === NULL) {
      return new JsonResponse([
        'error' => 'Missing required parameter: challenge',
      ], 400);
    }

    $question_number = $this->normalizeFilterValue($request->query->get('question_number'));
    $region = $this->normalizeFilterValue($request->query->get('region'));

    try {
      $challenge_term_ids = $this->resolveTaxonomyTermIdsByName('challenges', $challenge);
      if (empty($challenge_term_ids)) {
        return $this->buildCsvResponse($challenge, $region, []);
      }

      $question_term_ids = NULL;
      if ($question_number !== NULL) {
        $question_term_ids = $this->resolveTaxonomyTermIdsByField('survey_question', 'field_question_number', $question_number);
        if (empty($question_term_ids)) {
          return $this->buildCsvResponse($challenge, $region, []);
        }
      }

      $country_term_ids = NULL;
      if ($region !== NULL) {
        $country_term_ids = $this->resolveTaxonomyTermIdsByField('countries', 'field_region', $region);
        if (empty($country_term_ids)) {
          return $this->buildCsvResponse($challenge, $region, []);
        }
      }

      $survey_response_storage = $this->entityTypeManager()->getStorage('survey_response');
      $query = $survey_response_storage->getQuery()->accessCheck(TRUE)
        ->condition('status', 1)
        ->condition('field_challenge.target_id', $challenge_term_ids, 'IN');

      if ($question_term_ids !== NULL) {
        $query->condition('field_question.target_id', $question_term_ids, 'IN');
      }

      if ($country_term_ids !== NULL) {
        $query->condition('field_country.target_id', $country_term_ids, 'IN');
      }

      $survey_response_ids = $query->execute();
      if (empty($survey_response_ids)) {
        return $this->buildCsvResponse($challenge, $region, []);
      }

      $rows = [];
      $survey_responses = $survey_response_storage->loadMultiple($survey_response_ids);
      foreach ($survey_responses as $survey_response) {
        $country = '';
        $question_number_value = '';
        $answer = '';

        if ($survey_response->hasField('field_country') && !$survey_response->get('field_country')->isEmpty()) {
          $country_term = $survey_response->get('field_country')->entity;
          $country = $country_term ? trim((string) $country_term->label()) : '';
        }

        if ($survey_response->hasField('field_question') && !$survey_response->get('field_question')->isEmpty()) {
          $question_term = $survey_response->get('field_question')->entity;
          if ($question_term && $question_term->hasField('field_question_number') && !$question_term->get('field_question_number')->isEmpty()) {
            $question_number_value = trim((string) $question_term->get('field_question_number')->value);
          }
        }

        if ($survey_response->hasField('field_open_ans') && !$survey_response->get('field_open_ans')->isEmpty()) {
          $answer = (string) $survey_response->get('field_open_ans')->value;
        }

        $rows[] = [$country, $question_number_value, $answer];
      }

      return $this->buildCsvResponse($challenge, $region, $rows);
    }
    catch (\Exception $e) {
      $this->getLogger('open_science_survey')->error('Challenge context CSV export failed: @message', ['@message' => $e->getMessage()]);

      return new JsonResponse([
        'error' => 'Failed to export challenge context CSV',
      ], 500);
    }
  }

  /**
   * Resolves taxonomy term IDs by vocabulary and term name.
   *
   * @param string $vocabulary
   *   Vocabulary machine name.
   * @param string $name
   *   Taxonomy term name.
   *
   * @return array
   *   Matching taxonomy term IDs.
   */
  protected function resolveTaxonomyTermIdsByName($vocabulary, $name) {
    $taxonomy_term_storage = $this->entityTypeManager()->getStorage('taxonomy_term');
    $query = $taxonomy_term_storage->getQuery()->accessCheck(FALSE)
      ->condition('vid', $vocabulary)
      ->condition('name', $name);

    return array_values($query->execute());
  }

  /**
   * Resolves taxonomy term IDs by vocabulary and field value.
   *
   * @param string $vocabulary
   *   Vocabulary machine name.
   * @param string $field_name
   *   Taxonomy term field machine name.
   * @param string $value
   *   Filter value.
   *
   * @return array
   *   Matching taxonomy term IDs.
   */
  protected function resolveTaxonomyTermIdsByField($vocabulary, $field_name, $value) {
    $taxonomy_term_storage = $this->entityTypeManager()->getStorage('taxonomy_term');
    $query = $taxonomy_term_storage->getQuery()->accessCheck(FALSE)
      ->condition('vid', $vocabulary)
      ->condition($field_name . '.value', $value);

    return array_values($query->execute());
  }

  /**
   * Normalizes a query-string filter value.
   *
   * @param mixed $value
   *   Raw query-string value.
   *
   * @return string|null
   *   Trimmed value or NULL when empty.
   */
  protected function normalizeFilterValue($value) {
    if ($value === NULL) {
      return NULL;
    }

    $value = trim((string) $value);
    return $value === '' ? NULL : $value;
  }

  /**
   * Builds CSV export response.
   *
   * @param string $challenge
   *   Required challenge filter.
   * @param string|null $region
   *   Optional region filter.
   * @param array $rows
   *   CSV data rows.
   *
   * @return \Symfony\Component\HttpFoundation\StreamedResponse
   *   CSV streamed response.
   */
  protected function buildCsvResponse($challenge, $region, array $rows) {
    $region_part = $region ?? 'Worldwide';
    $filename = $this->sanitizeFilenamePart($challenge) . '_' . $this->sanitizeFilenamePart($region_part) . '.csv';

    $response = new StreamedResponse(function() use ($rows) {
      $handle = fopen('php://output', 'w');
      fputcsv($handle, ['country', 'question_number', 'answer']);

      foreach ($rows as $row) {
        fputcsv($handle, $row);
      }

      fclose($handle);
    });

    $response->headers->set('Content-Type', 'text/csv; charset=UTF-8');
    $response->headers->set('Content-Disposition', 'attachment; filename="' . $filename . '"');

    return $response;
  }

  /**
   * Sanitizes a filename segment for safe CSV download names.
   *
   * @param string $value
   *   Raw value.
   *
   * @return string
   *   Lowercase filename-safe segment.
   */
  protected function sanitizeFilenamePart($value) {
    $sanitized = preg_replace('/[^a-z0-9]+/i', '_', strtolower((string) $value));
    $sanitized = trim($sanitized, '_');

    return $sanitized === '' ? 'value' : $sanitized;
  }

}

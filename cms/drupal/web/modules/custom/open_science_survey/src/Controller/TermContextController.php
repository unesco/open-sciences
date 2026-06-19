<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <https://www.gnu.org/licenses/>.

namespace Drupal\open_science_survey\Controller;

use Drupal\Core\Cache\Cache;
use Drupal\Core\Cache\CacheableJsonResponse;
use Drupal\Core\Cache\CacheableMetadata;
use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\StreamedResponse;

/**
 * REST controller for term context endpoints.
 */
class TermContextController extends ControllerBase {
    /**
     * Term context CSV endpoint.
     *
     * GET /api/download/term-context
     * Query params:
    *   - term: Challenge term label
    *   - question_number: Filter by question number
    *   - region: Filter by country region
     *
     * @param \Symfony\Component\HttpFoundation\Request $request
     *   The request object.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse|\Symfony\Component\HttpFoundation\StreamedResponse
     *   CSV download response or JSON error response.
     */
    public function termContextCsv(Request $request) {
        $term = $this->normalizeFilterValue($request->query->get('term'));
        $question_number = $this->normalizeFilterValue($request->query->get('question_number'));
        $region = $this->normalizeFilterValue($request->query->get('region'));

        try {
            $challenge_term_ids = null;
            if ($term !== null) {
                $challenge_terms = $this->loadChallengeTermsByName($term);
                if (empty($challenge_terms)) {
                    return $this->buildCsvResponse($term, $region, []);
                }

                $challenge_term_ids = array_keys($challenge_terms);
            }

            $survey_responses = $this->loadSurveyResponses($challenge_term_ids, $question_number, $region);
            if (empty($survey_responses)) {
                return $this->buildCsvResponse($term, $region, []);
            }

            $rows = [];
            foreach ($survey_responses as $survey_response) {
                $country = $this->extractCountryName($survey_response);
                $question_number_value = $this->extractQuestionNumber($survey_response);
                $question_text_value = $this->extractQuestionText($survey_response);

                $answer = $this->extractOpenAnswer($survey_response);

                $challenges = $this->extractChallengeNames($survey_response);
                $rows[] = [$country, $question_number_value, $question_text_value, $answer, $challenges];
            }

            return $this->buildCsvResponse($term, $region, $rows);
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Term context CSV export failed: @message', ['@message' => $e->getMessage()]);

            $response = new JsonResponse([
            'error' => 'Failed to export term context CSV',
            ], 500);

            $response->headers->set('Cache-Control', 'private, no-store');
            return $response;
        }
    }

    /**
     * Term context JSON endpoint.
     *
     * GET /api/term-context
     * Query params:
     *   - term: Challenge term label (required)
     *   - question_number: Filter by question number
     *   - region: Filter by country region
     *
     * @param \Symfony\Component\HttpFoundation\Request $request
     *   The request object.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse|\Symfony\Component\HttpFoundation\StreamedResponse
     *   JSON response or JSON error response.
     */
    public function termContext(Request $request) {
        $term = $this->normalizeFilterValue($request->query->get('term'));
        if ($term === null) {
            return new JsonResponse([
            'error' => 'Missing required parameter: term',
            ], 400);
        }

        $question_number = $this->normalizeFilterValue($request->query->get('question_number'));
        $region = $this->normalizeFilterValue($request->query->get('region'));

        try {
            $challenge_terms = $this->loadChallengeTermsByName($term);
            if (empty($challenge_terms)) {
                return $this->buildJsonResponse($term, $question_number, $region, []);
            }

            $challenge_term_ids = array_keys($challenge_terms);
            $survey_responses = $this->loadSurveyResponses($challenge_term_ids, $question_number, $region);
            if (empty($survey_responses)) {
                return $this->buildJsonResponse($term, $question_number, $region, []);
            }

            $term_snippets = $this->collectTermSnippets($challenge_terms);
            $contexts = [];
            foreach ($survey_responses as $survey_response) {
                $answer = $this->extractOpenAnswer($survey_response);
                if ($answer === '') {
                    continue;
                }

                $highlighted = $this->buildHighlightedSnippet($answer, $term_snippets);
                if ($highlighted === null) {
                    continue;
                }

                $contexts[] = [
                    'country' => $this->extractCountryIso3($survey_response),
                    'question_number' => $this->extractQuestionNumber($survey_response),
                    'snippet' => $highlighted,
                ];
            }

            return $this->buildJsonResponse($term, $question_number, $region, $contexts);
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Term context JSON query failed: @message', ['@message' => $e->getMessage()]);

            $response = new JsonResponse([
            'error' => 'Failed to generate term context',
            ], 500);

            $response->headers->set('Cache-Control', 'private, no-store');
            return $response;
        }
    }

    /**
     * Loads challenge taxonomy terms by exact term name.
     *
     * @param string $term
     *   Challenge term label.
     *
     * @return \Drupal\taxonomy\TermInterface[]
     *   Loaded terms keyed by term ID.
     */
    protected function loadChallengeTermsByName($term) {
        $challenge_term_ids = $this->resolveTaxonomyTermIdsByName('challenges', $term);
        if (empty($challenge_term_ids)) {
            return [];
        }

        $taxonomy_term_storage = $this->entityTypeManager()->getStorage('taxonomy_term');
        return $taxonomy_term_storage->loadMultiple($challenge_term_ids);
    }

    /**
     * Loads survey responses using shared endpoint filters.
     *
    * @param array|null $challenge_term_ids
    *   Optional challenge term IDs.
     * @param string|null $question_number
     *   Optional question number filter.
     * @param string|null $region
     *   Optional region filter.
     *
     * @return \Drupal\Core\Entity\EntityInterface[]
     *   Survey response entities.
     */
    protected function loadSurveyResponses(?array $challenge_term_ids, $question_number, $region) {
        $question_term_ids = null;
        if ($question_number !== null) {
            $question_term_ids = $this->resolveTaxonomyTermIdsByField('survey_question', 'name', $question_number);
            if (empty($question_term_ids)) {
                return [];
            }
        }

        $country_term_ids = null;
        if ($region !== null) {
            $country_term_ids = $this->resolveTaxonomyTermIdsByField('countries', 'field_region', $region);
            if (empty($country_term_ids)) {
                return [];
            }
        }

        $survey_response_storage = $this->entityTypeManager()->getStorage('node');
        $query = $survey_response_storage->getQuery()->accessCheck(true)
            ->condition('type', 'survey_response')
            ->condition('status', 1)
            ->condition('field_challenge.target_id', null, 'IS NOT NULL');

        if ($challenge_term_ids !== null) {
            $query->condition('field_challenge.target_id', $challenge_term_ids, 'IN');
        }

        if ($question_term_ids !== null) {
            $query->condition('field_question.target_id', $question_term_ids, 'IN');
        }

        if ($country_term_ids !== null) {
            $query->condition('field_country.target_id', $country_term_ids, 'IN');
        }

        $survey_response_ids = $query->execute();
        if (empty($survey_response_ids)) {
            return [];
        }

        return $survey_response_storage->loadMultiple($survey_response_ids);
    }

    /**
     * Collects all snippet values from selected challenge terms.
     *
     * @param \Drupal\taxonomy\TermInterface[] $challenge_terms
     *   Loaded challenge terms.
     *
     * @return string[]
     *   Unique snippet values sorted by length descending.
     */
    protected function collectTermSnippets(array $challenge_terms) {
        $snippets = [];

        foreach ($challenge_terms as $challenge_term) {
            if (!$challenge_term->hasField('field_snippet') || $challenge_term->get('field_snippet')->isEmpty()) {
                continue;
            }

            foreach ($challenge_term->get('field_snippet')->getValue() as $item) {
                $snippet = trim((string) ($item['value'] ?? ''));
                if ($snippet === '') {
                    continue;
                }

                $snippets[mb_strtolower($snippet)] = $snippet;
            }
        }

        $snippets = array_values($snippets);
        usort($snippets, static function ($a, $b) {
            return mb_strlen($b) <=> mb_strlen($a);
        });

        return $snippets;
    }

    /**
     * Builds contextual highlighted snippet HTML from the first snippet occurrence.
     *
     * @param string $answer
     *   Open answer text.
     * @param string[] $term_snippets
     *   Snippet values from challenge term(s).
     *
     * @return string|null
     *   Highlighted HTML or NULL when no snippets match.
     */
    protected function buildHighlightedSnippet($answer, array $term_snippets) {
        if ($answer === '' || empty($term_snippets)) {
            return null;
        }

        $extrawords = 15;
        foreach ($term_snippets as $snippet) {
            if ($snippet === '') {
                continue;
            }

            $pattern = '/(^|(\s+\S+){0,' . $extrawords . '}\s*)'
                . '(' . preg_quote(trim($snippet), '/') . ')'
                . '(\s*(\S+\s+){0,' . $extrawords . '}|$)/iu';

            if (!preg_match($pattern, $answer, $match)) {
                continue;
            }

            return $match[1] . '<mark>' . $match[3] . '</mark> ' . $match[4];
        }

        return substr($answer, 0, 80);
    }

    /**
     * Builds JSON endpoint response payload.
     *
     * @param string $term
     *   Echoed term filter.
     * @param string|null $question_number
     *   Echoed question number filter.
     * @param string|null $region
     *   Echoed region filter.
     * @param array $contexts
     *   Context payload.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   JSON response.
     */
    protected function buildJsonResponse($term, $question_number, $region, array $contexts) {
        $response = new CacheableJsonResponse([
            'filters' => [
                'term' => $term,
                'question_number' => $question_number,
                'region' => $region,
            ],
            'contexts' => $contexts,
        ]);

        $cacheability = new CacheableMetadata();
        $cacheability->setCacheContexts(['url.query_args', 'user.permissions']);
        $cacheability->setCacheTags(['node_list:survey_response', 'taxonomy_term_list']);
        $cacheability->setCacheMaxAge(Cache::PERMANENT);
        $response->addCacheableDependency($cacheability);

        return $response;
    }

    /**
     * Extracts challenge tag names from a survey response.
     *
     * @param \Drupal\Core\Entity\EntityInterface $survey_response
     *   Survey response entity.
     *
     * @return string
     *   Comma-separated challenge names or empty string.
     */
    protected function extractChallengeNames($survey_response) {
        if (!$survey_response->hasField('field_challenge') || $survey_response->get('field_challenge')->isEmpty()) {
            return '';
        }

        $names = [];
        foreach ($survey_response->get('field_challenge') as $item) {
            $term = $item->entity;
            if ($term) {
                $names[] = $term->label();
            }
        }

        return implode(', ', $names);
    }

    /**
     * Extracts open answer text from a survey response.
     *
     * @param \Drupal\Core\Entity\EntityInterface $survey_response
     *   Survey response entity.
     *
     * @return string
     *   Open answer text or empty string.
     */
    protected function extractOpenAnswer($survey_response) {
        if ($survey_response->hasField('field_open_ans') && !$survey_response->get('field_open_ans')->isEmpty()) {
            return (string) $survey_response->get('field_open_ans')->value;
        }

        return '';
    }

    /**
     * Extracts country label from a survey response.
     *
     * @param \Drupal\Core\Entity\EntityInterface $survey_response
     *   Survey response entity.
     *
     * @return string
     *   Country label or empty string when unavailable.
     */
    protected function extractCountryName($survey_response) {
        if (!$survey_response->hasField('field_country') || $survey_response->get('field_country')->isEmpty()) {
            return '';
        }

        $country_term = $survey_response->get('field_country')->entity;
        if (!$country_term) {
            return '';
        }

        return trim((string) $country_term->label());
    }

    /**
     * Extracts country ISO3 code from a survey response.
     *
     * @param \Drupal\Core\Entity\EntityInterface $survey_response
     *   Survey response entity.
     *
     * @return string
     *   ISO3 code or empty string when unavailable.
     */
    protected function extractCountryIso3($survey_response) {
        if (!$survey_response->hasField('field_country') || $survey_response->get('field_country')->isEmpty()) {
            return '';
        }

        $country_term = $survey_response->get('field_country')->entity;
        if (!$country_term || !$country_term->hasField('field_iso_alpha3_code') || $country_term->get('field_iso_alpha3_code')->isEmpty()) {
            return '';
        }

        return trim((string) $country_term->get('field_iso_alpha3_code')->value);
    }

    /**
     * Extracts question number from a survey response.
     *
     * @param \Drupal\Core\Entity\EntityInterface $survey_response
     *   Survey response entity.
     *
     * @return string
     *   Question number or empty string when unavailable.
     */
    protected function extractQuestionNumber($survey_response) {
        if (!$survey_response->hasField('field_question') || $survey_response->get('field_question')->isEmpty()) {
            return '';
        }

        $question_term = $survey_response->get('field_question')->entity;
        if (!$question_term) {
            return '';
        }

        return trim((string) $question_term->label());
    }

    /**
     * Extracts question text from a survey response.
     *
     * @param \Drupal\Core\Entity\EntityInterface $survey_response
     *   Survey response entity.
     *
     * @return string
     *   Question text or empty string when unavailable.
     */
    protected function extractQuestionText($survey_response) {
        if (!$survey_response->hasField('field_question') || $survey_response->get('field_question')->isEmpty()) {
            return '';
        }

        $question_term = $survey_response->get('field_question')->entity;
        if (!$question_term || !$question_term->hasField('field_question_short_name') || $question_term->get('field_question_short_name')->isEmpty()) {
            return '';
        }

        return trim((string) $question_term->get('field_question_short_name')->value);
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
        $query = $taxonomy_term_storage->getQuery()->accessCheck(false)
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
        $condition_field = $field_name === 'name' ? 'name' : $field_name . '.value';
        $query = $taxonomy_term_storage->getQuery()->accessCheck(false)
            ->condition('vid', $vocabulary)
            ->condition($condition_field, $value);

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
        if ($value === null) {
            return null;
        }

        $value = trim((string) $value);
        return $value === '' ? null : $value;
    }

    /**
     * Builds CSV export response.
     *
    * @param string|null $term
    *   Optional term filter.
     * @param string|null $region
     *   Optional region filter.
     * @param array $rows
     *   CSV data rows.
     *
     * @return \Symfony\Component\HttpFoundation\StreamedResponse
     *   CSV streamed response.
     */
    protected function buildCsvResponse($term, $region, array $rows) {
        $term_part = $term ?? 'all_terms';
        $region_part = $region ?? 'Worldwide';
        $filename = $this->sanitizeFilenamePart($term_part) . '_' . $this->sanitizeFilenamePart($region_part) . '.csv';

        $response = new StreamedResponse(function () use ($rows) {
            $handle = fopen('php://output', 'w');
            fputcsv($handle, ['country', 'question_number', 'question_text', 'answer', 'challenges']);

            foreach ($rows as $row) {
                fputcsv($handle, $row);
            }

            fclose($handle);
        });

        $response->headers->set('Content-Type', 'text/csv; charset=UTF-8');
        $response->headers->set('Content-Disposition', 'attachment; filename="' . $filename . '"');
        $response->headers->set('Cache-Control', 'private, no-store');
        $response->headers->set('Pragma', 'no-cache');

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

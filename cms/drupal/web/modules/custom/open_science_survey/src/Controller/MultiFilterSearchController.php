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

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

/**
 * REST controller for multi-filter country search.
 */
class MultiFilterSearchController extends ControllerBase {
    /**
     * Valid answer short names.
     */
    const VALID_ANSWERS = ['Y', 'N', 'P', 'U', 'X'];

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
            'valid' => false,
            'error' => 'At least one filter is required',
            ];
        }

        foreach ($filters as $index => $filter) {
            // Validate question field.
            if (empty($filter['question'])) {
                return [
                'valid' => false,
                'error' => "Filter {$index}: 'question' parameter is required",
                ];
            }

            $question = trim($filter['question']);

            // Validate question number format (digits and dots).
            if (!preg_match('/^[\d.]+$/', $question)) {
                return [
                'valid' => false,
                'error' => "Filter {$index}: Invalid question number format '{$question}'",
                ];
            }

            // Validate answer field.
            if (empty($filter['answer'])) {
                return [
                'valid' => false,
                'error' => "Filter {$index}: 'answer' parameter is required",
                ];
            }

            // Parse comma-separated answers.
            $answers = array_map('trim', explode(',', $filter['answer']));
            $answers = array_filter($answers); // Remove empty values.

            if (empty($answers)) {
                return [
                'valid' => false,
                'error' => "Filter {$index}: At least one answer is required",
                ];
            }

            // Validate each answer.
            foreach ($answers as $answer) {
                $answer_upper = strtoupper($answer);
                if (!in_array($answer_upper, self::VALID_ANSWERS, true)) {
                    return [
                    'valid' => false,
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
        'valid' => true,
        'filters' => $parsed,
        ];
    }

    /**
     * Get survey_question term IDs for a given question number.
     *
     * @param string $question_number
     *   The question number string (e.g. "2.8").
     *
     * @return array
     *   Array of term IDs.
     */
    protected function getQuestionTids(string $question_number): array {
        return $this->entityTypeManager()
            ->getStorage('taxonomy_term')
            ->getQuery()
            ->condition('vid', 'survey_question')
            ->condition('field_question_number', $question_number)
            ->accessCheck(false)
            ->execute();
    }

    /**
     * Get survey_predefined_answers term IDs for given short name codes.
     *
     * @param array $short_names
     *   Array of answer short name codes (e.g. ['Y', 'P']).
     *
     * @return array
     *   Array of term IDs.
     */
    protected function getAnswerTids(array $short_names): array {
        return $this->entityTypeManager()
            ->getStorage('taxonomy_term')
            ->getQuery()
            ->condition('vid', 'survey_predefined_answers')
            ->condition('field_short_name', $short_names, 'IN')
            ->accessCheck(false)
            ->execute();
    }

    /**
     * Get country term IDs from survey responses matching a question/answer filter.
     *
     * @param array $question_tids
     *   Array of survey_question term IDs.
     * @param array $answer_tids
     *   Array of survey_predefined_answers term IDs.
     *
     * @return array
     *   Unique array of country term IDs.
     */
    protected function getCountryTidsForFilter(array $question_tids, array $answer_tids): array {
        $storage = $this->entityTypeManager()->getStorage('node');

        $response_ids = $storage->getQuery()
            ->condition('type', 'survey_response')
            ->condition('field_question', $question_tids, 'IN')
            ->condition('field_closed_ans', $answer_tids, 'IN')
            ->condition('status', 1)
            ->accessCheck(false)
            ->execute();

        if (empty($response_ids)) {
            return [];
        }

        $responses = $storage->loadMultiple($response_ids);
        $country_tids = [];
        foreach ($responses as $response) {
            $tid = $response->get('field_country')->target_id;
            if ($tid) {
                $country_tids[$tid] = $tid;
            }
        }

        return array_values($country_tids);
    }

    /**
     * Format filters array for API response.
     *
     * @param array $filters
     *   Parsed filters.
     *
     * @return array
     *   Formatted filters for JSON output.
     */
    protected function formatFilters(array $filters): array {
        return array_map(function ($filter) {
            return [
            'question' => $filter['question'],
            'answers' => $filter['answers'],
            ];
        }, $filters);
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
        $empty_response = [
        'countries' => [],
        'filters_applied' => $this->formatFilters($filters),
        'total_countries' => 0,
        ];

        // Step 1: For each filter resolve term IDs and collect matching country TIDs.
        $country_tid_sets = [];
        $filter_question_tids = [];

        foreach ($filters as $filter) {
            $question_tids = $this->getQuestionTids($filter['question']);
            if (empty($question_tids)) {
                return new JsonResponse($empty_response);
            }
            $filter_question_tids[$filter['question']] = $question_tids;

            $answer_tids = $this->getAnswerTids($filter['answers']);
            if (empty($answer_tids)) {
                return new JsonResponse($empty_response);
            }

            $country_tids = $this->getCountryTidsForFilter($question_tids, $answer_tids);
            $country_tid_sets[] = $country_tids;
        }

        // Step 2: Intersect country TID sets (AND logic between filters).
        if (empty($country_tid_sets)) {
            return new JsonResponse($empty_response);
        }
        $matching_country_tids = count($country_tid_sets) === 1
        ? $country_tid_sets[0]
        : array_values(array_intersect(...$country_tid_sets));

        if (empty($matching_country_tids)) {
            return new JsonResponse($empty_response);
        }

        // Step 3: Load survey responses for matching countries and filtered questions.
        $all_question_tids = array_merge(...array_values($filter_question_tids));
        $response_storage = $this->entityTypeManager()->getStorage('node');

        $response_ids = $response_storage->getQuery()
            ->condition('type', 'survey_response')
            ->condition('field_country', $matching_country_tids, 'IN')
            ->condition('field_question', $all_question_tids, 'IN')
            ->condition('status', 1)
            ->accessCheck(false)
            ->execute();

        $responses = $response_storage->loadMultiple($response_ids);

        // Step 4: Pre-load term metadata to avoid N+1 queries.
        $term_storage = $this->entityTypeManager()->getStorage('taxonomy_term');

        $country_terms = $term_storage->loadMultiple($matching_country_tids);
        $country_cache = [];
        foreach ($country_terms as $tid => $term) {
            $country_cache[$tid] = [
            'iso3' => $term->get('field_iso_alpha3_code')->value ?? '',
            'name' => $term->get('field_country_name')->value ?? $term->label(),
            ];
        }

        $question_terms = $term_storage->loadMultiple($all_question_tids);
        $question_cache = [];
        foreach ($question_terms as $tid => $term) {
            $question_cache[$tid] = [
            'number' => $term->get('field_question_number')->value ?? '',
            'text' => $term->get('field_question_text')->value ?? '',
            'type' => $term->get('field_question_type')->value ?? '',
            ];
        }

        $all_answer_terms = $term_storage->loadByProperties(['vid' => 'survey_predefined_answers']);
        $answer_cache = [];
        foreach ($all_answer_terms as $tid => $term) {
            $answer_cache[$tid] = [
            'short' => $term->get('field_short_name')->value ?? '',
            'long' => $term->get('field_long_name')->value ?? '',
            ];
        }

        // Step 5: Group responses by country.
        $countries_data = [];

        foreach ($responses as $response) {
            $country_tid = $response->get('field_country')->target_id;
            if (empty($country_cache[$country_tid])) {
                continue;
            }

            $country_iso = $country_cache[$country_tid]['iso3'];
            if (empty($country_iso)) {
                continue;
            }

            if (!isset($countries_data[$country_iso])) {
                $countries_data[$country_iso] = [
                'iso3' => $country_iso,
                'name' => $country_cache[$country_tid]['name'],
                'responses' => [],
                ];
            }

            $question_tid = $response->get('field_question')->target_id;
            if (empty($question_cache[$question_tid])) {
                continue;
            }

            $q = $question_cache[$question_tid];
            $response_data = [
            'question_number' => $q['number'],
            'question_text' => $q['text'],
            'question_type' => $q['type'],
            ];

            $closed_ans_tid = $response->get('field_closed_ans')->target_id;
            if ($closed_ans_tid && isset($answer_cache[$closed_ans_tid])) {
                $response_data['answer_short'] = $answer_cache[$closed_ans_tid]['short'];
                $response_data['answer'] = $answer_cache[$closed_ans_tid]['long'];
            }

            $open_ans = $response->get('field_open_ans')->value;
            if (!empty($open_ans)) {
                $response_data['answer_open'] = $open_ans;
            }

            $countries_data[$country_iso]['responses'][] = $response_data;
        }

        // Convert to indexed array and sort by country name.
        $countries_list = array_values($countries_data);
        usort($countries_list, function ($a, $b) {
            return strcmp($a['name'], $b['name']);
        });

        return new JsonResponse([
        'countries' => $countries_list,
        'filters_applied' => $this->formatFilters($filters),
        'total_countries' => count($countries_list),
        ]);
    }
}

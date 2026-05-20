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
 * REST controller for challenge word cloud endpoint.
 */
class WordCloudController extends ControllerBase {
    /**
     * Challenge occurrence word cloud endpoint.
     *
     * GET /api/wordcloud
     * Query params:
     *   - question_number: Filter by question number
     *   - region: Filter by country region
     *
     * @param \Symfony\Component\HttpFoundation\Request $request
     *   The request object.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   JSON response with challenge term percentages.
     */
    public function wordcloud(Request $request) {
        $question_number = $this->normalizeFilterValue($request->query->get('question_number'));
        $region = $this->normalizeFilterValue($request->query->get('region'));

        try {
            $question_term_ids = null;
            if ($question_number !== null) {
                $question_term_ids = $this->resolveTaxonomyTermIds('survey_question', 'field_question_number', $question_number);
                if (empty($question_term_ids)) {
                    return $this->buildWordCloudResponse($question_number, $region, []);
                }
            }

            $country_term_ids = null;
            if ($region !== null) {
                $country_term_ids = $this->resolveTaxonomyTermIds('countries', 'field_region', $region);
                if (empty($country_term_ids)) {
                    return $this->buildWordCloudResponse($question_number, $region, []);
                }
            }

            $survey_response_storage = $this->entityTypeManager()->getStorage('node');
            $query = $survey_response_storage->getQuery()->accessCheck(true);

            $query->condition('type', 'survey_response');
            $query->condition('status', 1);

            if ($question_term_ids !== null) {
                $query->condition('field_question.target_id', $question_term_ids, 'IN');
            }

            if ($country_term_ids !== null) {
                $query->condition('field_country.target_id', $country_term_ids, 'IN');
            }

            $survey_response_ids = $query->execute();

            if (empty($survey_response_ids)) {
                return $this->buildWordCloudResponse($question_number, $region, []);
            }

            $survey_responses = $survey_response_storage->loadMultiple($survey_response_ids);
            $term_counts = [];
            $total_occurrences = 0;

            foreach ($survey_responses as $survey_response) {
                if (!$survey_response->hasField('field_challenge')) {
                    continue;
                }

                foreach ($survey_response->get('field_challenge')->referencedEntities() as $challenge_term) {
                    $term_name = trim((string) $challenge_term->label());
                    if ($term_name === '') {
                        continue;
                    }

                    $term_counts[$term_name] = ($term_counts[$term_name] ?? 0) + 1;
                    $total_occurrences++;
                }
            }

            if ($total_occurrences === 0) {
                return $this->buildWordCloudResponse($question_number, $region, []);
            }

            arsort($term_counts);
            $terms = [];
            foreach ($term_counts as $term_name => $count) {
                $terms[] = [
                    'term' => $term_name,
                    'percent' => 100 * $count / $total_occurrences,
                    'count' => $count,
                ];
            }

            return $this->buildWordCloudResponse($question_number, $region, $terms);
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Challenge word cloud query failed: @message', ['@message' => $e->getMessage()]);

            return new JsonResponse([
                'error' => 'Failed to generate challenge word cloud',
            ], 500);
        }
    }

    /**
     * Resolves taxonomy term IDs for a vocabulary and field value.
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
    protected function resolveTaxonomyTermIds($vocabulary, $field_name, $value) {
        $taxonomy_term_storage = $this->entityTypeManager()->getStorage('taxonomy_term');
        $query = $taxonomy_term_storage->getQuery()->accessCheck(false)
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
        if ($value === null) {
            return null;
        }

        $value = trim((string) $value);
        return $value === '' ? null : $value;
    }

    /**
     * Builds endpoint response payload.
     *
     * @param string|null $question_number
     *   Echoed question number filter.
     * @param string|null $region
     *   Echoed region filter.
     * @param array $terms
     *   Terms payload.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   JSON response.
     */
    protected function buildWordCloudResponse($question_number, $region, array $terms) {
        return new JsonResponse([
        'filters' => [
        'question_number' => $question_number,
        'region' => $region,
        ],
        'terms' => $terms,
        ]);
    }
}

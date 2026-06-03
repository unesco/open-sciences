<?php

namespace Drupal\open_science_survey\Controller;

use Drupal\Core\Cache\CacheableJsonResponse;
use Drupal\Core\Cache\CacheableMetadata;
use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\Request;

/**
 * REST controller for survey questions endpoint.
 */
class SurveyQuestionsController extends ControllerBase {

    /**
     * Canonical short-code order for closed answers.
     */
    const CLOSED_ANSWER_SHORT_ORDER = ['Y', 'N', 'P', 'U', 'X'];

    /**
     * Returns survey questions for the dashboard API.
     *
     * GET /api/survey-questions?type=Closed|Open
     *
     * @param \Symfony\Component\HttpFoundation\Request $request
     *   The request object.
     *
     * @return \Drupal\Core\Cache\CacheableJsonResponse
     *   Survey questions response.
     */
    public function listSurveyQuestions(Request $request): CacheableJsonResponse {
        $question_type = $this->normalizeQuestionType($request->query->get('type'));

        $term_storage = $this->entityTypeManager()->getStorage('taxonomy_term');
        $query = $term_storage->getQuery()
            ->condition('vid', 'survey_question')
            ->condition('status', 1)
            ->sort('name', 'ASC')
            ->accessCheck(false);
        if (!$this->isAllQuestionType($question_type)) {
            $query->condition('field_question_type', $question_type);
        }
        $question_ids = $query->execute();

        if (empty($question_ids)) {
            return $this->buildResponse([]);
        }

        $questions = $term_storage->loadMultiple($question_ids);
        $section_ids = [];

        foreach ($questions as $question) {
            $section_id = (int) ($question->get('field_section')->target_id ?? 0);
            if ($section_id > 0) {
                $section_ids[$section_id] = $section_id;
            }
        }

        $sections = !empty($section_ids) ? $term_storage->loadMultiple($section_ids) : [];
        $visible_sections = [];

        foreach ($sections as $section) {
            $section_id = (int) $section->id();
            $visible_sections[$section_id] = (string) ($section->get('field_section_id')->value ?? '');
        }

        $question_id_list = array_map('intval', array_keys($questions));
        $closed_answer_definitions = $this->loadClosedAnswerDefinitions();
        $used_closed_answer_terms_by_question = $this->isClosedQuestionType($question_type)
            || $this->isAllQuestionType($question_type)
            ? $this->loadUsedClosedAnswerTermIdsByQuestion($question_id_list)
            : [];

        $data = [];
        foreach ($question_ids as $question_id) {
            if (!isset($questions[$question_id])) {
                continue;
            }

            $question = $questions[$question_id];
            $section_id = (int) ($question->get('field_section')->target_id ?? 0);

            if ($section_id <= 0 || !array_key_exists($section_id, $visible_sections)) {
                continue;
            }

            $normalized_type = (string) ($question->get('field_question_type')->value ?? '');
            $closed_answer_options = '';

            if ($this->isClosedQuestionType($normalized_type)) {
                $closed_answer_options = $this->buildClosedAnswerOptionsText(
                    (int) $question_id,
                    $used_closed_answer_terms_by_question,
                    $closed_answer_definitions
                );

                if ($closed_answer_options === '') {
                    continue;
                }
            }

            $data[] = [
                'number' => trim((string) $question->label()),
                'section' => $visible_sections[$section_id],
                'type' => $normalized_type,
                'text' => (string) ($question->get('field_question_text')->value ?? ''),
                'short_name' => (string) ($question->get('field_question_short_name')->value ?? ''),
                'description' => trim((string) $question->getDescription()),
                'long_description' => (string) ($question->get('field_question_long_description')->value ?? ''),
                'closed_answer_options' => $closed_answer_options,
            ];
        }

        return $this->buildResponse($data);
    }

    /**
     * Loads closed answer term definitions indexed by term id.
     *
     * @return array<int, array{short: string, long: string}>
     *   Closed answer definitions.
     */
    protected function loadClosedAnswerDefinitions(): array {
        $term_storage = $this->entityTypeManager()->getStorage('taxonomy_term');
        $answer_terms = $term_storage->loadByProperties(['vid' => 'survey_predefined_answers']);

        $definitions = [];
        foreach ($answer_terms as $answer_term) {
            $answer_tid = (int) $answer_term->id();
            $short_name = trim((string) ($answer_term->get('field_short_name')->value ?? ''));
            $long_name = trim((string) ($answer_term->get('field_long_name')->value ?? ''));

            if ($answer_tid <= 0 || $short_name === '' || $long_name === '') {
                continue;
            }

            $definitions[$answer_tid] = [
                'short' => $short_name,
                'long' => $long_name,
            ];
        }

        return $definitions;
    }

    /**
     * Loads used closed answer term ids grouped by question term id.
     *
     * @param array<int> $question_ids
     *   Survey question term ids.
     *
     * @return array<int, array<int, int>>
     *   Used closed answer term ids by question id.
     */
    protected function loadUsedClosedAnswerTermIdsByQuestion(array $question_ids): array {
        if (empty($question_ids)) {
            return [];
        }

        $response_storage = $this->entityTypeManager()->getStorage('node');
        $response_ids = $response_storage->getQuery()
            ->condition('type', 'survey_response')
            ->condition('status', 1)
            ->condition('field_question', $question_ids, 'IN')
            ->exists('field_closed_ans')
            ->accessCheck(false)
            ->execute();

        if (empty($response_ids)) {
            return [];
        }

        $responses = $response_storage->loadMultiple($response_ids);
        $used_answer_terms_by_question = [];

        foreach ($responses as $response) {
            $question_tid = (int) ($response->get('field_question')->target_id ?? 0);
            $answer_tid = (int) ($response->get('field_closed_ans')->target_id ?? 0);

            if ($question_tid <= 0 || $answer_tid <= 0) {
                continue;
            }

            $used_answer_terms_by_question[$question_tid][$answer_tid] = $answer_tid;
        }

        return $used_answer_terms_by_question;
    }

    /**
     * Builds closed answer options text for one question.
     *
     * @param int $question_id
     *   Survey question term id.
     * @param array<int, array<int, int>> $used_answers_by_question
     *   Used answer term ids grouped by question id.
     * @param array<int, array{short: string, long: string}> $definitions
     *   Closed answer definitions keyed by term id.
     *
     * @return string
     *   Options text in CODE|Label format joined by CRLF.
     */
    protected function buildClosedAnswerOptionsText(int $question_id, array $used_answers_by_question, array $definitions): string {
        if (!isset($used_answers_by_question[$question_id])) {
            return '';
        }

        $used_answer_tids = array_keys($used_answers_by_question[$question_id]);
        $ordered_answer_tids = $this->sortAnswerTermIdsByCanonicalOrder($used_answer_tids, $definitions);
        $lines = [];

        foreach ($ordered_answer_tids as $answer_tid) {
            if (!isset($definitions[$answer_tid])) {
                continue;
            }

            $lines[] = $definitions[$answer_tid]['short'] . '|' . $definitions[$answer_tid]['long'];
        }

        return implode("\n", $lines);
    }

    /**
     * Sorts answer term ids with canonical short-code precedence.
     *
     * @param array<int> $answer_tids
     *   Answer term ids.
     * @param array<int, array{short: string, long: string}> $definitions
     *   Closed answer definitions keyed by term id.
     *
     * @return array<int>
     *   Sorted answer term ids.
     */
    protected function sortAnswerTermIdsByCanonicalOrder(array $answer_tids, array $definitions): array {
        $order_map = array_flip(self::CLOSED_ANSWER_SHORT_ORDER);
        $unique_tids = array_values(array_unique(array_map('intval', $answer_tids)));

        usort($unique_tids, function (int $a, int $b) use ($definitions, $order_map): int {
            $short_a = strtoupper($definitions[$a]['short'] ?? '');
            $short_b = strtoupper($definitions[$b]['short'] ?? '');
            $rank_a = $order_map[$short_a] ?? PHP_INT_MAX;
            $rank_b = $order_map[$short_b] ?? PHP_INT_MAX;

            if ($rank_a !== $rank_b) {
                return $rank_a <=> $rank_b;
            }

            if ($short_a !== $short_b) {
                return strcmp($short_a, $short_b);
            }

            return $a <=> $b;
        });

        return $unique_tids;
    }

    /**
     * Normalizes question type query parameter with View-compatible fallback.
     *
     * @param string|null $question_type
     *   Raw query parameter.
     *
     * @return string
     *   The normalized question type.
     */
    protected function normalizeQuestionType(?string $question_type): string {
        if ($question_type === null || trim($question_type) === '') {
            return 'Closed';
        }

        $normalized = trim($question_type);

        if (strcasecmp($normalized, 'All') === 0) {
            return 'All';
        }

        if (strcasecmp($normalized, 'Open') === 0) {
            return 'Open';
        }

        if (strcasecmp($normalized, 'Closed') === 0) {
            return 'Closed';
        }

        return $normalized;
    }

    /**
     * Checks if question type is Closed.
     *
     * @param string $question_type
     *   Question type value.
     *
     * @return bool
     *   TRUE if Closed type.
     */
    protected function isClosedQuestionType(string $question_type): bool {
        return strcasecmp(trim($question_type), 'Closed') === 0;
    }

    /**
     * Checks if question type is All.
     *
     * @param string $question_type
     *   Question type value.
     *
     * @return bool
     *   TRUE if All type.
     */
    protected function isAllQuestionType(string $question_type): bool {
        return strcasecmp(trim($question_type), 'All') === 0;
    }

    /**
     * Builds cacheable JSON response with endpoint cache context.
     *
     * @param array $data
     *   Response rows.
     *
     * @return \Drupal\Core\Cache\CacheableJsonResponse
     *   Cacheable response object.
     */
    protected function buildResponse(array $data): CacheableJsonResponse {
        $response = new CacheableJsonResponse($data);

        $cacheability = new CacheableMetadata();
        $cacheability->setCacheContexts(['url.query_args:type']);
        $cacheability->setCacheTags(['taxonomy_term_list', 'node_list:survey_response']);
        $response->addCacheableDependency($cacheability);

        return $response;
    }

}

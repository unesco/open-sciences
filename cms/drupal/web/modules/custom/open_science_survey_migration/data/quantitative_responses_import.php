<?php

declare(strict_types=1);

/**
 * @file
 * Drush script: import quantitative responses from wide CSV into survey responses.
 *
 * Usage (from Drupal root):
 *   drush php:script web/modules/custom/open_science_survey_migration/data/quantitative_responses_import.php /path/to/quantitative_responses.csv
 */

use Drupal\Core\Entity\ContentEntityInterface;
use Drupal\taxonomy\TermInterface;

ini_set('memory_limit', '512M');
$csv_path = empty($extra[0]) ? __DIR__ . '/quantitative_responses.csv' : $extra[0];

if (!is_file($csv_path) || !is_readable($csv_path)) {
  throw new \RuntimeException("CSV file not found or not readable: {$csv_path}");
}

print "Importing $csv_path. This might take several minutes.\n";

$entity_type_manager = \Drupal::entityTypeManager();
$field_manager = \Drupal::service('entity_field.manager');

$taxonomy_storage = $entity_type_manager->getStorage('taxonomy_term');
$survey_response_storage = $entity_type_manager->getStorage('node');

$required_taxonomy_fields = [
  'survey_question' => ['name', 'field_question_type'],
  'survey_predefined_answers' => ['field_short_name'],
];

foreach ($required_taxonomy_fields as $bundle => $fields) {
  $definitions = $field_manager->getFieldDefinitions('taxonomy_term', $bundle);
  foreach ($fields as $field_name) {
    if (!isset($definitions[$field_name])) {
      throw new \RuntimeException(
        "Field '{$field_name}' does not exist on taxonomy vocabulary '{$bundle}'."
      );
    }
  }
}

$survey_response_field_definitions = $field_manager->getFieldDefinitions('node', 'survey_response');
foreach (['field_country', 'field_question', 'field_closed_ans'] as $field_name) {
  if (!isset($survey_response_field_definitions[$field_name])) {
    throw new \RuntimeException(
      "Field '{$field_name}' does not exist on node bundle 'survey_response'."
    );
  }
}

/**
 * Normalize free-text values for lookups.
 */
$normalize_text = static function (string $value): string {
  $value = str_replace("\xc2\xa0", ' ', $value);
  $value = trim($value);
  $value = preg_replace('/\s+/u', ' ', $value) ?? $value;

  if (function_exists('mb_strtolower')) {
    return mb_strtolower($value, 'UTF-8');
  }

  return strtolower($value);
};

/**
 * Normalize question number from CSV header or taxonomy field.
 */
$normalize_question_number = static function (string $value): string {
  $value = trim($value);
  $value = preg_replace('/^q\s*/i', '', $value) ?? $value;
  return $value;
};

$country_term_cache = [];
$country_term_ids = $taxonomy_storage->getQuery()
  ->accessCheck(FALSE)
  ->condition('vid', 'countries')
  ->execute();

if (!empty($country_term_ids)) {
  $country_terms = $taxonomy_storage->loadMultiple($country_term_ids);
  foreach ($country_terms as $country_term) {
    if (!$country_term instanceof TermInterface) {
      continue;
    }

    $country_name = (string) $country_term->label();
    $country_key = $normalize_text($country_name);

    if ($country_key === '') {
      continue;
    }

    if (isset($country_term_cache[$country_key])) {
      print "ERROR preload countries: duplicate key '{$country_name}'.\n";
      continue;
    }

    $country_term_cache[$country_key] = $country_term;
  }
}

$question_term_cache = [];
$question_term_ids = $taxonomy_storage->getQuery()
  ->accessCheck(FALSE)
  ->condition('vid', 'survey_question')
  ->execute();

if (!empty($question_term_ids)) {
  $question_terms = $taxonomy_storage->loadMultiple($question_term_ids);
  foreach ($question_terms as $question_term) {
    if (!$question_term instanceof TermInterface) {
      continue;
    }

    $question_number_raw = (string) $question_term->label();
    $question_number = $normalize_question_number($question_number_raw);

    if ($question_number === '') {
      continue;
    }

    if (isset($question_term_cache[$question_number])) {
      print "ERROR preload survey_question: duplicate name '{$question_number_raw}'.\n";
      continue;
    }

    $question_type = (string) $question_term->get('field_question_type')->value;
    $question_term_cache[$question_number] = [
      'term' => $question_term,
      'type' => $question_type,
    ];
  }
}

$answer_term_cache = [];
$answer_term_ids = $taxonomy_storage->getQuery()
  ->accessCheck(FALSE)
  ->condition('vid', 'survey_predefined_answers')
  ->execute();

if (!empty($answer_term_ids)) {
  $answer_terms = $taxonomy_storage->loadMultiple($answer_term_ids);
  foreach ($answer_terms as $answer_term) {
    if (!$answer_term instanceof TermInterface) {
      continue;
    }

    $short_name_raw = (string) $answer_term->get('field_short_name')->value;
    $short_name = $normalize_text($short_name_raw);

    if ($short_name === '') {
      continue;
    }

    if (isset($answer_term_cache[$short_name])) {
      print "ERROR preload survey_predefined_answers: duplicate field_short_name '{$short_name_raw}'.\n";
      continue;
    }

    $answer_term_cache[$short_name] = $answer_term;
    if ($short_name === 'x') {
      $answer_term_cache['n/a'] = $answer_term;
    }
  }
}

$handle = fopen($csv_path, 'r');
if ($handle === FALSE) {
  throw new \RuntimeException("Unable to open CSV file: {$csv_path}");
}

if (fgets($handle, 4) !== "\xef\xbb\xbf") {
  rewind($handle);
}

$headers = fgetcsv($handle);
if ($headers === FALSE) {
  fclose($handle);
  throw new \RuntimeException('CSV is empty.');
}

$headers = array_map(
  static function ($header): string {
    return trim((string) $header);
  },
  $headers
);

$country_column_index = NULL;
$valid_question_columns = [];
$ignored_section_columns = [];
$errors = 0;

foreach ($headers as $column_index => $header) {
  $header = trim($header);
  $normalized_header = $normalize_text($header);

  if ($normalized_header === 'country') {
    $country_column_index = $column_index;
    continue;
  }

  if (preg_match('/^section\b/i', $header) === 1) {
    $ignored_section_columns[] = $column_index;
    continue;
  }

  if (preg_match('/^q\s*([0-9]+(?:\.[0-9]+)*)\b/i', $header, $matches) !== 1) {
    $errors++;
    print "ERROR header '{$header}': unable to parse question number.\n";
    continue;
  }

  $question_number = $normalize_question_number((string) $matches[1]);
  if (!isset($question_term_cache[$question_number])) {
    $errors++;
    print "ERROR header '{$header}': no survey_question term found for question number '{$question_number}'.\n";
    continue;
  }

  $question_meta = $question_term_cache[$question_number];
  $question_type = $normalize_text((string) $question_meta['type']);
  if ($question_type !== 'closed') {
    $errors++;
    print "ERROR header '{$header}': question '{$question_number}' is type '{$question_meta['type']}', expected Closed.\n";
    continue;
  }

  $valid_question_columns[$column_index] = [
    'header' => $header,
    'question_number' => $question_number,
    'question_term_id' => (int) $question_meta['term']->id(),
  ];
}

if ($country_column_index === NULL) {
  fclose($handle);
  throw new \RuntimeException("CSV missing required 'Country' column.");
}

if (empty($valid_question_columns)) {
  fclose($handle);
  throw new \RuntimeException('CSV contains no valid question columns to import.');
}

$response_cache = [];

/**
 * Get survey_response entities by country+question with in-request caching.
 */
$load_responses = static function (int $country_term_id, int $question_term_id) use (
  &$response_cache,
  $survey_response_storage
): array {
  $cache_key = $country_term_id . ':' . $question_term_id;
  if (array_key_exists($cache_key, $response_cache)) {
    return $response_cache[$cache_key];
  }

  $ids = $survey_response_storage->getQuery()
    ->accessCheck(FALSE)
    ->condition('type', 'survey_response')
    ->condition('field_country.target_id', $country_term_id)
    ->condition('field_question.target_id', $question_term_id)
    ->execute();

  if (empty($ids)) {
    $response_cache[$cache_key] = [];
    return [];
  }

  $entities = $survey_response_storage->loadMultiple($ids);
  $response_cache[$cache_key] = $entities;
  return $entities;
};

$processed_rows = 0;
$skipped_rows = 0;
$processed_cells = 0;
$created_responses = 0;
$updated_responses = 0;
$skipped_cells = 0;
$line_number = 1;

while (($row = fgetcsv($handle)) !== FALSE) {
  $line_number++;

  if ($row === [NULL] || $row === []) {
    continue;
  }

  if (count($row) < count($headers)) {
    $row = array_pad($row, count($headers), '');
  }

  $processed_rows++;

  $country_value = trim((string) ($row[$country_column_index] ?? ''));
  if ($country_value === '') {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: Country is required.\n";
    continue;
  }

  $country_key = $normalize_text($country_value);
  if (!isset($country_term_cache[$country_key])) {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: no countries term found for Country '{$country_value}'.\n";
    continue;
  }

  $country_term = $country_term_cache[$country_key];
  $country_term_id = (int) $country_term->id();

  foreach ($valid_question_columns as $column_index => $column_meta) {
    $raw_value = trim((string) ($row[$column_index] ?? ''));
    if ($raw_value === '') {
      $skipped_cells++;
      continue;
    }

    $processed_cells++;

    $answer_key = $normalize_text($raw_value);
    if (!isset($answer_term_cache[$answer_key])) {
      $errors++;
      $skipped_cells++;
      print "ERROR line {$line_number}: no survey_predefined_answers term found for value '{$raw_value}' in '{$column_meta['header']}'.\n";
      continue;
    }

    $answer_term_id = (int) $answer_term_cache[$answer_key]->id();
    $question_term_id = (int) $column_meta['question_term_id'];

    try {
      $responses = $load_responses($country_term_id, $question_term_id);
      if (empty($responses)) {
        $response = $survey_response_storage->create([
          'type' => 'survey_response',
          'title' => sprintf('%s - Q%s', $country_value, $column_meta['question_number']),
          'field_country' => ['target_id' => $country_term_id],
          'field_question' => ['target_id' => $question_term_id],
          'field_closed_ans' => ['target_id' => $answer_term_id],
        ]);

        if (!$response instanceof ContentEntityInterface) {
          throw new \RuntimeException('Created survey_response node has unexpected type.');
        }

        $response->save();

        $cache_key = $country_term_id . ':' . $question_term_id;
        $response_cache[$cache_key] = [$response->id() => $response];
        $created_responses++;
        continue;
      }

      foreach ($responses as $response) {
        if (!$response instanceof ContentEntityInterface) {
          continue;
        }

        $current_target_id = (int) ($response->get('field_closed_ans')->target_id ?? 0);
        if ($current_target_id === $answer_term_id) {
          continue;
        }

        $response->set('field_closed_ans', ['target_id' => $answer_term_id]);
        $response->save();
        $updated_responses++;
      }
    }
    catch (\Throwable $e) {
      $errors++;
      $skipped_cells++;
      print "ERROR line {$line_number}: failed importing Country '{$country_value}' question '{$column_meta['question_number']}': {$e->getMessage()}\n";
    }
  }
}

fclose($handle);

print "Done.\n";
print "  CSV: {$csv_path}\n";
print "  Processed rows: {$processed_rows}\n";
print "  Skipped rows: {$skipped_rows}\n";
print "  Processed cells: {$processed_cells}\n";
print "  Skipped cells: {$skipped_cells}\n";
print "  Responses created: {$created_responses}\n";
print "  Responses updated: {$updated_responses}\n";
print "  Ignored section columns: " . count($ignored_section_columns) . "\n";
print "  Valid question columns: " . count($valid_question_columns) . "\n";
print "  Errors: {$errors}\n";

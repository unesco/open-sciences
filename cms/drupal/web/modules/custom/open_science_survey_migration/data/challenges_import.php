<?php

declare(strict_types=1);

/**
 * @file
 * Drush script: import challenges from CSV into taxonomy and survey responses.
 *
 * Usage (from Drupal root):
 *   drush php:script web/modules/custom/open_science_survey_migration/data/challanges_import_chat.php /path/to/challenges.csv
 */

use Drupal\taxonomy\Entity\Term;
use Drupal\taxonomy\TermInterface;

$csv_path = empty($extra[0]) ? __DIR__ . '/challenges.csv' : $extra[0];

if (!is_file($csv_path) || !is_readable($csv_path)) {
  throw new \RuntimeException("CSV file not found or not readable: {$csv_path}");
}

print "Importing $csv_path. This might take several minutes.\n";

$entity_type_manager = \Drupal::entityTypeManager();
$field_manager = \Drupal::service('entity_field.manager');

$taxonomy_storage = $entity_type_manager->getStorage('taxonomy_term');
$survey_response_storage = $entity_type_manager->getStorage('node');

$required_taxonomy_fields = [
  'countries' => ['field_iso_alpha3_code'],
  'survey_question' => ['name'],
  'challenges' => ['field_snippet'],
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
foreach (['field_country', 'field_question', 'field_challenge'] as $field_name) {
  if (!isset($survey_response_field_definitions[$field_name])) {
    throw new \RuntimeException(
      "Field '{$field_name}' does not exist on node bundle 'survey_response'."
    );
  }
}

/**
 * Normalize text values for matching and deduplication.
 */
$normalize_text = static function (string $value): string {
  $value = trim($value);
  $value = preg_replace('/\s+/', ' ', $value) ?? $value;
  return strtolower($value);
};

/**
 * Build in-memory map of existing challenge terms keyed by normalized name.
 */
$challenge_terms_by_name = [];
$challenge_term_ids = $taxonomy_storage->getQuery()
  ->accessCheck(FALSE)
  ->condition('vid', 'challenges')
  ->execute();

if (!empty($challenge_term_ids)) {
  $challenge_terms = $taxonomy_storage->loadMultiple($challenge_term_ids);
  foreach ($challenge_terms as $challenge_term) {
    if (!$challenge_term instanceof TermInterface) {
      continue;
    }
    $key = $normalize_text($challenge_term->label());
    if ($key !== '') {
      $challenge_terms_by_name[$key] = $challenge_term;
    }
  }
}

$country_term_cache = [];
$question_term_cache = [];

/**
 * Load country term by ISO code with in-request caching.
 */
$load_country_term = static function (string $iso_code) use (
  &$country_term_cache,
  $taxonomy_storage
): ?TermInterface {
  if (isset($country_term_cache[$iso_code])) {
    return $country_term_cache[$iso_code];
  }

  $ids = $taxonomy_storage->getQuery()
    ->accessCheck(FALSE)
    ->condition('vid', 'countries')
    ->condition('field_iso_alpha3_code', $iso_code)
    ->range(0, 1)
    ->execute();

  if (empty($ids)) {
    $country_term_cache[$iso_code] = NULL;
    return NULL;
  }

  $terms = $taxonomy_storage->loadMultiple($ids);
  $term = reset($terms);
  $country_term_cache[$iso_code] = ($term instanceof TermInterface) ? $term : NULL;
  return $country_term_cache[$iso_code];
};

/**
 * Load question term by question number with in-request caching.
 */
$load_question_term = static function (string $question_number) use (
  &$question_term_cache,
  $taxonomy_storage
): ?TermInterface {
  if (isset($question_term_cache[$question_number])) {
    return $question_term_cache[$question_number];
  }

  $ids = $taxonomy_storage->getQuery()
    ->accessCheck(FALSE)
    ->condition('vid', 'survey_question')
    ->condition('name', $question_number)
    ->range(0, 1)
    ->execute();

  if (empty($ids)) {
    $question_term_cache[$question_number] = NULL;
    return NULL;
  }

  $terms = $taxonomy_storage->loadMultiple($ids);
  $term = reset($terms);
  $question_term_cache[$question_number] = ($term instanceof TermInterface) ? $term : NULL;
  return $question_term_cache[$question_number];
};

$processed_rows = 0;
$terms_created = 0;
$terms_updated = 0;
$responses_updated = 0;
$skipped_rows = 0;
$errors = 0;

$handle = fopen($csv_path, 'r');
if ($handle === FALSE) {
  throw new \RuntimeException("Unable to open CSV file: {$csv_path}");
}

// Skip BOM marker if present.
if (fgets($handle, 4) !== "\xef\xbb\xbf") {
  rewind($handle);
}

$headers = fgetcsv($handle);
if ($headers === FALSE) {
  fclose($handle);
  throw new \RuntimeException('CSV is empty.');
}

$headers = array_map('trim', $headers);
$required_headers = ['challenge_name', 'country', 'question_number', 'snippet'];
foreach ($required_headers as $required_header) {
  if (!in_array($required_header, $headers, TRUE)) {
    fclose($handle);
    throw new \RuntimeException("CSV missing required column: {$required_header}");
  }
}

$line_number = 1;
while (($row = fgetcsv($handle)) !== FALSE) {
  $line_number++;

  if ($row === [NULL] || $row === []) {
    continue;
  }

  if (count($row) < count($headers)) {
    $row = array_pad($row, count($headers), '');
  }

  $record = array_combine($headers, array_slice($row, 0, count($headers)));
  if ($record === FALSE) {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: unable to parse row.\n";
    continue;
  }

  $challenge_name = trim((string) ($record['challenge_name'] ?? ''));
  $country_iso = strtoupper(trim((string) ($record['country'] ?? '')));
  $question_number = trim((string) ($record['question_number'] ?? ''));
  $snippet = trim((string) ($record['snippet'] ?? ''));

  if ($challenge_name === '' || $country_iso === '' || $question_number === '') {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: challenge_name, country and question_number are required.\n";
    continue;
  }

  $processed_rows++;

  $challenge_key = $normalize_text($challenge_name);
  if ($challenge_key === '') {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: normalized challenge_name is empty.\n";
    continue;
  }

  $term_created = FALSE;
  $term_changed = FALSE;

  if (!isset($challenge_terms_by_name[$challenge_key])) {
    $challenge_term = Term::create([
      'vid' => 'challenges',
      'name' => $challenge_name,
    ]);
    $term_created = TRUE;
    $term_changed = TRUE;
  }
  else {
    $challenge_term = $challenge_terms_by_name[$challenge_key];
  }

  $existing_snippets = $challenge_term->get('field_snippet')->getValue();
  $existing_snippet_values = [];
  $snippet_index = [];

  foreach ($existing_snippets as $item) {
    $value = trim((string) ($item['value'] ?? ''));
    if ($value === '') {
      continue;
    }
    $existing_snippet_values[] = ['value' => $value];
    $snippet_index[$normalize_text($value)] = TRUE;
  }

  if ($snippet !== '') {
    $snippet_key = $normalize_text($snippet);
    if (!isset($snippet_index[$snippet_key])) {
      $existing_snippet_values[] = ['value' => $snippet];
      $term_changed = TRUE;
    }
  }

  try {
    if ($term_changed) {
      $challenge_term->set('field_snippet', $existing_snippet_values);
      $challenge_term->save();

      if ($term_created) {
        $terms_created++;
      }
      else {
        $terms_updated++;
      }

      $challenge_terms_by_name[$challenge_key] = $challenge_term;
    }
  }
  catch (\Throwable $e) {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: failed saving challenge term '{$challenge_name}': {$e->getMessage()}\n";
    continue;
  }

  $country_term = $load_country_term($country_iso);
  if (!$country_term) {
    $skipped_rows++;
    print "SKIP line {$line_number}: no countries term found for country '{$country_iso}'.\n";
    continue;
  }

  $question_term = $load_question_term($question_number);
  if (!$question_term) {
    $skipped_rows++;
    print "SKIP line {$line_number}: no survey_question term found for question_number '{$question_number}'.\n";
    continue;
  }

  $survey_response_ids = $survey_response_storage->getQuery()
    ->accessCheck(FALSE)
    ->condition('type', 'survey_response')
    ->condition('field_country.target_id', (int) $country_term->id())
    ->condition('field_question.target_id', (int) $question_term->id())
    ->execute();

  if (empty($survey_response_ids)) {
    $skipped_rows++;
    print "SKIP line {$line_number}: no survey_response found for country '{$country_iso}' and question_number '{$question_number}'.\n";
    continue;
  }

  $survey_responses = $survey_response_storage->loadMultiple($survey_response_ids);
  foreach ($survey_responses as $survey_response) {
    $current_values = $survey_response->get('field_challenge')->getValue();
    $current_ids = [];

    foreach ($current_values as $current_value) {
      if (isset($current_value['target_id'])) {
        $current_ids[] = (int) $current_value['target_id'];
      }
    }

    $challenge_id = (int) $challenge_term->id();
    if (in_array($challenge_id, $current_ids, TRUE)) {
      continue;
    }

    $current_values[] = ['target_id' => $challenge_id];

    try {
      $survey_response->set('field_challenge', $current_values);
      $survey_response->save();
      $responses_updated++;
    }
    catch (\Throwable $e) {
      $errors++;
      print "ERROR line {$line_number}: failed saving survey_response {$survey_response->id()}: {$e->getMessage()}\n";
    }
  }
}

fclose($handle);

print "Done.\n";
print "  CSV: {$csv_path}\n";
print "  Rows processed: {$processed_rows}\n";
print "  Terms created: {$terms_created}\n";
print "  Terms updated: {$terms_updated}\n";
print "  Survey responses updated: {$responses_updated}\n";
print "  Rows skipped: {$skipped_rows}\n";
print "  Errors: {$errors}\n";

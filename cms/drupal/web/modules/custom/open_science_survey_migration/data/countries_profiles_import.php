<?php

declare(strict_types=1);

/**
 * @file
 * Drush script: import countries profile summaries from CSV into Countries terms.
 *
 * Usage (from Drupal root):
 *   drush php:script web/modules/custom/open_science_survey_migration/data/import_countries_profiles.php /path/to/countries_profiles.csv
 */

use Drupal\taxonomy\TermInterface;

$csv_path = empty($extra[0]) ? __DIR__ . '/countries_profiles.csv' : $extra[0];

if (!is_file($csv_path) || !is_readable($csv_path)) {
  throw new \RuntimeException("CSV file not found or not readable: {$csv_path}");
}

$entity_type_manager = \Drupal::entityTypeManager();
$field_manager = \Drupal::service('entity_field.manager');
$taxonomy_storage = $entity_type_manager->getStorage('taxonomy_term');

$vocabulary = 'countries';
$country_iso_field = 'field_iso_alpha3_code';

$section_to_field = [
  '1' => 'field_info_promoting',
  '2' => 'field_info_policy',
  '3' => 'field_info_funding_infra',
  '4' => 'field_info_funding_training',
  '5' => 'field_info_promote_culture',
  '6' => 'field_info_promote_inovation',
  '7' => 'field_info_promote_cooperation',
];

$bundle_field_definitions = $field_manager->getFieldDefinitions('taxonomy_term', $vocabulary);
$required_term_fields = array_values($section_to_field);
$required_term_fields[] = $country_iso_field;

foreach ($required_term_fields as $required_term_field) {
  if (!isset($bundle_field_definitions[$required_term_field])) {
    throw new \RuntimeException(
      "Field '{$required_term_field}' does not exist on taxonomy vocabulary '{$vocabulary}'."
    );
  }
}

/**
 * Load countries term by ISO alpha-3 code.
 */
$load_country_term = static function (string $iso_code) use (
  $taxonomy_storage,
  $vocabulary,
  $country_iso_field
): ?TermInterface {
  $ids = $taxonomy_storage->getQuery()
    ->accessCheck(FALSE)
    ->condition('vid', $vocabulary)
    ->condition($country_iso_field, strtoupper($iso_code))
    ->range(0, 1)
    ->execute();

  if (empty($ids)) {
    return NULL;
  }

  $terms = $taxonomy_storage->loadMultiple($ids);
  return reset($terms) ?: NULL;
};

$updated_rows = 0;
$skipped_rows = 0;
$errors = 0;

$handle = fopen($csv_path, 'r');
if ($handle === FALSE) {
  throw new \RuntimeException("Unable to open CSV file: {$csv_path}");
}

// Skip BOM marker if present
if (fgets($handle, 4) !== "\xef\xbb\xbf") {
    rewind($handle);
}

$headers = fgetcsv($handle);
if ($headers === FALSE) {
  fclose($handle);
  throw new \RuntimeException('CSV is empty.');
}

$headers = array_map('trim', $headers);
$required_headers = ['Country Code', 'Survey Section ID', 'Summary'];
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

  $iso_code = strtoupper(trim((string) ($record['Country Code'] ?? '')));
  $section_id = trim((string) ($record['Survey Section ID'] ?? ''));
  $summary = (string) ($record['Summary'] ?? '');

  if ($iso_code === '' || $section_id === '') {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: Country Code and Survey Section ID are required.\n";
    continue;
  }

  if (!isset($section_to_field[$section_id])) {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: unmapped Survey Section ID '{$section_id}'.\n";
    continue;
  }

  $term = $load_country_term($iso_code);
  if (!$term) {
    $skipped_rows++;
    print "SKIP line {$line_number}: no countries term found for Country Code '{$iso_code}'.\n";
    continue;
  }

  $target_field = $section_to_field[$section_id];
  $decoded_summary = html_entity_decode($summary, ENT_QUOTES | ENT_HTML5, 'UTF-8');

  try {
    $term->set($target_field, [
        'value' => $decoded_summary,
        'format' => 'basic_html',
    ]);
    $term->save();
    $updated_rows++;
  }
  catch (\Throwable $e) {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: failed saving term '{$iso_code}' field '{$target_field}': {$e->getMessage()}\n";
  }
}

fclose($handle);

print "Done.\n";
print "  CSV: {$csv_path}\n";
print "  Rows updated: {$updated_rows}\n";
print "  Rows skipped: {$skipped_rows}\n";
print "  Errors: {$errors}\n";

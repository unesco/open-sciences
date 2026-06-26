<?php

declare(strict_types=1);

/**
 * @file
 * Drush script: import countries profile summaries from CSV into Survey reports.
 *
 * Usage (from Drupal root):
 *   drush php:script web/modules/custom/open_science_survey_migration/data/import_countries_profiles.php /path/to/countries_profiles.csv
 */

use Drupal\taxonomy\TermInterface;
use Drupal\node\NodeInterface;
use Drupal\file\Entity\File;
use Drupal\Core\File\FileSystemInterface;

$csv_path = empty($extra[0]) ? __DIR__ . '/countries_profiles.csv' : $extra[0];

if (!is_file($csv_path) || !is_readable($csv_path)) {
  throw new \RuntimeException("CSV file not found or not readable: {$csv_path}");
}

print "Importing $csv_path. This might take several minutes.\n";

$entity_type_manager = \Drupal::entityTypeManager();
$field_manager = \Drupal::service('entity_field.manager');
$file_system = \Drupal::service('file_system');
$renderer = \Drupal::service('renderer');
$taxonomy_storage = $entity_type_manager->getStorage('taxonomy_term');
$node_storage = $entity_type_manager->getStorage('node');
$file_storage = $entity_type_manager->getStorage('file');

$vocabulary = 'countries';
$country_iso_field = 'field_iso_alpha3_code';
$report_bundle = 'survey_report';
$report_year_field = 'field_year';
$report_country_field = 'field_country';
$report_file_field = 'field_report_file';
$report_files_source_dir = __DIR__ . '/reports';
$default_report_year = 2025;

$section_to_field = [
  '1' => 'field_info_promoting',
  '2' => 'field_info_policy',
  '3' => 'field_info_funding_infra',
  '4' => 'field_info_funding_training',
  '5' => 'field_info_promote_culture',
  '6' => 'field_info_promote_inovation',
  '7' => 'field_info_promote_cooperation',
];

$term_field_definitions = $field_manager->getFieldDefinitions('taxonomy_term', $vocabulary);
$report_field_definitions = $field_manager->getFieldDefinitions('node', $report_bundle);
$required_term_fields = [$country_iso_field];
$required_report_fields = array_values($section_to_field);
$required_report_fields[] = $report_country_field;
$required_report_fields[] = $report_year_field;
$required_report_fields[] = $report_file_field;

foreach ($required_term_fields as $required_term_field) {
  if (!isset($term_field_definitions[$required_term_field])) {
    throw new \RuntimeException(
      "Field '{$required_term_field}' does not exist on taxonomy vocabulary '{$vocabulary}'."
    );
  }
}

foreach ($required_report_fields as $required_report_field) {
  if (!isset($report_field_definitions[$required_report_field])) {
    throw new \RuntimeException(
      "Field '{$required_report_field}' does not exist on node bundle '{$report_bundle}'."
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

$report_cache = [];

/**
 * Load or create the managed PDF file entity for a country report.
 */
$load_country_report_file = static function (string $iso_code) use (
  $report_files_source_dir,
  $file_system,
  $file_storage
): ?File {
  $filename = strtoupper($iso_code) . '.pdf';
  $source_path = $report_files_source_dir . '/' . $filename;

  if (!is_file($source_path) || !is_readable($source_path)) {
    return NULL;
  }

  $destination_directory = 'public://survey_reports';
  $prepared = $file_system->prepareDirectory(
    $destination_directory,
    FileSystemInterface::CREATE_DIRECTORY | FileSystemInterface::MODIFY_PERMISSIONS
  );
  if (!$prepared) {
    throw new \RuntimeException("Unable to prepare destination directory: {$destination_directory}");
  }

  $destination_uri = $destination_directory . '/' . $filename;
  $file_system->copy($source_path, $destination_uri, FileSystemInterface::EXISTS_REPLACE);

  $existing_files = $file_storage->loadByProperties(['uri' => $destination_uri]);
  $file = reset($existing_files);

  if (!$file instanceof File) {
    $file = File::create([
      'uri' => $destination_uri,
      'filename' => $filename,
      'status' => 1,
    ]);
  }
  else {
    $file->setFilename($filename);
  }

  $file->setPermanent();
  $file->save();

  return $file;
};

/**
 * Load or create the survey report node for a country.
 */
$load_country_report = static function (TermInterface $country_term) use (
  &$report_cache,
  $node_storage,
  $report_bundle,
  $report_country_field,
  $report_year_field,
  $default_report_year
): NodeInterface {
  $country_term_id = (int) $country_term->id();

  if (isset($report_cache[$country_term_id])) {
    return $report_cache[$country_term_id];
  }

  $ids = $node_storage->getQuery()
    ->accessCheck(FALSE)
    ->condition('type', $report_bundle)
    ->condition("{$report_country_field}.target_id", $country_term_id)
    ->condition($report_year_field, $default_report_year)
    ->range(0, 1)
    ->execute();

  if (!empty($ids)) {
    $reports = $node_storage->loadMultiple($ids);
    $report = reset($reports);
    if ($report instanceof NodeInterface) {
      $report_cache[$country_term_id] = $report;
      return $report;
    }
  }

  $report = $node_storage->create([
    'type' => $report_bundle,
    $report_country_field => ['target_id' => $country_term_id],
    $report_year_field => $default_report_year,
    'status' => 1,
  ]);

  $report_cache[$country_term_id] = $report;
  return $report;
};

/**
 * Remove empty HTML blocks and redundant line breaks from imported summaries.
 */
$normalize_summary_html = static function (string $summary) use ($renderer): string {
  $summary = str_replace(["<div", "</div>"], ['<p', '</p>'], $summary);
  $summary = str_replace(["\r\n", "\r", "\n", '&nbsp;'], ' ', $summary);
  $summary = html_entity_decode($summary, ENT_QUOTES | ENT_HTML5, 'UTF-8');
  $processed_text = [
    '#type' => 'processed_text',
    '#text' => $summary,
    '#format' => 'basic_html',
  ];
  $summary = (string) $renderer->renderInIsolation($processed_text);
  $summary = str_replace(["\r\n", "\r", "\n", '&nbsp;'], ' ', $summary);

  $patterns = [
    '/(?:<br>\s*){2,}/iu' => '<p>',
    '/<p>(?:\s|<br>)*<\/p>/iu' => '',
    '/(<p>\s*)((?:<br>\s*)+)/iu' => '$1',
    '/(<p>.*?)((?:\s*<br>)+)(\s*<\/p>)/iu' => '$1$3',
    '/<\/p>\s*(?:<br>\s*)+(?=<p>|$)/iu' => '</p>',
    '/\A(?:\s*<br>\s*)+/iu' => '',
    '/(?:\s*<br>\s*)+\z/iu' => '',
  ];

  foreach ($patterns as $pattern => $replacement) {
    $summary = preg_replace($pattern, $replacement, $summary) ?? $summary;
  }

  return trim($summary);
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
  $decoded_summary = $normalize_summary_html($summary);
  $report = $load_country_report($term);

  try {
    $report->set($target_field, [
      'value' => $decoded_summary,
      'format' => 'basic_html',
    ]);

    $report_file = $load_country_report_file($iso_code);
    if ($report_file instanceof File) {
      $report->set($report_file_field, [
        'target_id' => (int) $report_file->id(),
      ]);
    }

    $report->save();
    $updated_rows++;
  }
  catch (\Throwable $e) {
    $errors++;
    $skipped_rows++;
    print "ERROR line {$line_number}: failed saving survey report '{$iso_code}' field '{$target_field}': {$e->getMessage()}\n";
  }
}

fclose($handle);

print "Done.\n";
print "  CSV: {$csv_path}\n";
print "  Rows updated: {$updated_rows}\n";
print "  Rows skipped: {$skipped_rows}\n";
print "  Errors: {$errors}\n";

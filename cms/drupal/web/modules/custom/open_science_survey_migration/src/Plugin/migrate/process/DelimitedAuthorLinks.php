<?php

namespace Drupal\open_science_survey_migration\Plugin\migrate\process;

use Drupal\migrate\Attribute\MigrateProcess;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;
use Drupal\paragraphs\Entity\Paragraph;

#[MigrateProcess('delimited_author_links')]
final class DelimitedAuthorLinks extends ProcessPluginBase {

  public function transform($value, MigrateExecutableInterface $migrate_executable, Row $row, $destination_property): array {
    $delimiter = $this->configuration['delimiter'] ?? ',';
    $trim = $this->configuration['trim'] ?? TRUE;
    $fallback_uri = $this->configuration['fallback_uri'] ?? 'route:<nolink>';

    $authors_raw = '';
    $links_raw = '';
    $orcids_raw = '';
    if (is_array($value)) {
      $authors_raw = (string) ($value[0] ?? '');
      $links_raw = (string) ($value[1] ?? '');
      $orcids_raw = (string) ($value[2] ?? '');
    }
    elseif ($value !== NULL) {
      $authors_raw = (string) $value;
    }

    $authors = $authors_raw === '' ? [] : explode($delimiter, $authors_raw);
    $links = $links_raw === '' ? [] : explode($delimiter, $links_raw);
    $orcids = $orcids_raw === '' ? [] : explode($delimiter, $orcids_raw);

    $items = [];
    foreach ($authors as $index => $author) {
      $title = (string) $author;
      if ($trim) {
        $title = trim($title);
      }

      if ($title === '') {
        continue;
      }

      $uri = (string) ($links[$index] ?? '');
      if ($trim) {
        $uri = trim($uri);
      }
      if ($uri === '') {
        $uri = $fallback_uri;
      }

      $orcid = (string) ($orcids[$index] ?? '');
      if ($trim) {
        $orcid = trim($orcid);
      }

      $paragraph_values = [
        'type' => 'author',
        'field_full_name' => $title,
        'field_url' => ['uri' => $uri],
      ];
      if ($orcid !== '') {
        $paragraph_values['field_orcid'] = $orcid;
      }

      $paragraph = Paragraph::create($paragraph_values);
      $paragraph->save();

      $items[] = [
        'target_id' => (int) $paragraph->id(),
        'target_revision_id' => (int) $paragraph->getRevisionId(),
      ];
    }

    return $items;
  }

}

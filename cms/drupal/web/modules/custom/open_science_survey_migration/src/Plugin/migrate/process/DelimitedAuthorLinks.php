<?php

namespace Drupal\open_science_survey_migration\Plugin\migrate\process;

use Drupal\migrate\Attribute\MigrateProcess;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;

#[MigrateProcess('delimited_author_links')]
final class DelimitedAuthorLinks extends ProcessPluginBase {

  public function transform($value, MigrateExecutableInterface $migrate_executable, Row $row, $destination_property): array {
    $delimiter = $this->configuration['delimiter'] ?? ',';
    $trim = $this->configuration['trim'] ?? TRUE;
    $fallback_uri = $this->configuration['fallback_uri'] ?? 'route:<nolink>';

    $authors_raw = '';
    $links_raw = '';
    if (is_array($value)) {
      $authors_raw = (string) ($value[0] ?? '');
      $links_raw = (string) ($value[1] ?? '');
    }
    elseif ($value !== NULL) {
      $authors_raw = (string) $value;
    }

    $authors = $authors_raw === '' ? [] : explode($delimiter, $authors_raw);
    $links = $links_raw === '' ? [] : explode($delimiter, $links_raw);

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

      $items[] = [
        'uri' => $uri,
        'title' => $title,
      ];
    }

    return $items;
  }

}

<?php

namespace Drupal\open_science_survey_migration\Plugin\migrate\process;

use Drupal\migrate\Attribute\MigrateProcess;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;

#[MigrateProcess('delimited_links')]
final class DelimitedLinks extends ProcessPluginBase {

  public function transform($value, MigrateExecutableInterface $migrate_executable, Row $row, $destination_property): array {
    $trim = $this->configuration['trim'] ?? TRUE;

    $titles_raw = '';
    $links_raw = '';
    if (is_array($value)) {
      $titles_raw = (string) ($value[0] ?? '');
      $links_raw = (string) ($value[1] ?? '');
    }
    elseif ($value !== NULL) {
      $titles_raw = (string) $value;
    }

    // Split on commas not preceded by a backslash.
    $split = static fn(string $s): array => $s === '' ? [] : preg_split('/(?<!\\\\),/', $s);
    $unescape = static fn(string $s): string => str_replace('\,', ',', $s);

    $titles = $split($titles_raw);
    $links = $split($links_raw);

    $items = [];
    $count = max(count($titles), count($links));
    for ($i = 0; $i < $count; $i++) {
      $title = $unescape($trim ? trim((string) ($titles[$i] ?? '')) : (string) ($titles[$i] ?? ''));
      $uri = $unescape($trim ? trim((string) ($links[$i] ?? '')) : (string) ($links[$i] ?? ''));

      if ($uri === '' && $title === '') {
        continue;
      }

      $items[] = ['uri' => $uri, 'title' => $title];
    }

    return $items;
  }

}

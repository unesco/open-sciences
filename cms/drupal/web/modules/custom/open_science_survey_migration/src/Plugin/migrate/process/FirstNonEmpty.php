<?php

namespace Drupal\open_science_survey_migration\Plugin\migrate\process;

use Drupal\migrate\Attribute\MigrateProcess;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;

#[MigrateProcess('first_non_empty')]
final class FirstNonEmpty extends ProcessPluginBase {

  public function transform($value, MigrateExecutableInterface $migrate_executable, Row $row, $destination_property): string {
    $candidates = is_array($value) ? $value : [$value];

    foreach ($candidates as $candidate) {
      if ($candidate === NULL) {
        continue;
      }

      $string_value = is_scalar($candidate) ? trim((string) $candidate) : '';
      if ($string_value !== '') {
        return $string_value;
      }
    }

    return '';
  }

}

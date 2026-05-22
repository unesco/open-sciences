<?php

namespace Drupal\open_science_survey_migration\Plugin\migrate\process;

use Drupal\Core\Entity\EntityInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\migrate\Attribute\MigrateProcess;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\MigrateException;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;
use Symfony\Component\DependencyInjection\ContainerInterface;

#[MigrateProcess('delimited_entity_reference')]
final class DelimitedEntityReference extends ProcessPluginBase implements ContainerFactoryPluginInterface {

  public function __construct(array $configuration, $plugin_id, $plugin_definition, private readonly EntityTypeManagerInterface $entityTypeManager) {
    parent::__construct($configuration, $plugin_id, $plugin_definition);
  }

  public static function create(ContainerInterface $container, array $configuration, $plugin_id, $plugin_definition): static {
    return new static(
      $configuration,
      $plugin_id,
      $plugin_definition,
      $container->get('entity_type.manager')
    );
  }

  public function transform($value, MigrateExecutableInterface $migrate_executable, Row $row, $destination_property): array {
    $entity_type = $this->configuration['entity_type'] ?? NULL;
    $value_key = $this->configuration['value_key'] ?? NULL;

    if (!$entity_type || !$value_key) {
      throw new MigrateException('The delimited_entity_reference process plugin requires entity_type and value_key configuration.');
    }

    if ($value === NULL || $value === '') {
      return [];
    }

    $items = is_array($value)
      ? $value
      : explode($this->configuration['delimiter'] ?? ',', (string) $value);

    $references = [];
    foreach ($items as $item) {
      $lookup_value = (string) $item;
      if (($this->configuration['trim'] ?? TRUE) === TRUE) {
        $lookup_value = trim($lookup_value);
      }

      if ($lookup_value === '') {
        continue;
      }

      $entity = $this->loadEntity($entity_type, $value_key, $lookup_value);
      if (!$entity && !empty($this->configuration['autocreate'])) {
        $entity = $this->createEntity($entity_type, $value_key, $lookup_value);
      }

      if ($entity) {
        $references[] = ['target_id' => $entity->id()];
      }
    }

    return $references;
  }

  private function loadEntity(string $entity_type, string $value_key, string $lookup_value): ?EntityInterface {
    $storage = $this->entityTypeManager->getStorage($entity_type);
    $properties = [$value_key => $lookup_value];

    $bundle = $this->configuration['bundle'] ?? NULL;
    $bundle_key = $this->configuration['bundle_key'] ?? $storage->getEntityType()->getKey('bundle');
    if ($bundle && $bundle_key) {
      $properties[$bundle_key] = $bundle;
    }

    $entities = $storage->loadByProperties($properties);
    if (!$entities) {
      return NULL;
    }

    return reset($entities) ?: NULL;
  }

  private function createEntity(string $entity_type, string $value_key, string $lookup_value): EntityInterface {
    $storage = $this->entityTypeManager->getStorage($entity_type);
    $values = [$value_key => $lookup_value];

    $bundle = $this->configuration['bundle'] ?? NULL;
    $bundle_key = $this->configuration['bundle_key'] ?? $storage->getEntityType()->getKey('bundle');
    if ($bundle && $bundle_key) {
      $values[$bundle_key] = $bundle;
    }

    $entity = $storage->create($values);
    $entity->save();

    return $entity;
  }

}

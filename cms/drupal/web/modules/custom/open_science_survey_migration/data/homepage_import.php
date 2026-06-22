<?php

declare(strict_types=1);

/**
 * @file
 * Drush script: create a sample homepage header node.
 *
 * Usage (from Drupal root):
 *   drush php:script web/modules/custom/open_science_survey_migration/data/homepage_import.php
 */

use Drupal\Core\File\FileSystemInterface;
use Drupal\file\Entity\File;

$entity_type_manager = \Drupal::entityTypeManager();
$field_manager = \Drupal::service('entity_field.manager');
$node_storage = $entity_type_manager->getStorage('node');
$taxonomy_storage = $entity_type_manager->getStorage('taxonomy_term');
$file_storage = $entity_type_manager->getStorage('file');
$file_system = \Drupal::service('file_system');

$header_bundle = 'homepage_header';
$header_required_fields = [
  'field_advanced_search_label',
  'field_image',
  'field_logo',
  'field_navigation_links',
  'field_search_placeholder',
  'field_subtitle',
];

$footer_bundle = 'homepage_footer';
$footer_required_fields = [
  'field_contact_email',
  'field_copyright_text',
  'field_logo',
  'field_navigation_links',
  'field_privacy_page',
  'field_tagline',
  'field_website',
];

$card_bundle = 'homepage_card';
$card_required_fields = [
  'body',
  'field_image',
  'field_tagline',
  'field_tags',
  'field_website',
  'field_weight',
];

$partner_bundle = 'homepage_partner';
$partner_required_fields = [
  'field_logo',
  'field_website',
  'field_weight',
];

$assert_bundle_fields = static function (string $bundle, array $required_fields) use ($field_manager): void {
  $field_definitions = $field_manager->getFieldDefinitions('node', $bundle);
  foreach ($required_fields as $field_name) {
    if (!isset($field_definitions[$field_name])) {
      throw new \RuntimeException(
        "Field '{$field_name}' does not exist on node bundle '{$bundle}'."
      );
    }
  }
};

$required_fields_by_bundle = [
  $header_bundle => $header_required_fields,
  $footer_bundle => $footer_required_fields,
  $card_bundle => $card_required_fields,
  $partner_bundle => $partner_required_fields,
];

foreach ($required_fields_by_bundle as $bundle => $required_fields) {
  $assert_bundle_fields($bundle, $required_fields);
}

$sample_data = [
  'title' => 'UNESCO Open Science Platform',
  'field_subtitle' => 'Your Gateway to Knowledge from the UNESCO Natural Science Family',
  'field_search_placeholder' => "Search UNESCO's research publications",
  'field_advanced_search_label' => 'Advanced search',
  // background_image and logo are intentionally left empty.
  'field_navigation_links' => [
    [
      'title' => 'About',
      'uri' => 'internal:/about',
    ],
    [
      'title' => 'UNESCO Natural Sciences Family',
      'uri' => 'internal:/natural-sciences-family',
    ],
    [
      'title' => 'UNESCO Open Science Dashboards',
      'uri' => '/dashboards',
    ],
  ],
];

$header_node = $node_storage->create([
  'type' => $header_bundle,
  'title' => $sample_data['title'],
  'status' => 1,
  'langcode' => 'en',
  'field_subtitle' => $sample_data['field_subtitle'],
  'field_search_placeholder' => $sample_data['field_search_placeholder'],
  'field_advanced_search_label' => $sample_data['field_advanced_search_label'],
  'field_navigation_links' => $sample_data['field_navigation_links'],
]);

$header_node->save();
print "Created sample homepage_header node with NID {$header_node->id()}.\n";

$about_page_node = $node_storage->create([
  'type' => 'page',
  'title' => 'About the UNESCO Open Science Platform',
  'path' => [
    'alias' => '/about',
  ],
  'status' => 1,
  'langcode' => 'en',
  'body' => [
    'value' => file_get_contents(__DIR__ . '/homepage/page_about.html'),
    'format' => 'basic_html',
  ],
]);

$about_page_node->save();
print "Created sample about page node with NID {$about_page_node->id()}.\n";

$natural_sciences_page_node = $node_storage->create([
  'type' => 'page',
  'title' => 'UNESCO Natural Sciences Family',
  'path' => [
    'alias' => '/natural-sciences-family',
  ],
  'status' => 1,
  'langcode' => 'en',
  'body' => [
    'value' => file_get_contents(__DIR__ . '/homepage/page_natural_sciences_family.html'),
    'format' => 'basic_html',
  ],
]);

$natural_sciences_page_node->save();
print "Created sample natural sciences family page node with NID {$natural_sciences_page_node->id()}.\n";

$privacy_page_node = $node_storage->create([
  'type' => 'page',
  'title' => 'Privacy Notice',
  'path' => [
    'alias' => '/privacy',
  ],
  'status' => 1,
  'langcode' => 'en',
  'body' => [
    'value' => file_get_contents(__DIR__ . '/homepage/page_privacy_notice.html'),
    'format' => 'basic_html',
  ],
]);

$privacy_page_node->save();
print "Created sample privacy page node with NID {$privacy_page_node->id()}.\n";

$footer_sample_data = [
  'title' => 'Homepage Footer',
  'field_contact_email' => 'open-science-platform@unesco.org',
  'field_copyright_text' => 'UNESCO Open Science Platform - United Nations Educational, Scientific and Cultural Organization',
  'field_navigation_links' => [
    [
      'title' => 'About',
      'uri' => 'internal:/about',
    ],
    [
      'title' => 'UNESCO Natural Sciences Family',
      'uri' => 'internal:/natural-sciences-family',
    ],
    [
      'title' => 'UNESCO Open Science Dashboard',
      'uri' => '/dashboards',
    ],
    [
      'title' => 'Privacy',
      'uri' => 'internal:/privacy',
    ],
  ],
  'field_tagline' => 'Promoting international cooperation in education, science, and culture worldwide.',
  'field_privacy_page' => [
    'target_id' => $privacy_page_node->id(),
  ],
  // unesco_logo is intentionally left empty.
  'field_website' => [
    'title' => 'Official UNESCO Website',
    'uri' => 'https://www.unesco.org',
  ],
];

$footer_node = $node_storage->create([
  'type' => $footer_bundle,
  'title' => $footer_sample_data['title'],
  'status' => 1,
  'langcode' => 'en',
  'field_contact_email' => $footer_sample_data['field_contact_email'],
  'field_copyright_text' => $footer_sample_data['field_copyright_text'],
  'field_navigation_links' => $footer_sample_data['field_navigation_links'],
  'field_privacy_page' => $footer_sample_data['field_privacy_page'],
  'field_tagline' => $footer_sample_data['field_tagline'],
  'field_website' => $footer_sample_data['field_website'],
]);

$footer_node->save();
print "Created sample homepage_footer node with NID {$footer_node->id()}.\n";

$module_relative_path = \Drupal::service('extension.list.module')->getPath('open_science_survey_migration');
if ($module_relative_path === '' || $module_relative_path === NULL) {
  throw new \RuntimeException('Unable to resolve module path for open_science_survey_migration.');
}

$module_absolute_path = DRUPAL_ROOT . '/' . $module_relative_path;
$homepage_data_path = $module_absolute_path . '/data/homepage';
if (!is_dir($homepage_data_path)) {
  throw new \RuntimeException("Homepage images directory not found: {$homepage_data_path}");
}

$public_images_directory = 'public://homepage_cards';
$prepared = $file_system->prepareDirectory(
  $public_images_directory,
  FileSystemInterface::CREATE_DIRECTORY | FileSystemInterface::MODIFY_PERMISSIONS
);
if (!$prepared) {
  throw new \RuntimeException("Unable to prepare destination directory: {$public_images_directory}");
}

$ensure_tag_term = static function (string $label) use ($taxonomy_storage) {
  $existing_ids = $taxonomy_storage->getQuery()
    ->accessCheck(FALSE)
    ->condition('vid', 'tags')
    ->condition('name', $label)
    ->range(0, 1)
    ->execute();

  if (!empty($existing_ids)) {
    $existing = $taxonomy_storage->loadMultiple($existing_ids);
    $term = reset($existing);
    if ($term) {
      return $term;
    }
  }

  $term = $taxonomy_storage->create([
    'vid' => 'tags',
    'name' => $label,
  ]);
  $term->save();
  return $term;
};

$load_or_create_image = static function (string $source_path, string $destination_directory) use ($file_storage, $file_system): ?File {
  if (!is_file($source_path) || !is_readable($source_path)) {
    return NULL;
  }

  $filename = basename($source_path);
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

$cards_json_path = $homepage_data_path . '/cards.json';
if (!is_readable($cards_json_path)) {
  throw new \RuntimeException("Cards JSON file not found or unreadable: {$cards_json_path}");
}
$card_samples = json_decode(file_get_contents($cards_json_path), TRUE, 512, JSON_THROW_ON_ERROR);

foreach ($card_samples as $card_data) {
  $tag_refs = [];
  foreach ($card_data['tags'] as $tag_label) {
    $tag_term = $ensure_tag_term($tag_label);
    $tag_refs[] = ['target_id' => $tag_term->id()];
  }

  $card_values = [
    'type' => $card_bundle,
    'title' => $card_data['title'],
    'status' => 1,
    'langcode' => 'en',
    'body' => [
      'value' => $card_data['body'],
      'format' => 'basic_html',
    ],
    'field_tagline' => $card_data['field_tagline'],
    'field_website' => [
      'title' => 'Source',
      'uri' => $card_data['link'],
    ],
    'field_weight' => $card_data['field_weight'],
    'field_tags' => $tag_refs,
  ];

  $image_file = $load_or_create_image($homepage_data_path . '/' . $card_data['image_source'], $public_images_directory);
  if ($image_file) {
    $card_values['field_image'] = [
      'target_id' => $image_file->id(),
      'alt' => $card_data['title'],
    ];
  }

  $card_node = $node_storage->create($card_values);
  $card_node->save();
  print "Created sample homepage_card node '{$card_data['title']}' with NID {$card_node->id()}.\n";
}

$partner_samples = [
  [
    'title' => 'InvenioRDM',
    'url' => 'https://inveniosoftware.org/',
    'image_source' => $homepage_data_path . '/partner_1.svg',
    'field_weight' => 1,
  ],
  [
    'title' => 'Lens.org',
    'url' => 'https://www.lens.org/',
    'image_source' => $homepage_data_path . '/partner_2.png',
    'field_weight' => 2,
  ],
];

$partner_nids = [];
$public_partner_images_directory = 'public://homepage_partners';
foreach ($partner_samples as $partner_data) {
  $image_file = $load_or_create_image($partner_data['image_source'], $public_partner_images_directory);
  if (!$image_file) {
    throw new \RuntimeException("Missing or unreadable partner image: {$partner_data['image_source']}");
  }

  $partner_values = [
    'type' => $partner_bundle,
    'title' => $partner_data['title'],
    'status' => 1,
    'langcode' => 'en',
    'field_logo' => [
      'target_id' => $image_file->id(),
      'alt' => $partner_data['title'],
    ],
    'field_website' => [
      'title' => $partner_data['title'],
      'uri' => $partner_data['url'],
    ],
    'field_weight' => $partner_data['field_weight'],
  ];

  $partner_node = $node_storage->create($partner_values);
  $partner_node->save();
  $partner_nids[] = $partner_node->id();
  print "Created sample homepage_partner node '{$partner_data['title']}' with NID {$partner_node->id()}.\n";
}

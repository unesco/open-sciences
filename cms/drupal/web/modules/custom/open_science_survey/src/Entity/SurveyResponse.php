<?php

declare(strict_types=1);

namespace Drupal\open_science_survey\Entity;

use Drupal\Core\Entity\Attribute\ContentEntityType;
use Drupal\Core\Entity\ContentEntityDeleteForm;
use Drupal\Core\Entity\EditorialContentEntityBase;
use Drupal\Core\Entity\EntityChangedTrait;
use Drupal\Core\Entity\EntityStorageInterface;
use Drupal\Core\Entity\EntityTypeInterface;
use Drupal\Core\Entity\Form\DeleteMultipleForm;
use Drupal\Core\Entity\Form\RevisionDeleteForm;
use Drupal\Core\Entity\Form\RevisionRevertForm;
use Drupal\Core\Entity\Routing\RevisionHtmlRouteProvider;
use Drupal\Core\Field\BaseFieldDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\open_science_survey\Form\SurveyResponseForm;
use Drupal\open_science_survey\Routing\SurveyResponseHtmlRouteProvider;
use Drupal\open_science_survey\SurveyResponseAccessControlHandler;
use Drupal\open_science_survey\SurveyResponseInterface;
use Drupal\open_science_survey\SurveyResponseListBuilder;
use Drupal\user\EntityOwnerTrait;
use Drupal\views\EntityViewsData;

/**
 * Defines the survey response entity class.
 */
#[ContentEntityType(
  id: 'survey_response',
  label: new TranslatableMarkup('Survey Response'),
  label_collection: new TranslatableMarkup('Survey Responses'),
  label_singular: new TranslatableMarkup('survey response'),
  label_plural: new TranslatableMarkup('survey responses'),
  entity_keys: [
    'id' => 'id',
    'revision' => 'revision_id',
    'label' => 'id',
    'owner' => 'uid',
    'published' => 'status',
    'uuid' => 'uuid',
  ],
  handlers: [
    'list_builder' => SurveyResponseListBuilder::class,
    'views_data' => EntityViewsData::class,
    'access' => SurveyResponseAccessControlHandler::class,
    'form' => [
      'add' => SurveyResponseForm::class,
      'edit' => SurveyResponseForm::class,
      'delete' => ContentEntityDeleteForm::class,
      'delete-multiple-confirm' => DeleteMultipleForm::class,
      'revision-delete' => RevisionDeleteForm::class,
      'revision-revert' => RevisionRevertForm::class,
    ],
    'route_provider' => [
      'html' => SurveyResponseHtmlRouteProvider::class,
      'revision' => RevisionHtmlRouteProvider::class,
    ],
  ],
  links: [
    'collection' => '/admin/content/survey-response',
    'add-form' => '/survey-response/add',
    'canonical' => '/survey-response/{survey_response}',
    'edit-form' => '/survey-response/{survey_response}',
    'delete-form' => '/survey-response/{survey_response}/delete',
    'delete-multiple-form' => '/admin/content/survey-response/delete-multiple',
    'revision' => '/survey-response/{survey_response}/revision/{survey_response_revision}/view',
    'revision-delete-form' => '/survey-response/{survey_response}/revision/{survey_response_revision}/delete',
    'revision-revert-form' => '/survey-response/{survey_response}/revision/{survey_response_revision}/revert',
    'version-history' => '/survey-response/{survey_response}/revisions',
  ],
  admin_permission: 'administer survey_response',
  base_table: 'survey_response',
  revision_table: 'survey_response_revision',
  show_revision_ui: TRUE,
  label_count: [
    'singular' => '@count survey responses',
    'plural' => '@count survey responses',
  ],
  field_ui_base_route: 'entity.survey_response.settings',
  revision_metadata_keys: [
    'revision_user' => 'revision_uid',
    'revision_created' => 'revision_timestamp',
    'revision_log_message' => 'revision_log',
  ],
)]
class SurveyResponse extends EditorialContentEntityBase implements SurveyResponseInterface {

  use EntityChangedTrait;
  use EntityOwnerTrait;

  /**
   * {@inheritdoc}
   */
  public function preSave(EntityStorageInterface $storage): void {
    parent::preSave($storage);
    if (!$this->getOwnerId()) {
      // If no owner has been set explicitly, make the anonymous user the owner.
      $this->setOwnerId(0);
    }
  }

  /**
   * {@inheritdoc}
   */
  public static function baseFieldDefinitions(EntityTypeInterface $entity_type): array {

    $fields = parent::baseFieldDefinitions($entity_type);

    $fields['status'] = BaseFieldDefinition::create('boolean')
      ->setRevisionable(TRUE)
      ->setLabel(t('Status'))
      ->setDefaultValue(TRUE)
      ->setSetting('on_label', 'Enabled')
      ->setDisplayOptions('form', [
        'type' => 'boolean_checkbox',
        'settings' => [
          'display_label' => FALSE,
        ],
        'weight' => 0,
      ])
      ->setDisplayConfigurable('form', TRUE)
      ->setDisplayOptions('view', [
        'type' => 'boolean',
        'label' => 'above',
        'weight' => 0,
        'settings' => [
          'format' => 'enabled-disabled',
        ],
      ])
      ->setDisplayConfigurable('view', TRUE);

    $fields['uid'] = BaseFieldDefinition::create('entity_reference')
      ->setRevisionable(TRUE)
      ->setLabel(t('Author'))
      ->setSetting('target_type', 'user')
      ->setDefaultValueCallback(self::class . '::getDefaultEntityOwner')
      ->setDisplayOptions('form', [
        'type' => 'entity_reference_autocomplete',
        'settings' => [
          'match_operator' => 'CONTAINS',
          'size' => 60,
          'placeholder' => '',
        ],
        'weight' => 15,
      ])
      ->setDisplayConfigurable('form', TRUE)
      ->setDisplayOptions('view', [
        'label' => 'above',
        'type' => 'author',
        'weight' => 15,
      ])
      ->setDisplayConfigurable('view', TRUE);

    $fields['created'] = BaseFieldDefinition::create('created')
      ->setLabel(t('Authored on'))
      ->setDescription(t('The time that the survey response was created.'))
      ->setDisplayOptions('view', [
        'label' => 'above',
        'type' => 'timestamp',
        'weight' => 20,
      ])
      ->setDisplayConfigurable('form', TRUE)
      ->setDisplayOptions('form', [
        'type' => 'datetime_timestamp',
        'weight' => 20,
      ])
      ->setDisplayConfigurable('view', TRUE);

    $fields['changed'] = BaseFieldDefinition::create('changed')
      ->setLabel(t('Changed'))
      ->setDescription(t('The time that the survey response was last edited.'));

    return $fields;
  }

}

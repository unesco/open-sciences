<?php

declare(strict_types=1);

namespace Drupal\open_science_survey;

use Drupal\Core\Entity\ContentEntityInterface;
use Drupal\Core\Entity\EntityChangedInterface;
use Drupal\user\EntityOwnerInterface;

/**
 * Provides an interface defining a survey response entity type.
 */
interface SurveyResponseInterface extends ContentEntityInterface, EntityOwnerInterface, EntityChangedInterface {

}

<?php

declare(strict_types=1);

namespace Drupal\open_science_survey;

use Drupal\Core\Access\AccessResult;
use Drupal\Core\Entity\EntityAccessControlHandler;
use Drupal\Core\Entity\EntityInterface;
use Drupal\Core\Session\AccountInterface;

/**
 * Defines the access control handler for the survey response entity type.
 *
 * phpcs:disable Drupal.Arrays.Array.LongLineDeclaration
 *
 * @see https://www.drupal.org/project/coder/issues/3185082
 */
final class SurveyResponseAccessControlHandler extends EntityAccessControlHandler {

  /**
   * {@inheritdoc}
   */
  protected function checkAccess(EntityInterface $entity, $operation, AccountInterface $account): AccessResult {
    if ($account->hasPermission($this->entityType->getAdminPermission())) {
      return AccessResult::allowed()->cachePerPermissions();
    }

    return match($operation) {
      'view' => AccessResult::allowedIfHasPermission($account, 'view survey_response'),
      'update' => AccessResult::allowedIfHasPermission($account, 'edit survey_response'),
      'delete' => AccessResult::allowedIfHasPermission($account, 'delete survey_response'),
      'delete revision' => AccessResult::allowedIfHasPermission($account, 'delete survey_response revision'),
      'view all revisions', 'view revision' => AccessResult::allowedIfHasPermissions($account, ['view survey_response revision', 'view survey_response']),
      'revert' => AccessResult::allowedIfHasPermissions($account, ['revert survey_response revision', 'edit survey_response']),
      default => AccessResult::neutral(),
    };
  }

  /**
   * {@inheritdoc}
   */
  protected function checkCreateAccess(AccountInterface $account, array $context, $entity_bundle = NULL): AccessResult {
    return AccessResult::allowedIfHasPermissions($account, ['create survey_response', 'administer survey_response'], 'OR');
  }

}

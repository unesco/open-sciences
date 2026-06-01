#!/bin/bash
set -e

ENV=${ENV:-dev}
ADMIN_USER_EMAIL=${ADMIN_USER_EMAIL:-admin@unesco.org}
ADMIN_USER_PASSWORD=${ADMIN_USER_PASSWORD:-demo1234}

echo "Deploying in $ENV environment"
cd /var/www/

echo "Installing Drupal..."
chown -R nobody:nobody html/sites/default/files/ private/
vendor/bin/drush site:install --yes --existing-config \
  --account-name="$ADMIN_USER_EMAIL" \
  --account-pass="$ADMIN_USER_PASSWORD"

echo "Installing open_science_survey_migration..."
vendor/bin/drush en open_science_survey_migration -y

echo "Importing data..."
vendor/bin/drush migrate:import --all
vendor/bin/drush scr web/modules/custom/open_science_survey_migration/data/homepage_import.php
vendor/bin/drush scr web/modules/custom/open_science_survey_migration/data/qualitative_responses_import.php
vendor/bin/drush scr web/modules/custom/open_science_survey_migration/data/quantitative_responses_import.php
vendor/bin/drush scr web/modules/custom/open_science_survey_migration/data/countries_profiles_import.php
vendor/bin/drush scr web/modules/custom/open_science_survey_migration/data/challenges_import.php

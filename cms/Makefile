.PHONY: setup help wait-db setup-db setup-db-clean

# Configuration variables
WAIT_TIMEOUT ?= 60

help:
	@echo "=============================="
	@echo " CMS Makefile Documentation"
	@echo "=============================="
	@echo ""
	@echo "CMS Commands:"
	@echo "  make cms-setup                  - Setup CMS containers and permissions"
	@echo "  make cms-setup-clean            - Clean and setup CMS containers and permissions"
	@echo "  make cms-fix-volumes-permissions - Fix file permissions for CMS volumes"
	@echo "  make cms-install-drupal         - Install Drupal if not already installed"
	@echo "  make cms-import-survey-data     - Enable migration module and import survey data"
	@echo "  make cms-index-survey-responses - Enable search module and index survey responses"
	@echo ""
	@echo "=============================="
	@echo " For more details, see comments in this Makefile."

cms-setup:
ifdef CLEAN
	@docker compose up -d --build --force-recreate cms
else
	@docker compose up -d cms
endif
	@$(MAKE) fix-volumes-permissions
	@$(MAKE) install-drupal

cms-setup-clean:
	@$(MAKE) setup CLEAN=1

cms-fix-volumes-permissions:
	@docker compose exec -u root cms chown -R nobody:nobody /var/www/html/sites/default/files
	@docker compose exec -u root cms chown -R nobody:nobody /var/www/private

cms-install-drupal:
ifndef CLEAN
	@if docker compose exec cms drush status --fields=bootstrap 2>/dev/null | grep -q "Successful"; then \
		echo "✓ Drupal is already installed"; \
		exit 0; \
	fi
endif
	@echo "Installing Drupal..."
	@docker compose exec cms drush site:install --yes --existing-config \
		--account-name=admin@unesco.org \
		--account-pass=$(USER_PASSWORD)
	@echo "✓ Drupal installation complete"

cms-import-survey-data:
	@docker compose exec cms drush en open_science_survey_migration -y
	@docker compose exec cms drush migrate:import --all

cms-index-survey-responses:
	@docker compose exec cms drush en open_science_survey_search -y
	@docker compose exec cms drush search-api:reset-tracker survey_responses
	@docker compose exec cms drush search-api:index survey_responses


.PHONY: cms-setup cms-help cms-install-drupal cms-disable-elastic

# Configuration variables
WAIT_TIMEOUT ?= 60

cms-help:
	@echo "=============================="
	@echo " CMS Makefile Documentation"
	@echo "=============================="
	@echo ""
	@echo "CMS Commands:"
	@echo "  make cms-setup                  - Setup CMS containers"
	@echo "  make cms-setup-clean            - Clean and setup CMS containers"
	@echo "  make cms-install-drupal         - Install Drupal"
	@echo "  make cms-disable-elastic        - Disable Elastic APM"
	@echo ""
	@echo "=============================="
	@echo " For more details, see comments in this Makefile."

cms-setup:
	@docker compose up -d db cms
	@$(MAKE) cms-install-drupal

cms-setup-clean:
	@docker compose up -d --build --force-recreate db cms
	@$(MAKE) cms-setup

cms-disable-elastic:
	@docker compose exec -u root cms mv /usr/local/etc/php/conf.d/98-elastic-apm.ini /usr/local/etc/php/conf.d/98-elastic-apm.ini.off
	@docker compose exec -u root cms killall -9 php-fpm

cms-install-drupal:
	@docker compose exec -u root -e ENV=dev -e ADMIN_USER_EMAIL=admin@unesco.org -e ADMIN_USER_PASSWORD=$(USER_PASSWORD) cms /var/www/deploy.sh

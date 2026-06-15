FROM public.ecr.aws/unicc/lap83-alpine:stable

USER root

RUN rm -rf /vendor \
    && rm -rf /usr/local/bin/drush

RUN rm -rf /var/www/html
RUN rm -rf /var/www/localhost
RUN apk update && apk add git postgresql-client patch
RUN apk add --no-cache postgresql-dev \
 && docker-php-ext-install pdo_pgsql pgsql \
 && apk del --no-cache postgresql-dev

COPY httpd/cms-subpath.conf /etc/apache2/conf.d/cms-subpath.conf

USER nobody
COPY --chown=nobody:nobody drupal /var/www

RUN mkdir /var/tmp/drupal \
    && mkdir -p /var/www/web/sites/default/files \
    && mkdir /var/www/private

WORKDIR /var/www
RUN ln -s /var/www/web html
RUN ln -sf /var/www/web /var/www/html/cms

ENV COMPOSER_HOME=/var/www
RUN composer install
ENV PATH=$PATH:/var/www/vendor/bin

#   CMD ["/var/www/startup.sh"]

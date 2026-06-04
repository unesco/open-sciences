<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <https://www.gnu.org/licenses/>.

namespace Drupal\open_science_survey\Controller;

use Drupal\Core\Cache\Cache;
use Drupal\Core\Cache\CacheableJsonResponse;
use Drupal\Core\Cache\CacheableMetadata;
use Drupal\Core\Controller\ControllerBase;
use Drupal\Core\Entity\EntityInterface;
use Drupal\Core\Url;
use Symfony\Component\HttpFoundation\JsonResponse;

/**
 * Controller for homepage header API endpoints.
 *
 * @copyright 2026 UNESCO Open Science
 * @license http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class HomepageController extends ControllerBase {
    /**
     * Header endpoint.
     *
     * GET /api/frontpage/header
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   Cacheable JSON object with homepage header content.
     */
    public function header() {
        try {
            $nodestorage = $this->entityTypeManager()->getStorage('node');
            $nodeids = $nodestorage->getQuery()->accessCheck(true)
                ->condition('type', 'homepage_header')
                ->condition('status', 1)
                ->sort('nid', 'ASC')
                ->range(0, 1)
                ->execute();

            if (empty($nodeids)) {
                return new JsonResponse([
                    'error' => 'Homepage header not found',
                ], 404);
            }

            $nid = (int) reset($nodeids);
            $node = $nodestorage->load($nid);
            if (!$node) {
                return new JsonResponse([
                    'error' => 'Homepage header not found',
                ], 404);
            }

            $data = [
                'advanced_search_label' => $this->extractstringfieldvalue($node, 'field_advanced_search_label'),
                'background_image' => $this->extractimagefieldurl($node, 'field_image'),
                'logo' => $this->extractimagefieldurl($node, 'field_logo'),
                'navigation_links' => $this->extractnavigationlinks($node),
                'search_placeholder' => $this->extractstringfieldvalue($node, 'field_search_placeholder'),
                'subtitle' => $this->extractstringfieldvalue($node, 'field_subtitle'),
                'title' => (string) $node->label(),
            ];

            $payload = $this->buildresourcepayload(
                $data,
                'header_frontpage',
                (string) $node->language()->getId()
            );

            return $this->buildcacheablejsonresponse(
                $payload,
                ['user.permissions'],
                ['node_list:homepage_header'],
                $node,
                Cache::PERMANENT
            );
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Homepage header endpoint failed: @message', [
                '@message' => $e->getMessage(),
            ]);

            $response = new JsonResponse([
                'error' => 'Failed to fetch homepage header',
            ], 500);

            $response->headers->set('Cache-Control', 'private, no-store');
            return $response;
        }
    }

    /**
     * Footer endpoint.
     *
     * GET /api/homepage/footer
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   Cacheable JSON object with homepage footer content.
     */
    public function footer() {
        try {
            $nodestorage = $this->entityTypeManager()->getStorage('node');
            $nodeids = $nodestorage->getQuery()->accessCheck(true)
                ->condition('type', 'homepage_footer')
                ->condition('status', 1)
                ->sort('nid', 'ASC')
                ->range(0, 1)
                ->execute();

            if (empty($nodeids)) {
                return new JsonResponse([
                    'error' => 'Homepage footer not found',
                ], 404);
            }

            $nid = (int) reset($nodeids);
            $node = $nodestorage->load($nid);
            if (!$node) {
                return new JsonResponse([
                    'error' => 'Homepage footer not found',
                ], 404);
            }

            $website = $this->extractlinkfield($node, 'field_website');

            $data = [
                'contact_email' => $this->extractstringfieldvalue($node, 'field_contact_email'),
                'copyright_text' => $this->extractstringfieldvalue($node, 'field_copyright_text'),
                'navigation_links' => $this->extractnavigationlinks($node),
                'privacy_page' => $this->extractentityreferenceapipageurl($node, 'field_privacy_page'),
                'tagline' => $this->extractstringfieldvalue($node, 'field_tagline'),
                'unesco_logo' => $this->extractimagefieldurl($node, 'field_logo'),
                'unesco_website_label' => $website['label'],
                'unesco_website_url' => $website['url'],
            ];

            $payload = $this->buildresourcepayload(
                $data,
                'footer',
                (string) $node->language()->getId()
            );

            return $this->buildcacheablejsonresponse(
                $payload,
                ['user.permissions'],
                ['node_list:homepage_footer'],
                $node,
                Cache::PERMANENT
            );
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Homepage footer endpoint failed: @message', [
                '@message' => $e->getMessage(),
            ]);

            $response = new JsonResponse([
                'error' => 'Failed to fetch homepage footer',
            ], 500);

            $response->headers->set('Cache-Control', 'private, no-store');
            return $response;
        }
    }

    /**
     * Cards endpoint.
     *
     * GET /api/homepage/cards
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   Cacheable JSON object with homepage highlight cards sorted by field_weight.
     */
    public function cards() {
        try {
            $nodestorage = $this->entityTypeManager()->getStorage('node');
            $nodeids = $nodestorage->getQuery()->accessCheck(true)
                ->condition('type', 'homepage_card')
                ->condition('status', 1)
                ->sort('field_weight', 'ASC')
                ->sort('nid', 'ASC')
                ->execute();

            if (empty($nodeids)) {
                return $this->buildcacheablejsonresponse(
                    $this->buildresourcepayload(['highlight_cards' => []], 'cards'),
                    ['user.permissions'],
                    ['node_list:homepage_card']
                );
            }

            $nodes = $nodestorage->loadMultiple($nodeids);
            $items = [];

            foreach ($nodes as $node) {
                $items[] = [
                    'image' => $this->extractcardimagepath($node),
                    'tags' => $this->extractcardtags($node),
                    'number' => $this->extractstringfieldvalue($node, 'field_tagline'),
                    'description' => $this->extractbodyfieldvalue($node),
                    'website' => $this->extractapilinkfield($node, 'field_website'),
                ];
            }

            $first_node = reset($nodes);
            $lang = $first_node ? (string) $first_node->language()->getId() : 'en';

            return $this->buildcacheablejsonresponse(
                $this->buildresourcepayload(['highlight_cards' => $items], 'cards', $lang),
                ['user.permissions'],
                ['node_list:homepage_card']
            );
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Homepage cards endpoint failed: @message', [
                '@message' => $e->getMessage(),
            ]);

            $response = new JsonResponse([
                'error' => 'Failed to fetch homepage cards',
            ], 500);

            $response->headers->set('Cache-Control', 'private, no-store');
            return $response;
        }
    }

    /**
     * Partners endpoint.
     *
     * GET /api/homepage/partners
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   Cacheable JSON object with homepage partners sorted by field_weight.
     */
    public function partners() {
        try {
            $nodestorage = $this->entityTypeManager()->getStorage('node');
            $nodeids = $nodestorage->getQuery()->accessCheck(true)
                ->condition('type', 'homepage_partner')
                ->condition('status', 1)
                ->sort('field_weight', 'ASC')
                ->sort('nid', 'ASC')
                ->execute();

            if (empty($nodeids)) {
                return $this->buildcacheablejsonresponse(
                    $this->buildresourcepayload(['partners' => []], 'partners'),
                    ['user.permissions'],
                    ['node_list:homepage_partner']
                );
            }

            $nodes = $nodestorage->loadMultiple($nodeids);
            $items = [];

            foreach ($nodes as $node) {
                $website = $this->extractlinkfield($node, 'field_website');
                $items[] = [
                    'image' => $this->extractimagefieldurl($node, 'field_logo'),
                    'url' => $website['url'],
                    'title' => (string) $node->label(),
                ];
            }

            $first_node = reset($nodes);
            $lang = $first_node ? (string) $first_node->language()->getId() : 'en';

            return $this->buildcacheablejsonresponse(
                $this->buildresourcepayload(['partners' => $items], 'partners', $lang),
                ['user.permissions'],
                ['node_list:homepage_partner']
            );
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Homepage partners endpoint failed: @message', [
                '@message' => $e->getMessage(),
            ]);

            $response = new JsonResponse([
                'error' => 'Failed to fetch homepage partners',
            ], 500);

            $response->headers->set('Cache-Control', 'private, no-store');
            return $response;
        }
    }

    /**
     * Page endpoint.
     *
     * GET /api/pages/{page_path}
     *
    * @param string $page_path
    *   First path segment for alias/internal path.
    * @param string $page_subpath
    *   Optional remaining path segments.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   JSON object with title and rendered body for a published basic page.
     */
    public function page($page_path, $page_subpath = '') {
        try {
            $combinedpath = (string) $page_path;
            if ($page_subpath !== '') {
                $combinedpath .= '/' . (string) $page_subpath;
            }

            $requestedpath = '/' . ltrim($combinedpath, '/');
            $resolvedpath = \Drupal::service('path_alias.manager')->getPathByAlias($requestedpath);

            // If the alias lookup does not resolve, allow direct internal node paths.
            if ($resolvedpath === $requestedpath && strpos($requestedpath, '/node/') !== 0) {
                return new JsonResponse([
                    'error' => 'Page not found',
                ], 404);
            }

            if (!preg_match('#^/node/(\d+)$#', $resolvedpath, $matches)) {
                return new JsonResponse([
                    'error' => 'Page not found',
                ], 404);
            }

            $node = $this->entityTypeManager()->getStorage('node')->load((int) $matches[1]);
            if (!$node || $node->bundle() !== 'page' || !$node->isPublished() || !$node->access('view')) {
                return new JsonResponse([
                    'error' => 'Page not found',
                ], 404);
            }

            return $this->buildcacheablejsonresponse(
                [
                    'body' => $this->extractbodyfieldvalue($node),
                    'title' => (string) $node->label(),
                ],
                ['languages:language_interface', 'url.path', 'user.permissions'],
                ['node:' . $node->id(), 'route_match'],
                $node,
                Cache::PERMANENT
            );
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('Homepage page endpoint failed: @message', [
                '@message' => $e->getMessage(),
            ]);

            $response = new JsonResponse([
                'error' => 'Failed to fetch page',
            ], 500);

            $response->headers->set('Cache-Control', 'private, no-store');
            return $response;
        }
    }

    /**
     * Page endpoint for internal node paths.
     *
     * GET /api/pages/node/{nid}
     *
     * @param int|string $nid
     *   Node ID.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   JSON object with title and rendered body for a published basic page.
     */
    public function pagebynid($nid) {
        return $this->page('node', (string) $nid);
    }

    /**
     * Builds a cacheable JSON response with cache metadata.
     */
    protected function buildcacheablejsonresponse(
        array $data,
        array $contexts = [],
        array $tags = [],
        $entity = null,
        $maxage = Cache::PERMANENT
    ) {
        $response = new CacheableJsonResponse($data);

        $cacheability = new CacheableMetadata();
        if (!empty($contexts)) {
            $cacheability->setCacheContexts($contexts);
        }
        if (!empty($tags)) {
            $cacheability->setCacheTags($tags);
        }
        $cacheability->setCacheMaxAge($maxage);
        if ($entity !== null) {
            $cacheability->addCacheableDependency($entity);
        }

        $response->addCacheableDependency($cacheability);
        return $response;
    }

    /**
     * Builds the shared API envelope for homepage resources.
     */
    protected function buildresourcepayload(array $data, $resourcetype, $lang = 'en') {
        return [
            'data' => $data,
            'lang' => (string) $lang,
            'resource_type' => (string) $resourcetype,
            'source' => 'database',
        ];
    }

    /**
     * Extracts rendered body (description) text from a node body field.
     */
    protected function extractbodyfieldvalue(EntityInterface $node) {
        if (!$node->hasField('body') || $node->get('body')->isEmpty()) {
            return '';
        }

        $item = $node->get('body')->first();
        $text = (string) ($item->value ?? '');
        $format = (string) ($item->format ?? '');

        if ($text === '') {
            return '';
        }

        if ($format === '') {
            return $text;
        }

        $build = [
            '#type' => 'processed_text',
            '#text' => $text,
            '#format' => $format,
            '#langcode' => $node->language()->getId(),
        ];

        return (string) \Drupal::service('renderer')->renderInIsolation($build);
    }

    /**
     * Extracts string value from a node string field.
     */
    protected function extractstringfieldvalue(EntityInterface $node, $fieldname) {
        if (!$node->hasField($fieldname) || $node->get($fieldname)->isEmpty()) {
            return '';
        }

        return trim((string) ($node->get($fieldname)->value ?? ''));
    }

    /**
     * Extracts a file URL from an image field.
     */
    protected function extractimagefieldurl(EntityInterface $entity, $fieldname) {
        if (!$entity->hasField($fieldname) || $entity->get($fieldname)->isEmpty()) {
            return '';
        }

        $file = $entity->get($fieldname)->entity;
        if (!$file || !$file->getFileUri()) {
            return '';
        }

        return \Drupal::service('file_url_generator')->generateString($file->getFileUri());
    }

    /**
     * Extracts image path in /static/images/<filename> format for cards.
     */
    protected function extractcardimagepath(EntityInterface $node) {
        if (!$node->hasField('field_image') || $node->get('field_image')->isEmpty()) {
            return '';
        }

        $file = $node->get('field_image')->entity;
        if (!$file || !$file->getFileUri()) {
            return '';
        }

        return \Drupal::service('file_url_generator')->generateString($file->getFileUri());
    }

    /**
     * Extracts card tags as a plain label array.
     */
    protected function extractcardtags(EntityInterface $node) {
        $tags = [];
        if (!$node->hasField('field_tags') || $node->get('field_tags')->isEmpty()) {
            return $tags;
        }

        foreach ($node->get('field_tags')->referencedEntities() as $term) {
            $tags[] = (string) $term->label();
        }

        return $tags;
    }

    /**
     * Extracts navigation links in {external, label, url} format.
     */
    protected function extractnavigationlinks(EntityInterface $node) {
        $links = [];
        if (!$node->hasField('field_navigation_links') || $node->get('field_navigation_links')->isEmpty()) {
            return $links;
        }

        foreach ($node->get('field_navigation_links') as $item) {
            $uri = (string) ($item->uri ?? '');
            if ($uri === '') {
                continue;
            }

            $external = $this->isexternallinkuri($uri);
            $url = $this->normalizelinkuri($uri);

            if (!$external) {
                $url = '/api/pages/' . ltrim($url, '/');
            }

            $links[] = [
                'external' => $external,
                'label' => (string) ($item->title ?? ''),
                'url' => $url,
            ];
        }

        return $links;
    }

    /**
     * Extracts a single link field in {label, url} format.
     */
    protected function extractlinkfield(EntityInterface $node, $fieldname) {
        if (!$node->hasField($fieldname) || $node->get($fieldname)->isEmpty()) {
            return ['label' => '', 'url' => ''];
        }

        $item = $node->get($fieldname)->first();
        if (!$item) {
            return ['label' => '', 'url' => ''];
        }

        $uri = (string) ($item->uri ?? '');
        if ($uri === '') {
            return [
                'label' => (string) ($item->title ?? ''),
                'url' => '',
            ];
        }

        return [
            'label' => (string) ($item->title ?? ''),
            'url' => $this->normalizelinkuri($uri),
        ];
    }

    /**
     * Extracts a single link field in {external, label, url} format.
     *
     * Internal links are converted to /api/pages/... URLs.
     */
    protected function extractapilinkfield(EntityInterface $node, $fieldname) {
        if (!$node->hasField($fieldname) || $node->get($fieldname)->isEmpty()) {
            return ['external' => false, 'label' => '', 'url' => ''];
        }

        $item = $node->get($fieldname)->first();
        if (!$item) {
            return ['external' => false, 'label' => '', 'url' => ''];
        }

        $uri = (string) ($item->uri ?? '');
        $label = (string) ($item->title ?? '');
        if ($uri === '') {
            return ['external' => false, 'label' => $label, 'url' => ''];
        }

        $external = $this->isexternallinkuri($uri);
        $url = $this->normalizelinkuri($uri);
        if (!$external) {
            $url = '/api/pages/' . ltrim($url, '/');
        }

        return [
            'external' => $external,
            'label' => $label,
            'url' => $url,
        ];
    }

    /**
     * Extracts relative URL from a referenced entity field.
     */
    protected function extractentityreferenceurl(EntityInterface $node, $fieldname) {
        if (!$node->hasField($fieldname) || $node->get($fieldname)->isEmpty()) {
            return '';
        }

        $entity = $node->get($fieldname)->entity;
        if (!$entity) {
            return '';
        }

        return $entity->toUrl()->toString();
    }

    /**
     * Normalizes Drupal link URIs to frontend-friendly URLs.
     */
    protected function normalizelinkuri($uri) {
        try {
            return Url::fromUri($uri)->toString();
        } catch (\Exception $e) {
            if (strpos($uri, 'internal:') === 0) {
                return substr($uri, strlen('internal:'));
            }

            return $uri;
        }
    }

    /**
     * Determines if a link URI points to an external target.
     */
    protected function isexternallinkuri($uri) {
        return preg_match('/^(https?:|mailto:|tel:)/i', (string) $uri) === 1;
    }

    /**
     * Returns the /api/pages/ URL for a referenced node entity.
     *
     * Uses the path alias if one exists (e.g. /api/pages/about),
     * otherwise falls back to the node ID form (e.g. /api/pages/node/42).
     */
    protected function extractentityreferenceapipageurl(EntityInterface $node, $fieldname) {
        if (!$node->hasField($fieldname) || $node->get($fieldname)->isEmpty()) {
            return '';
        }

        $entity = $node->get($fieldname)->entity;
        if (!$entity) {
            return '';
        }

        $nid = $entity->id();
        $internalpath = '/node/' . $nid;
        $alias = \Drupal::service('path_alias.manager')->getAliasByPath($internalpath);

        if ($alias !== $internalpath) {
            return '/api/pages/' . ltrim($alias, '/');
        }

        return '/api/pages/node/' . $nid;
    }

}

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

use Drupal\Core\Controller\ControllerBase;
use Drupal\Core\Entity\EntityInterface;
use Drupal\Core\Url;
use Symfony\Component\HttpFoundation\JsonResponse;

/**
 * Controller for plain language summary API endpoints.
 *
 * @copyright 2026 UNESCO Open Science
 * @license http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class PlsController extends ControllerBase {
    /**
     * List endpoint.
     *
     * GET /api/pls
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   JSON array with PLS title and node ID.
     */
    public function listpls() {
        try {
            $nodestorage = $this->entityTypeManager()->getStorage('node');
            $nodeids = $nodestorage->getQuery()->accessCheck(true)
                ->condition('type', 'plain_language_summary')
                ->condition('status', 1)
                ->sort('nid', 'ASC')
                ->execute();

            if (empty($nodeids)) {
                return new JsonResponse([]);
            }

            $nodes = $nodestorage->loadMultiple($nodeids);
            $items = [];

            foreach ($nodes as $node) {
                $items[] = [
                    'title' => (string) $node->label(),
                    'id' => (int) $node->id(),
                ];
            }

            return new JsonResponse($items);
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('PLS list endpoint failed: @message', ['@message' => $e->getMessage()]);

            return new JsonResponse([
                'error' => 'Failed to fetch plain language summaries',
            ], 500);
        }
    }

    /**
     * Detail endpoint.
     *
     * GET /api/pls/{nid}
     *
     * @param int $nid
     *   Node ID.
     *
     * @return \Symfony\Component\HttpFoundation\JsonResponse
     *   JSON object with all requested details.
     */
    public function detailpls($nid) {
        try {
            $node = $this->entityTypeManager()->getStorage('node')->load($nid);

            if (!$node || $node->bundle() !== 'plain_language_summary' || (int) $node->get('status')->value !== 1) {
                return new JsonResponse([
                    'error' => 'Plain language summary not found',
                ], 404);
            }

            $tagids = $this->extractreferencedentityids($node, 'field_tags');

            $data = [
                'title' => (string) $node->label(),
                'what_was_done' => $this->extracttextfieldvalue($node, 'field_what_was_done'),
                'why_was_done' => $this->extracttextfieldvalue($node, 'field_why_was_done'),
                'meaning' => $this->extracttextfieldvalue($node, 'field_meaning'),
                'footnotes' => $this->extracttextfieldvalue($node, 'field_footnotes'),
                'original_publication' => [
                    'link' => $this->extractlinkfielduri($node, 'field_publication_link'),
                    'authors' => $this->extractauthors($node),
                    'sponsor_text' => $this->extracttextfieldvalue($node, 'field_publication_sponsor'),
                    'sponsor_logo' => $this->extractimagefieldabsoluteurl($node, 'field_publication_sponsor_logo'),
                ],
                'tags' => $this->extracttags($node),
                'sdgs' => $this->extractsdgs($node),
                'related' => $this->loadrelatedpls((int) $node->id(), $tagids),
            ];

            return new JsonResponse($data);
        } catch (\Exception $e) {
            $this->getLogger('open_science_survey')->error('PLS detail endpoint failed for NID @nid: @message', [
                '@nid' => $nid,
                '@message' => $e->getMessage(),
            ]);

            return new JsonResponse([
                'error' => 'Failed to fetch plain language summary',
            ], 500);
        }
    }

    /**
     * Extracts text value from a node text field.
     */
    protected function extracttextfieldvalue(EntityInterface $node, $fieldname) {
        if (!$node->hasField($fieldname) || $node->get($fieldname)->isEmpty()) {
            return '';
        }

        $item = $node->get($fieldname)->first();
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
     * Extracts the first link URI from a link field.
     */
    protected function extractlinkfielduri(EntityInterface $node, $fieldname) {
        if (!$node->hasField($fieldname) || $node->get($fieldname)->isEmpty()) {
            return '';
        }

        return (string) ($node->get($fieldname)->first()->uri ?? '');
    }

    /**
     * Extracts all link items for publication authors.
     */
    protected function extractauthors(EntityInterface $node) {
        $authors = [];
        if (!$node->hasField('field_publication_authors') || $node->get('field_publication_authors')->isEmpty()) {
            return $authors;
        }

        foreach ($node->get('field_publication_authors')->getValue() as $item) {
            $title = trim((string) ($item['title'] ?? ''));
            $uri = (string) ($item['uri'] ?? '');
            $authors[] = [
                'name' => $title,
                'link' => $uri,
            ];
        }

        return $authors;
    }

    /**
     * Extracts a file URL from an image field as an absolute URL.
     */
    protected function extractimagefieldabsoluteurl(EntityInterface $entity, $fieldname) {
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
     * Extracts tags in {text, id} format.
     */
    protected function extracttags(EntityInterface $node) {
        $tags = [];
        if (!$node->hasField('field_tags') || $node->get('field_tags')->isEmpty()) {
            return $tags;
        }

        foreach ($node->get('field_tags')->referencedEntities() as $term) {
            $tags[] = [
                'text' => (string) $term->label(),
                'id' => (int) $term->id(),
            ];
        }

        return $tags;
    }

    /**
     * Extracts SDGs in {goal, text, logo, description} format.
     */
    protected function extractsdgs(EntityInterface $node) {
        $sdgs = [];
        if (!$node->hasField('field_sdgs') || $node->get('field_sdgs')->isEmpty()) {
            return $sdgs;
        }

        foreach ($node->get('field_sdgs')->referencedEntities() as $term) {
            $goal = '';
            if ($term->hasField('field_number') && !$term->get('field_number')->isEmpty()) {
                $goal = (string) ($term->get('field_number')->value ?? '');
            }

            $description = '';
            if ($term->hasField('description') && !$term->get('description')->isEmpty()) {
                $description = (string) ($term->get('description')->value ?? '');
            }

            $sdgs[] = [
                'goal' => $goal,
                'text' => (string) $term->label(),
                'logo' => $this->extractimagefieldabsoluteurl($term, 'field_logo'),
                'description' => $description,
            ];
        }

        return $sdgs;
    }

    /**
     * Extracts referenced entity IDs from an entity reference field.
     */
    protected function extractreferencedentityids(EntityInterface $entity, $fieldname) {
        if (!$entity->hasField($fieldname) || $entity->get($fieldname)->isEmpty()) {
            return [];
        }

        $ids = [];
        foreach ($entity->get($fieldname)->getValue() as $item) {
            $targetid = (int) ($item['target_id'] ?? 0);
            if ($targetid > 0) {
                $ids[] = $targetid;
            }
        }

        return array_values(array_unique($ids));
    }

    /**
     * Loads up to 3 random related published PLS nodes sharing at least one tag.
     */
    protected function loadrelatedpls($currentnid, array $tagids) {
        if (empty($tagids)) {
            return [];
        }

        $nodestorage = $this->entityTypeManager()->getStorage('node');
        $candidateids = $nodestorage->getQuery()->accessCheck(true)
            ->condition('type', 'plain_language_summary')
            ->condition('status', 1)
            ->condition('nid', (int) $currentnid, '<>')
            ->condition('field_tags.target_id', $tagids, 'IN')
            ->execute();

        if (empty($candidateids)) {
            return [];
        }

        $candidateids = array_values($candidateids);
        shuffle($candidateids);
        $selectedids = array_slice($candidateids, 0, 3);

        $selectednodes = $nodestorage->loadMultiple($selectedids);
        $related = [];
        foreach ($selectednodes as $relatednode) {
            $related[] = [
                'title' => (string) $relatednode->label(),
                'id' => (int) $relatednode->id(),
            ];
        }

        return $related;
    }

}

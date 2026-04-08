<?php

namespace Drupal\open_science_survey_search\Form;

use Drupal\Core\Form\ConfigFormBase;
use Drupal\Core\Form\FormStateInterface;

/**
 * Configure OpenSearch analyzer settings.
 */
class OpenSearchSettingsForm extends ConfigFormBase {

  /**
   * {@inheritdoc}
   */
  protected function getEditableConfigNames() {
    return ['open_science_survey_search.settings'];
  }

  /**
   * {@inheritdoc}
   */
  public function getFormId() {
    return 'open_science_survey_search_settings_form';
  }

  /**
   * {@inheritdoc}
   */
  public function buildForm(array $form, FormStateInterface $form_state) {
    $config = $this->config('open_science_survey_search.settings');

    $form['info'] = [
      '#type' => 'markup',
      '#markup' => '<p>' . $this->t('Configure the stop words used by the OpenSearch text analyzer for survey response word cloud generation.') . '</p>',
    ];

    $form['stop_words'] = [
      '#type' => 'textarea',
      '#title' => $this->t('Stop Words'),
      '#description' => $this->t('Enter stop words (one per line). These words will be excluded from word cloud analysis.'),
      '#default_value' => $config->get('stop_words') ?? '',
      '#rows' => 20,
      '#required' => TRUE,
    ];

    $form['warning'] = [
      '#type' => 'markup',
      '#markup' => '<div class="messages messages--warning">' . 
        $this->t('<strong>Important:</strong> After changing stop words, you must manually reindex the survey responses for changes to take effect. Run: <code>drush search-api:reset-tracker survey_responses && drush search-api:index survey_responses</code>') . 
        '</div>',
    ];

    $form['advanced'] = [
      '#type' => 'details',
      '#title' => $this->t('Advanced Settings'),
      '#open' => FALSE,
    ];

    $significant_terms = $config->get('significant_terms') ?? [
      'min_doc_count' => 2,
      'shard_size' => 100,
      'size' => 50,
    ];

    $form['advanced']['info_advanced'] = [
      '#type' => 'markup',
      '#markup' => '<p>' . $this->t('These settings control the significant_terms aggregation used for word cloud generation. Only modify if you understand OpenSearch aggregation parameters.') . '</p>',
    ];

    $form['advanced']['min_doc_count'] = [
      '#type' => 'number',
      '#title' => $this->t('Minimum Document Count'),
      '#description' => $this->t('Minimum number of documents a term must appear in to be included in results.'),
      '#default_value' => $significant_terms['min_doc_count'] ?? 2,
      '#min' => 1,
      '#required' => TRUE,
    ];

    $form['advanced']['shard_size'] = [
      '#type' => 'number',
      '#title' => $this->t('Shard Size'),
      '#description' => $this->t('Number of candidate terms generated from each shard.'),
      '#default_value' => $significant_terms['shard_size'] ?? 100,
      '#min' => 10,
      '#required' => TRUE,
    ];

    $form['advanced']['size'] = [
      '#type' => 'number',
      '#title' => $this->t('Maximum Terms'),
      '#description' => $this->t('Maximum number of terms to return in word cloud.'),
      '#default_value' => $significant_terms['size'] ?? 50,
      '#min' => 1,
      '#required' => TRUE,
    ];

    return parent::buildForm($form, $form_state);
  }

  /**
   * {@inheritdoc}
   */
  public function submitForm(array &$form, FormStateInterface $form_state) {
    $this->config('open_science_survey_search.settings')
      ->set('stop_words', $form_state->getValue('stop_words'))
      ->set('significant_terms', [
        'min_doc_count' => (int) $form_state->getValue('min_doc_count'),
        'shard_size' => (int) $form_state->getValue('shard_size'),
        'size' => (int) $form_state->getValue('size'),
      ])
      ->save();

    parent::submitForm($form, $form_state);

    // Update analyzer configuration.
    open_science_survey_search_update_analyzer();

    $this->messenger()->addWarning($this->t('Stop words updated. Please reindex survey responses for changes to take effect.'));
  }

}

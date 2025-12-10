# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Fixtures.

This module contains default content for CMS resources.
These fixtures are used to populate initial values when the CMS is set up.
"""

from datetime import datetime

# =============================================================================
# HEADER FRONTPAGE FIXTURE
# =============================================================================
HEADER_FRONTPAGE_DEFAULT = {
    "logo": "",  # Empty = use default /static/images/unesco-logo.svg
    "background_image": "",  # Empty = use default /static/images/science-background1.jpg
    "navigation_links": [
        {
            "label": "About",
            "url": "/pages/about",
            "external": False,
        },
        {
            "label": "Natural Sciences",
            "url": "https://www.unesco.org/en/natural-sciences",
            "external": True,
        },
        {
            "label": "Open Science",
            "url": "https://www.unesco.org/en/open-science",
            "external": True,
        },
    ],
    "title": "UNESCO Open Science Platform",
    "subtitle": "Your Gateway to Knowledge from the UNESCO Natural Science Family",
    "search_placeholder": "Search UNESCO research publications",
    "advanced_search_label": "Advanced search",
}


# =============================================================================
# FOOTER FIXTURE
# =============================================================================
FOOTER_DEFAULT = {
    "unesco_logo": "",  # Path to uploaded logo (empty = use default)
    "unesco_website_url": "https://www.unesco.org",
    "unesco_website_label": "Official UNESCO Website",
    "contact_email": "open-science-platform@unesco.org",
    "navigation_links": [
        {
            "label": "About",
            "url": "/pages/about",
            "external": False,
        },
        {
            "label": "UNESCO Natural Sciences Family",
            "url": "https://www.unesco.org/en/natural-sciences",
            "external": True,
        },
        {
            "label": "UNESCO Open Science",
            "url": "https://www.unesco.org/en/open-science",
            "external": True,
        },
    ],
    "copyright_text": "© 2025 UNESCO Open Science Portal - United Nations Educational, Scientific and Cultural Organization",
    "tagline": "Promoting international cooperation in education, science, and culture worldwide.",
}


# =============================================================================
# STATIC PAGES FIXTURES
# =============================================================================
ABOUT_PAGE_CONTENT = """<!-- Introduction Section -->
<div class="intro-section">
  <div class="section-container">
    <h2 class="section-title">What is Open Science?</h2>
    <div class="section-divider"></div>
    <p class="lead-text">
      Open Science represents a fundamental shift in how research is conducted,
      shared, and utilized. It encompasses making scientific research, data, and
      dissemination accessible to all levels of society, from professional
      researchers to curious citizens.
    </p>

    <div class="intro-cards-grid">
      <div class="intro-card">
        <div class="intro-card-image">
          <img
            src="/static/images/science-education.jpg"
            alt="Research Excellence"
          />
        </div>
        <div class="intro-card-content">
          <h3>Research Excellence</h3>
          <p>
            Promoting transparency and reproducibility in scientific research
          </p>
        </div>
      </div>

      <div class="intro-card">
        <div class="intro-card-image">
          <img
            src="/static/images/natural-sciences.jpg"
            alt="Global Collaboration"
          />
        </div>
        <div class="intro-card-content">
          <h3>Global Collaboration</h3>
          <p>Connecting researchers and institutions worldwide</p>
        </div>
      </div>

      <div class="intro-card">
        <div class="intro-card-image">
          <img src="/static/images/publish-research.jpg" alt="Open Access" />
        </div>
        <div class="intro-card-content">
          <h3>Open Access</h3>
          <p>Making knowledge freely available to everyone</p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Stats Section -->
<div class="stats-section">
  <div class="section-container">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">2.5M+</div>
        <div class="stat-label">Open Access Publications</div>
        <div class="stat-description">Available on the platform</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">193</div>
        <div class="stat-label">Member States</div>
        <div class="stat-description">Supporting the initiative</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">85%</div>
        <div class="stat-label">Increased Impact</div>
        <div class="stat-description">Through open access</div>
      </div>
    </div>
  </div>
</div>

<!-- UNESCO Recommendation Section -->
<div class="unesco-section">
  <div class="section-container">
    <h2 class="section-title">The UNESCO Recommendation on Open Science</h2>
    <div class="section-divider"></div>

    <p>
      In November 2021, UNESCO's 193 Member States adopted the groundbreaking
      Recommendation on Open Science. This historic agreement provides the first
      international framework to guide the global transition towards open
      science.
    </p>

    <div class="highlight-box">
      <h3>Key Principles</h3>
      <p>
        The UNESCO Recommendation identifies
        <strong>seven priority areas for action</strong>: promoting a common
        understanding of open science, developing enabling policy environments,
        investing in open science infrastructures, building capacity and skills,
        fostering a culture of open science, aligning incentives for open
        science, and promoting innovative approaches for open science at
        different stages of the scientific process.
      </p>
    </div>
  </div>
</div>

<div class="page-divider"></div>

<!-- Impact Section -->
<div class="impact-section">
  <div class="section-container">
    <h2 class="section-title">Impact on Global Research</h2>
    <div class="section-divider"></div>

    <div class="two-column-layout">
      <div class="benefits-card">
        <h3>For Researchers</h3>
        <ul class="benefits-list">
          <li>✓ Increased visibility and citation rates</li>
          <li>✓ Enhanced collaboration opportunities</li>
          <li>✓ Improved research quality and reproducibility</li>
          <li>✓ Access to diverse datasets and tools</li>
          <li>✓ Greater societal impact of research</li>
        </ul>
      </div>
      <div class="benefits-card">
        <h3>For Society</h3>
        <ul class="benefits-list">
          <li>✓ Accelerated innovation and discovery</li>
          <li>✓ Evidence-based policy making</li>
          <li>✓ Reduced research duplication</li>
          <li>✓ Improved public trust in science</li>
          <li>✓ Democratic access to knowledge</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<div class="page-divider"></div>

<!-- Success Stories Section -->
<div class="stories-section">
  <div class="section-container">
    <h2 class="section-title">Success Stories</h2>
    <div class="section-divider"></div>

    <div class="story-cards-grid">
      <div class="story-card">
        <div class="story-card-image">
          <img
            src="/static/images/exact-sciences.jpg"
            alt="COVID-19 Response"
          />
        </div>
        <div class="story-card-content">
          <h3>COVID-19 Response</h3>
          <p>
            Rapid sharing of genomic data and research findings enabled
            unprecedented global collaboration, accelerating vaccine development
            from years to months.
          </p>
        </div>
      </div>

      <div class="story-card">
        <div class="story-card-image">
          <img
            src="/static/images/explore-research.jpg"
            alt="Human Genome Project"
          />
        </div>
        <div class="story-card-content">
          <h3>Human Genome Project</h3>
          <p>
            A pioneering example of open science, releasing genomic data freely
            and catalyzing advances in personalized medicine and biotechnology.
          </p>
        </div>
      </div>

      <div class="story-card">
        <div class="story-card-image">
          <img src="/static/images/climate-change.jpg" alt="Climate Science" />
        </div>
        <div class="story-card-content">
          <h3>Climate Science</h3>
          <p>
            Open data initiatives have empowered communities to understand and
            respond to local environmental challenges with evidence-based
            solutions.
          </p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Call to Action Section -->
<div class="cta-section">
  <h3>Join the Open Science Movement</h3>
  <p class="cta-description">
    Explore our comprehensive database of open science publications, connect
    with researchers worldwide, and contribute to building a more transparent
    and collaborative research ecosystem.
  </p>
  <div class="cta-buttons">
    <a href="/search" class="cta-button">Explore Publications</a>
    <a href="/communities" class="cta-button cta-button-secondary"
      >Join Communities</a
    >
  </div>
</div>"""

STATIC_PAGE_ABOUT = {
    "title": "About Open Science",
    "slug": "about",
    "content": ABOUT_PAGE_CONTENT,
    "meta_title": "About Open Science - UNESCO Open Science Platform",
    "meta_description": "Learn about the open science movement and its global impact on research, collaboration, and knowledge sharing.",
}


# =============================================================================
# ALL FIXTURES REGISTRY
# =============================================================================
CMS_FIXTURES = {
    "header_frontpage": {
        "en": HEADER_FRONTPAGE_DEFAULT,
    },
    "footer": {
        "en": FOOTER_DEFAULT,
    },
    "static_page": {
        "en": {
            "about": STATIC_PAGE_ABOUT,
        },
    },
}


def get_fixture(resource_type: str, lang: str = "en") -> dict:
    """Get fixture data for a resource type and language.

    Args:
        resource_type: The CMS resource type (e.g., "footer")
        lang: Language code (default: "en")

    Returns:
        Dictionary with fixture data, or empty dict if not found
    """
    if resource_type not in CMS_FIXTURES:
        return {}

    fixtures = CMS_FIXTURES[resource_type]

    # Try requested language, fall back to English
    if lang in fixtures:
        return fixtures[lang]
    elif "en" in fixtures:
        return fixtures["en"]
    else:
        # Return first available language
        return next(iter(fixtures.values()), {})


def get_all_fixtures() -> dict:
    """Get all CMS fixtures.

    Returns:
        Dictionary with all fixtures organized by resource_type and lang
    """
    return CMS_FIXTURES

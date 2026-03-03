/**
 * Challenges Dashboard Component
 * Tab 3: Word cloud of most frequently mentioned Open Science challenges
 */

import React, { useState } from "react";

// ─── Constants ─────────────────────────────────────────────────────────────

const REGIONS = [
  "All regions",
  "Africa",
  "Arab States",
  "Asia-Pacific",
  "Europe",
  "Latin America",
  "North America",
];

const CHALLENGE_WORDS = [
  { text: "Policy",         weight: 9  },
  { text: "Knowledge",      weight: 10 },
  { text: "Security",       weight: 8  },
  { text: "Bureaucracy",    weight: 6  },
  { text: "Capacity",       weight: 8  },
  { text: "Inequality",     weight: 7  },
  { text: "Literacy",       weight: 6  },
  { text: "Politics",       weight: 5  },
  { text: "Mistrust",       weight: 8  },
  { text: "Regulation",     weight: 6  },
  { text: "Privacy",        weight: 6  },
  { text: "Patents",        weight: 8  },
  { text: "Infrastructure", weight: 7  },
  { text: "Competition",    weight: 5  },
  { text: "Funding",        weight: 7  },
  { text: "Awareness",      weight: 6  },
  { text: "Access",         weight: 7  },
  { text: "Standards",      weight: 5  },
  { text: "Collaboration",  weight: 6  },
  { text: "Trust",          weight: 7  },
  { text: "Skills",         weight: 6  },
  { text: "Resources",      weight: 7  },
  { text: "Barriers",       weight: 6  },
  { text: "Incentives",     weight: 5  },
];

// ─── Helpers ───────────────────────────────────────────────────────────────

const fontSizes = [0.8, 0.9, 1.0, 1.15, 1.35, 1.6, 1.9, 2.3, 2.8, 3.4];

const getSize = (weight) => {
  const idx = Math.min(
    Math.round(((weight - 5) / 5) * (fontSizes.length - 1)),
    fontSizes.length - 1
  );
  return fontSizes[Math.max(idx, 0)];
};

// ─── Challenges component ──────────────────────────────────────────────────

export const Challenges = () => {
  const [region, setRegion] = useState("All regions");

  return (
    <div className="dash-challenges">
      <div className="dashboard-subheader">
        <strong>
          Most frequently mentioned challenges in the implementation of Open Science.
        </strong>
        <div className="dashboard-subheader-actions">
          <select
            className="dashboard-region-select"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            {REGIONS.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
          <button type="button" className="dash-btn outline">
            Download ⬇
          </button>
        </div>
      </div>

      <div className="word-cloud-container">
        {CHALLENGE_WORDS.map((w) => (
          <span
            key={w.text}
            className="word-cloud-item"
            style={{ fontSize: `${getSize(w.weight)}rem` }}
          >
            {w.text}
          </span>
        ))}
      </div>
    </div>
  );
};

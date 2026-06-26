/**
 * ComingSoonWrap
 * Wraps a download trigger so that, while downloads are disabled
 * (`DOWNLOAD_COMING_SOON`), hovering shows a "Coming soon" tooltip below the
 * button — matching the desktop hover-tooltip pattern used by InfoIcon.
 * When downloads are enabled it renders its children untouched.
 */

import React from "react";
import PropTypes from "prop-types";
import { DOWNLOAD_COMING_SOON, COMING_SOON_MESSAGE } from "../constants";

export const ComingSoonWrap = ({ children }) => {
  if (!DOWNLOAD_COMING_SOON) return children;

  return (
    <span className="coming-soon-wrap">
      {children}
      <span className="coming-soon-tooltip" role="tooltip">
        {COMING_SOON_MESSAGE}
      </span>
    </span>
  );
};

ComingSoonWrap.propTypes = {
  children: PropTypes.node.isRequired,
};

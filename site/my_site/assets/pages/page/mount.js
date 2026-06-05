/**
 * CMS page entry point.
 * Mounts <CmsPage/> under /page; the specific page is selected by the URL
 * hash slug (e.g. /page#about). Hash routing keeps it a single mount point.
 */

import React from "react";
import ReactDOM from "react-dom";
import { CmsPage } from "./index";

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("cms-page-root");
  if (!container) return;
  ReactDOM.render(<CmsPage />, container);
});

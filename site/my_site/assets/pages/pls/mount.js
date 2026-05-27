/**
 * PLS detail entry point.
 * Mounts <PlsDetail/> under /pls/:nid with client-side routing.
 */

import React from "react";
import ReactDOM from "react-dom";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PlsDetail } from "./index";

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("pls-root");
  if (!container) return;
  ReactDOM.render(
    <BrowserRouter basename="/pls">
      <Routes>
        <Route path=":nid" element={<PlsDetail />} />
      </Routes>
    </BrowserRouter>,
    container
  );
});

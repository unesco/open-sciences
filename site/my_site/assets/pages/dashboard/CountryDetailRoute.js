/**
 * CountryDetailRoute
 * Route wrapper that reads `:iso3` from the URL and passes it to CountryDetail.
 */

import React from "react";
import { useParams, useLocation } from "react-router-dom";
import { CountryDetail } from "./components";

export const CountryDetailRoute = ({ onBack }) => {
  const { iso3 } = useParams();
  const location = useLocation();
  const countryName = location.state?.countryName || iso3;

  return (
    <CountryDetail
      iso3={iso3}
      countryName={countryName}
      onBack={onBack}
    />
  );
};

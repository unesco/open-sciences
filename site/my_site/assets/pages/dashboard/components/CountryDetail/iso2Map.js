// ISO-3166-1 alpha-3 → alpha-2 mapping.
// flagcdn.com and most flag CDNs require the alpha-2 code.

export const ISO3_TO_ISO2 = {
  AFG: "AF", ALB: "AL", DZA: "DZ", AND: "AD", AGO: "AO", ATG: "AG", ARG: "AR",
  ARM: "AM", AUS: "AU", AUT: "AT", AZE: "AZ", BHS: "BS", BHR: "BH", BGD: "BD",
  BRB: "BB", BLR: "BY", BEL: "BE", BLZ: "BZ", BEN: "BJ", BTN: "BT", BOL: "BO",
  BIH: "BA", BWA: "BW", BRA: "BR", BRN: "BN", BGR: "BG", BFA: "BF", BDI: "BI",
  CPV: "CV", KHM: "KH", CMR: "CM", CAN: "CA", CAF: "CF", TCD: "TD", CHL: "CL",
  CHN: "CN", COL: "CO", COM: "KM", COG: "CG", COD: "CD", CRI: "CR", CIV: "CI",
  HRV: "HR", CUB: "CU", CYP: "CY", CZE: "CZ", DNK: "DK", DJI: "DJ", DMA: "DM",
  DOM: "DO", ECU: "EC", EGY: "EG", SLV: "SV", GNQ: "GQ", ERI: "ER", EST: "EE",
  SWZ: "SZ", ETH: "ET", FJI: "FJ", FIN: "FI", FRA: "FR", GAB: "GA", GMB: "GM",
  GEO: "GE", DEU: "DE", GHA: "GH", GRC: "GR", GRD: "GD", GTM: "GT", GIN: "GN",
  GNB: "GW", GUY: "GY", HTI: "HT", HND: "HN", HUN: "HU", ISL: "IS", IND: "IN",
  IDN: "ID", IRN: "IR", IRQ: "IQ", IRL: "IE", ISR: "IL", ITA: "IT", JAM: "JM",
  JPN: "JP", JOR: "JO", KAZ: "KZ", KEN: "KE", KIR: "KI", PRK: "KP", KOR: "KR",
  KWT: "KW", KGZ: "KG", LAO: "LA", LVA: "LV", LBN: "LB", LSO: "LS", LBR: "LR",
  LBY: "LY", LIE: "LI", LTU: "LT", LUX: "LU", MDG: "MG", MWI: "MW", MYS: "MY",
  MDV: "MV", MLI: "ML", MLT: "MT", MHL: "MH", MRT: "MR", MUS: "MU", MEX: "MX",
  FSM: "FM", MDA: "MD", MCO: "MC", MNG: "MN", MNE: "ME", MAR: "MA", MOZ: "MZ",
  MMR: "MM", NAM: "NA", NRU: "NR", NPL: "NP", NLD: "NL", NZL: "NZ", NIC: "NI",
  NER: "NE", NGA: "NG", MKD: "MK", NOR: "NO", OMN: "OM", PAK: "PK", PLW: "PW",
  PSE: "PS", PAN: "PA", PNG: "PG", PRY: "PY", PER: "PE", PHL: "PH", POL: "PL",
  PRT: "PT", QAT: "QA", ROU: "RO", RUS: "RU", RWA: "RW", KNA: "KN", LCA: "LC",
  VCT: "VC", WSM: "WS", SMR: "SM", STP: "ST", SAU: "SA", SEN: "SN", SRB: "RS",
  SYC: "SC", SLE: "SL", SGP: "SG", SVK: "SK", SVN: "SI", SLB: "SB", SOM: "SO",
  ZAF: "ZA", SSD: "SS", ESP: "ES", LKA: "LK", SDN: "SD", SUR: "SR", SWE: "SE",
  CHE: "CH", SYR: "SY", TJK: "TJ", TZA: "TZ", THA: "TH", TLS: "TL", TGO: "TG",
  TON: "TO", TTO: "TT", TUN: "TN", TUR: "TR", TKM: "TM", TUV: "TV", UGA: "UG",
  UKR: "UA", ARE: "AE", GBR: "GB", USA: "US", URY: "UY", UZB: "UZ", VUT: "VU",
  VAT: "VA", VEN: "VE", VNM: "VN", YEM: "YE", ZMB: "ZM", ZWE: "ZW",
  // Common observers / non-UN-member territories
  TWN: "TW", HKG: "HK", MAC: "MO", PRI: "PR", COK: "CK", NIU: "NU",
};

export function iso3ToIso2(iso3) {
  if (!iso3) return "";
  return ISO3_TO_ISO2[iso3.toUpperCase()] || "";
}

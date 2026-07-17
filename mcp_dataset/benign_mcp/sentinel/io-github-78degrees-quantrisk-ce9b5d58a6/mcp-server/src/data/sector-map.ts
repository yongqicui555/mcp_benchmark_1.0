/**
 * Fallback ticker → GICS sector mapping for common US stocks.
 *
 * Used when Alpha Vantage metadata is unavailable (rate-limited, network error,
 * or the ticker is not covered). Covers all S&P 500 mega-caps and a broad
 * selection of large/mid-cap names (~240 tickers).
 *
 * GICS sector names used throughout this map:
 *   "Information Technology"
 *   "Financials"
 *   "Health Care"
 *   "Consumer Discretionary"
 *   "Consumer Staples"
 *   "Energy"
 *   "Materials"
 *   "Industrials"
 *   "Utilities"
 *   "Real Estate"
 *   "Communication Services"
 *
 * If a ticker is not found here and Alpha Vantage also fails,
 * callers should default to "Unknown" and apply market-level shocks.
 */

export const SECTOR_MAP: Record<string, string> = {

  // ═══════════════════════════════════════════════════════════════════════════
  // INFORMATION TECHNOLOGY
  // ═══════════════════════════════════════════════════════════════════════════

  AAPL:   "Information Technology",   // Apple
  MSFT:   "Information Technology",   // Microsoft
  NVDA:   "Information Technology",   // NVIDIA
  AVGO:   "Information Technology",   // Broadcom
  ORCL:   "Information Technology",   // Oracle
  CRM:    "Information Technology",   // Salesforce
  AMD:    "Information Technology",   // Advanced Micro Devices
  QCOM:   "Information Technology",   // Qualcomm
  TXN:    "Information Technology",   // Texas Instruments
  AMAT:   "Information Technology",   // Applied Materials
  INTC:   "Information Technology",   // Intel
  MU:     "Information Technology",   // Micron Technology
  KLAC:   "Information Technology",   // KLA Corporation
  LRCX:   "Information Technology",   // Lam Research
  MRVL:   "Information Technology",   // Marvell Technology
  SNPS:   "Information Technology",   // Synopsys
  CDNS:   "Information Technology",   // Cadence Design
  APH:    "Information Technology",   // Amphenol
  FTNT:   "Information Technology",   // Fortinet
  PANW:   "Information Technology",   // Palo Alto Networks
  CRWD:   "Information Technology",   // CrowdStrike
  NOW:    "Information Technology",   // ServiceNow
  ADBE:   "Information Technology",   // Adobe
  INTU:   "Information Technology",   // Intuit
  IBM:    "Information Technology",   // IBM
  ACN:    "Information Technology",   // Accenture
  CSCO:   "Information Technology",   // Cisco
  HPQ:    "Information Technology",   // HP Inc.
  HPE:    "Information Technology",   // Hewlett Packard Enterprise
  DELL:   "Information Technology",   // Dell Technologies
  STX:    "Information Technology",   // Seagate
  WDC:    "Information Technology",   // Western Digital
  GLW:    "Information Technology",   // Corning
  TEL:    "Information Technology",   // TE Connectivity
  KEYS:   "Information Technology",   // Keysight
  ANSS:   "Information Technology",   // ANSYS
  CTSH:   "Information Technology",   // Cognizant
  MSI:    "Information Technology",   // Motorola Solutions
  GEN:    "Information Technology",   // Gen Digital
  ZBRA:   "Information Technology",   // Zebra Technologies
  IT:     "Information Technology",   // Gartner
  GDDY:   "Information Technology",   // GoDaddy
  EPAM:   "Information Technology",   // EPAM Systems
  FFIV:   "Information Technology",   // F5 Networks
  JNPR:   "Information Technology",   // Juniper Networks
  NTAP:   "Information Technology",   // NetApp
  FSLR:   "Information Technology",   // First Solar (panels; GICS = IT)
  ENPH:   "Information Technology",   // Enphase Energy (GICS = IT)
  SEDG:   "Information Technology",   // SolarEdge (GICS = IT)

  // ═══════════════════════════════════════════════════════════════════════════
  // COMMUNICATION SERVICES
  // ═══════════════════════════════════════════════════════════════════════════

  GOOGL:  "Communication Services",   // Alphabet Class A
  GOOG:   "Communication Services",   // Alphabet Class C
  META:   "Communication Services",   // Meta Platforms
  NFLX:   "Communication Services",   // Netflix
  DIS:    "Communication Services",   // Walt Disney
  CMCSA:  "Communication Services",   // Comcast
  VZ:     "Communication Services",   // Verizon
  T:      "Communication Services",   // AT&T
  TMUS:   "Communication Services",   // T-Mobile
  CHTR:   "Communication Services",   // Charter Communications
  WBD:    "Communication Services",   // Warner Bros. Discovery
  PARA:   "Communication Services",   // Paramount Global
  FOX:    "Communication Services",   // Fox Corporation
  FOXA:   "Communication Services",   // Fox Corporation Class A
  LYV:    "Communication Services",   // Live Nation
  EA:     "Communication Services",   // Electronic Arts
  TTWO:   "Communication Services",   // Take-Two Interactive
  ATVI:   "Communication Services",   // Activision Blizzard
  MTCH:   "Communication Services",   // Match Group
  IAC:    "Communication Services",   // IAC/InterActiveCorp
  ZM:     "Communication Services",   // Zoom Video

  // ═══════════════════════════════════════════════════════════════════════════
  // CONSUMER DISCRETIONARY
  // ═══════════════════════════════════════════════════════════════════════════

  AMZN:   "Consumer Discretionary",   // Amazon
  TSLA:   "Consumer Discretionary",   // Tesla
  HD:     "Consumer Discretionary",   // Home Depot
  MCD:    "Consumer Discretionary",   // McDonald's
  NKE:    "Consumer Discretionary",   // Nike
  LOW:    "Consumer Discretionary",   // Lowe's
  SBUX:   "Consumer Discretionary",   // Starbucks
  TJX:    "Consumer Discretionary",   // TJX Companies
  BKNG:   "Consumer Discretionary",   // Booking Holdings
  GM:     "Consumer Discretionary",   // General Motors
  F:      "Consumer Discretionary",   // Ford Motor
  ABNB:   "Consumer Discretionary",   // Airbnb
  EBAY:   "Consumer Discretionary",   // eBay
  ETSY:   "Consumer Discretionary",   // Etsy
  ROST:   "Consumer Discretionary",   // Ross Stores
  ORLY:   "Consumer Discretionary",   // O'Reilly Automotive
  AZO:    "Consumer Discretionary",   // AutoZone
  CMG:    "Consumer Discretionary",   // Chipotle
  YUM:    "Consumer Discretionary",   // Yum! Brands
  DRI:    "Consumer Discretionary",   // Darden Restaurants
  HLT:    "Consumer Discretionary",   // Hilton
  MAR:    "Consumer Discretionary",   // Marriott
  LVS:    "Consumer Discretionary",   // Las Vegas Sands
  WYNN:   "Consumer Discretionary",   // Wynn Resorts
  MGM:    "Consumer Discretionary",   // MGM Resorts
  EXPE:   "Consumer Discretionary",   // Expedia
  LYFT:   "Consumer Discretionary",   // Lyft
  UBER:   "Consumer Discretionary",   // Uber
  VFC:    "Consumer Discretionary",   // VF Corporation
  PVH:    "Consumer Discretionary",   // PVH Corp
  RL:     "Consumer Discretionary",   // Ralph Lauren
  TPR:    "Consumer Discretionary",   // Tapestry
  WHR:    "Consumer Discretionary",   // Whirlpool
  LEG:    "Consumer Discretionary",   // Leggett & Platt
  BBY:    "Consumer Discretionary",   // Best Buy
  DLTR:   "Consumer Discretionary",   // Dollar Tree
  DG:     "Consumer Discretionary",   // Dollar General

  // ═══════════════════════════════════════════════════════════════════════════
  // CONSUMER STAPLES
  // ═══════════════════════════════════════════════════════════════════════════

  WMT:    "Consumer Staples",         // Walmart
  PG:     "Consumer Staples",         // Procter & Gamble
  KO:     "Consumer Staples",         // Coca-Cola
  PEP:    "Consumer Staples",         // PepsiCo
  COST:   "Consumer Staples",         // Costco
  PM:     "Consumer Staples",         // Philip Morris
  MO:     "Consumer Staples",         // Altria
  MDLZ:   "Consumer Staples",         // Mondelez
  CL:     "Consumer Staples",         // Colgate-Palmolive
  KMB:    "Consumer Staples",         // Kimberly-Clark
  GIS:    "Consumer Staples",         // General Mills
  K:      "Consumer Staples",         // Kellanova (Kellogg's)
  CAG:    "Consumer Staples",         // Conagra Brands
  HRL:    "Consumer Staples",         // Hormel Foods
  SJM:    "Consumer Staples",         // J.M. Smucker
  CPB:    "Consumer Staples",         // Campbell Soup
  HSY:    "Consumer Staples",         // Hershey
  MKC:    "Consumer Staples",         // McCormick
  CLX:    "Consumer Staples",         // Clorox
  CHD:    "Consumer Staples",         // Church & Dwight
  EL:     "Consumer Staples",         // Estee Lauder
  KR:     "Consumer Staples",         // Kroger
  SYY:    "Consumer Staples",         // Sysco
  ADM:    "Consumer Staples",         // Archer-Daniels-Midland
  BG:     "Consumer Staples",         // Bunge
  TSN:    "Consumer Staples",         // Tyson Foods

  // ═══════════════════════════════════════════════════════════════════════════
  // HEALTH CARE
  // ═══════════════════════════════════════════════════════════════════════════

  LLY:    "Health Care",              // Eli Lilly
  UNH:    "Health Care",              // UnitedHealth Group
  JNJ:    "Health Care",              // Johnson & Johnson
  ABBV:   "Health Care",              // AbbVie
  MRK:    "Health Care",              // Merck
  PFE:    "Health Care",              // Pfizer
  TMO:    "Health Care",              // Thermo Fisher Scientific
  ABT:    "Health Care",              // Abbott Laboratories
  DHR:    "Health Care",              // Danaher
  BMY:    "Health Care",              // Bristol-Myers Squibb
  AMGN:   "Health Care",              // Amgen
  GILD:   "Health Care",              // Gilead Sciences
  BIIB:   "Health Care",              // Biogen
  REGN:   "Health Care",              // Regeneron
  VRTX:   "Health Care",              // Vertex Pharmaceuticals
  MRNA:   "Health Care",              // Moderna
  ISRG:   "Health Care",              // Intuitive Surgical
  SYK:    "Health Care",              // Stryker
  BSX:    "Health Care",              // Boston Scientific
  MDT:    "Health Care",              // Medtronic
  ZBH:    "Health Care",              // Zimmer Biomet
  BAX:    "Health Care",              // Baxter International
  BDX:    "Health Care",              // Becton Dickinson
  EW:     "Health Care",              // Edwards Lifesciences
  HOLX:   "Health Care",              // Hologic
  DXCM:   "Health Care",              // DexCom
  IDXX:   "Health Care",              // IDEXX Laboratories
  IQV:    "Health Care",              // IQVIA Holdings
  CVS:    "Health Care",              // CVS Health
  CI:     "Health Care",              // Cigna
  HUM:    "Health Care",              // Humana
  ELV:    "Health Care",              // Elevance Health
  CNC:    "Health Care",              // Centene
  MOH:    "Health Care",              // Molina Healthcare
  HCA:    "Health Care",              // HCA Healthcare
  THC:    "Health Care",              // Tenet Healthcare
  MCK:    "Health Care",              // McKesson
  AHH:    "Health Care",              // (placeholder)
  CAH:    "Health Care",              // Cardinal Health
  ABC:    "Health Care",              // AmerisourceBergen / Cencora

  // ═══════════════════════════════════════════════════════════════════════════
  // FINANCIALS
  // ═══════════════════════════════════════════════════════════════════════════

  BRK:    "Financials",               // Berkshire Hathaway (generic)
  BRKA:   "Financials",               // Berkshire Hathaway A
  BRKB:   "Financials",               // Berkshire Hathaway B
  JPM:    "Financials",               // JPMorgan Chase
  BAC:    "Financials",               // Bank of America
  WFC:    "Financials",               // Wells Fargo
  GS:     "Financials",               // Goldman Sachs
  MS:     "Financials",               // Morgan Stanley
  C:      "Financials",               // Citigroup
  USB:    "Financials",               // U.S. Bancorp
  PNC:    "Financials",               // PNC Financial
  TFC:    "Financials",               // Truist Financial
  COF:    "Financials",               // Capital One
  AXP:    "Financials",               // American Express
  V:      "Financials",               // Visa
  MA:     "Financials",               // Mastercard
  PYPL:   "Financials",               // PayPal
  SQ:     "Financials",               // Block (Square)
  SCHW:   "Financials",               // Charles Schwab
  BLK:    "Financials",               // BlackRock
  SPGI:   "Financials",               // S&P Global
  MCO:    "Financials",               // Moody's
  ICE:    "Financials",               // Intercontinental Exchange
  CME:    "Financials",               // CME Group
  CBOE:   "Financials",               // Cboe Global Markets
  AON:    "Financials",               // Aon
  MMC:    "Financials",               // Marsh McLennan
  PRU:    "Financials",               // Prudential Financial
  MET:    "Financials",               // MetLife
  AFL:    "Financials",               // Aflac
  AIG:    "Financials",               // American International Group
  ALL:    "Financials",               // Allstate
  PGR:    "Financials",               // Progressive
  CB:     "Financials",               // Chubb
  HIG:    "Financials",               // Hartford Financial
  TRV:    "Financials",               // Travelers Companies
  RF:     "Financials",               // Regions Financial
  FITB:   "Financials",               // Fifth Third Bancorp
  HBAN:   "Financials",               // Huntington Bancshares
  KEY:    "Financials",               // KeyCorp
  CFG:    "Financials",               // Citizens Financial
  MTB:    "Financials",               // M&T Bank
  STT:    "Financials",               // State Street
  BK:     "Financials",               // Bank of New York Mellon
  FDS:    "Financials",               // FactSet Research
  FI:     "Financials",               // Fiserv
  FIS:    "Financials",               // Fidelity National Information Services
  GPN:    "Financials",               // Global Payments

  // ═══════════════════════════════════════════════════════════════════════════
  // ENERGY
  // ═══════════════════════════════════════════════════════════════════════════

  XOM:    "Energy",                   // ExxonMobil
  CVX:    "Energy",                   // Chevron
  COP:    "Energy",                   // ConocoPhillips
  EOG:    "Energy",                   // EOG Resources
  SLB:    "Energy",                   // Schlumberger / SLB
  PXD:    "Energy",                   // Pioneer Natural Resources
  MPC:    "Energy",                   // Marathon Petroleum
  PSX:    "Energy",                   // Phillips 66
  VLO:    "Energy",                   // Valero Energy
  OXY:    "Energy",                   // Occidental Petroleum
  HES:    "Energy",                   // Hess
  HAL:    "Energy",                   // Halliburton
  DVN:    "Energy",                   // Devon Energy
  FANG:   "Energy",                   // Diamondback Energy
  BKR:    "Energy",                   // Baker Hughes
  KMI:    "Energy",                   // Kinder Morgan
  OKE:    "Energy",                   // ONEOK
  WMB:    "Energy",                   // Williams Companies
  ET:     "Energy",                   // Energy Transfer
  EPD:    "Energy",                   // Enterprise Products Partners
  CTRA:   "Energy",                   // Coterra Energy
  APA:    "Energy",                   // APA Corporation
  MRO:    "Energy",                   // Marathon Oil
  XEC:    "Energy",                   // Cimarex (now Coterra)
  CHK:    "Energy",                   // Chesapeake Energy

  // ═══════════════════════════════════════════════════════════════════════════
  // INDUSTRIALS
  // ═══════════════════════════════════════════════════════════════════════════

  RTX:    "Industrials",              // Raytheon Technologies
  HON:    "Industrials",              // Honeywell
  UPS:    "Industrials",              // United Parcel Service
  CAT:    "Industrials",              // Caterpillar
  DE:     "Industrials",              // Deere & Company
  BA:     "Industrials",              // Boeing
  LMT:    "Industrials",              // Lockheed Martin
  GE:     "Industrials",              // GE Aerospace
  NOC:    "Industrials",              // Northrop Grumman
  GD:     "Industrials",              // General Dynamics
  L3HT:   "Industrials",              // L3Harris Technologies
  TDG:    "Industrials",              // TransDigm
  HWM:    "Industrials",              // Howmet Aerospace
  SPX:    "Industrials",              // SPX Technologies
  ITW:    "Industrials",              // Illinois Tool Works
  EMR:    "Industrials",              // Emerson Electric
  ETN:    "Industrials",              // Eaton
  ROK:    "Industrials",              // Rockwell Automation
  PH:     "Industrials",              // Parker Hannifin
  DOV:    "Industrials",              // Dover
  AME:    "Industrials",              // AMETEK
  FTV:    "Industrials",              // Fortive
  GWW:    "Industrials",              // W.W. Grainger
  FAST:   "Industrials",              // Fastenal
  RSG:    "Industrials",              // Republic Services
  WM:     "Industrials",              // Waste Management
  VRSK:   "Industrials",              // Verisk Analytics
  FDX:    "Industrials",              // FedEx
  XPO:    "Industrials",              // XPO Logistics
  JBHT:   "Industrials",              // J.B. Hunt Transport
  CSX:    "Industrials",              // CSX
  NSC:    "Industrials",              // Norfolk Southern
  UNP:    "Industrials",              // Union Pacific
  CP:     "Industrials",              // Canadian Pacific Kansas City
  CNI:    "Industrials",              // Canadian National Railway
  UAL:    "Industrials",              // United Airlines
  DAL:    "Industrials",              // Delta Air Lines
  AAL:    "Industrials",              // American Airlines
  LUV:    "Industrials",              // Southwest Airlines
  CCL:    "Industrials",              // Carnival Corporation
  RCL:    "Industrials",              // Royal Caribbean

  // ═══════════════════════════════════════════════════════════════════════════
  // MATERIALS
  // ═══════════════════════════════════════════════════════════════════════════

  LIN:    "Materials",                // Linde
  APD:    "Materials",                // Air Products
  SHW:    "Materials",                // Sherwin-Williams
  FCX:    "Materials",                // Freeport-McMoRan
  NEM:    "Materials",                // Newmont
  NUE:    "Materials",                // Nucor
  STLD:   "Materials",                // Steel Dynamics
  MLM:    "Materials",                // Martin Marietta Materials
  VMC:    "Materials",                // Vulcan Materials
  ECL:    "Materials",                // Ecolab
  IFF:    "Materials",                // International Flavors
  PPG:    "Materials",                // PPG Industries
  RPM:    "Materials",                // RPM International
  CF:     "Materials",                // CF Industries
  MOS:    "Materials",                // The Mosaic Company
  DD:     "Materials",                // DuPont
  DOW:    "Materials",                // Dow
  LYB:    "Materials",                // LyondellBasell
  EMN:    "Materials",                // Eastman Chemical
  CE:     "Materials",                // Celanese
  PKG:    "Materials",                // Packaging Corp of America
  IP:     "Materials",                // International Paper
  WRK:    "Materials",                // WestRock
  AVY:    "Materials",                // Avery Dennison
  SEE:    "Materials",                // Sealed Air

  // ═══════════════════════════════════════════════════════════════════════════
  // UTILITIES
  // ═══════════════════════════════════════════════════════════════════════════

  NEE:    "Utilities",                // NextEra Energy
  SO:     "Utilities",                // Southern Company
  DUK:    "Utilities",                // Duke Energy
  AEP:    "Utilities",                // American Electric Power
  EXC:    "Utilities",                // Exelon
  XEL:    "Utilities",                // Xcel Energy
  PCG:    "Utilities",                // PG&E
  SRE:    "Utilities",                // Sempra Energy
  ED:     "Utilities",                // Consolidated Edison
  WEC:    "Utilities",                // WEC Energy Group
  ES:     "Utilities",                // Eversource Energy
  AWK:    "Utilities",                // American Water Works
  CNP:    "Utilities",                // CenterPoint Energy
  LNT:    "Utilities",                // Alliant Energy
  NRG:    "Utilities",                // NRG Energy
  ETR:    "Utilities",                // Entergy
  FE:     "Utilities",                // FirstEnergy
  PPL:    "Utilities",                // PPL Corporation
  AEE:    "Utilities",                // Ameren
  DTE:    "Utilities",                // DTE Energy
  EIX:    "Utilities",                // Edison International
  PNW:    "Utilities",                // Pinnacle West Capital
  EVRG:   "Utilities",                // Evergy
  OGE:    "Utilities",                // OGE Energy

  // ═══════════════════════════════════════════════════════════════════════════
  // REAL ESTATE
  // ═══════════════════════════════════════════════════════════════════════════

  AMT:    "Real Estate",              // American Tower
  PLD:    "Real Estate",              // Prologis
  CCI:    "Real Estate",              // Crown Castle
  EQIX:   "Real Estate",              // Equinix
  PSA:    "Real Estate",              // Public Storage
  WELL:   "Real Estate",              // Welltower
  DLR:    "Real Estate",              // Digital Realty
  O:      "Real Estate",              // Realty Income
  SPG:    "Real Estate",              // Simon Property Group
  AVB:    "Real Estate",              // AvalonBay Communities
  EQR:    "Real Estate",              // Equity Residential
  ARE:    "Real Estate",              // Alexandria Real Estate
  VICI:   "Real Estate",              // VICI Properties
  CBRE:   "Real Estate",              // CBRE Group
  IRM:    "Real Estate",              // Iron Mountain
  SBAC:   "Real Estate",              // SBA Communications
  WY:     "Real Estate",              // Weyerhaeuser
  KIM:    "Real Estate",              // Kimco Realty
  REG:    "Real Estate",              // Regency Centers
  FRT:    "Real Estate",              // Federal Realty
  HST:    "Real Estate",              // Host Hotels & Resorts
  MAA:    "Real Estate",              // Mid-America Apartment
  UDR:    "Real Estate",              // UDR Inc.

  // ═══════════════════════════════════════════════════════════════════════════
  // BROAD-MARKET / INDEX ETFs (return the dominant sector for stress purposes)
  // These are NOT GICS sectors but are commonly passed as "tickers"
  // ═══════════════════════════════════════════════════════════════════════════

  SPY:    "Information Technology",   // S&P 500 — largest sector is IT
  QQQ:    "Information Technology",   // Nasdaq 100 — overwhelmingly IT
  IWM:    "Information Technology",   // Russell 2000 — mixed, IT/Financials
  DIA:    "Industrials",              // Dow Jones Industrial Average
  VTI:    "Information Technology",   // Total Stock Market ETF
  VOO:    "Information Technology",   // Vanguard S&P 500
  IVV:    "Information Technology",   // iShares S&P 500
  GLD:    "Materials",                // SPDR Gold Shares (treat as commodity)
  SLV:    "Materials",                // iShares Silver Trust
  USO:    "Energy",                   // US Oil Fund
  TLT:    "Utilities",                // iShares 20+ Year Treasury (treat as rate-sensitive)
  HYG:    "Financials",               // iShares High Yield Bond
  LQD:    "Financials",               // iShares Investment Grade Bond

};

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

/**
 * Look up the GICS sector for a ticker.
 * Returns "Unknown" if not found in the map.
 */
export function getSectorForTicker(ticker: string): string {
  return SECTOR_MAP[ticker.toUpperCase()] ?? "Unknown";
}

#!/usr/bin/env node
// bin/mcp.mjs - ScraperCity MCP Server (stdio transport)
// Connect from Claude Code / Cursor / any MCP client
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import * as sc from '../lib/client.mjs'

const server = new Server(
  { name: 'scrapercity', version: '1.0.0' },
  { capabilities: { tools: {} } }
)

// ── Tool definitions ──────────────────────────────────────────
const TOOLS = [
  {
    name: 'check_wallet',
    description: 'Check account balance, plan, and billing info. Call this FIRST to verify credits before running any scrape.',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'list_runs',
    description: 'List recent scraper runs with status, lead counts, and costs.',
    inputSchema: {
      type: 'object',
      properties: {
        hours: { type: 'number', description: 'How many hours back to look (default 24, max 168)', default: 24 },
        limit: { type: 'number', description: 'Max runs to return (default 20, max 100)', default: 20 }
      }
    }
  },
  {
    name: 'scrape_apollo',
    description: 'Scrape leads from Apollo.io using a search URL. IMPORTANT: Apollo delivery takes 11-48+ hours. Use webhooks (configure at app.scrapercity.com/dashboard/webhooks) instead of polling. Returns a runId to check status later.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'Full Apollo.io search URL (from the People search page)' },
        count: { type: 'number', description: 'Number of leads to pull (min 500, max 50000)', default: 1000 },
        fileName: { type: 'string', description: 'Name for this export', default: '' }
      },
      required: ['url']
    }
  },
  {
    name: 'scrape_apollo_filters',
    description: 'Scrape leads from Apollo.io using filter parameters instead of a URL. Same 4-day delivery - use webhooks. At least one filter required.',
    inputSchema: {
      type: 'object',
      properties: {
        seniorityLevel: { type: 'string', description: 'e.g. "director", "vp", "c_suite", "manager", "senior"' },
        functionDept: { type: 'string', description: 'e.g. "sales", "marketing", "engineering", "finance"' },
        companyIndustry: { type: 'string', description: 'e.g. "computer software", "financial services"' },
        personCountry: { type: 'string', description: 'e.g. "United States", "United Kingdom"' },
        personState: { type: 'string', description: 'e.g. "California", "New York"' },
        companyCountry: { type: 'string', description: 'Company HQ country' },
        companyState: { type: 'string', description: 'Company HQ state' },
        companySize: { type: 'string', description: 'e.g. "11-50", "51-200", "201-500", "501-1000", "1001-5000"' },
        personTitles: { type: 'array', items: { type: 'string' }, description: 'Specific job titles to target' },
        companyDomains: { type: 'array', items: { type: 'string' }, description: 'Specific company domains' },
        companyKeywords: { type: 'array', items: { type: 'string' }, description: 'Company description keywords' },
        personCities: { type: 'array', items: { type: 'string' }, description: 'Person city filter' },
        companyCities: { type: 'array', items: { type: 'string' }, description: 'Company city filter' },
        hasPhone: { type: 'boolean', description: 'Only return contacts with phone numbers', default: false },
        count: { type: 'number', description: 'Number of leads (min 500, max 50000)', default: 1000 },
        fileName: { type: 'string', description: 'Export name', default: 'Apollo Export' }
      }
    }
  },
  {
    name: 'scrape_maps',
    description: 'Scrape businesses from Google Maps. Returns businesses with names, addresses, phone numbers, websites, emails, ratings. Typically completes in 5-30 minutes.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search keyword, e.g. "plumbers", "dentists", "restaurants"' },
        location: { type: 'string', description: 'City/area, e.g. "Denver, CO", "London, UK"' },
        limit: { type: 'number', description: 'Max places to scrape (default 500)', default: 500 }
      },
      required: ['query', 'location']
    }
  },
  {
    name: 'validate_emails',
    description: 'Validate a list of email addresses. Returns deliverability status, catch-all detection, MX records, and company info. Typically completes in 1-10 minutes.',
    inputSchema: {
      type: 'object',
      properties: {
        emails: { type: 'array', items: { type: 'string' }, description: 'Email addresses to validate' }
      },
      required: ['emails']
    }
  },
  {
    name: 'find_emails',
    description: 'Find business email addresses given a person name and company. Provide first/last name + domain or company name.',
    inputSchema: {
      type: 'object',
      properties: {
        contacts: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              first_name: { type: 'string' },
              last_name: { type: 'string' },
              full_name: { type: 'string', description: 'Alternative to first/last' },
              domain: { type: 'string', description: 'Company domain, e.g. "acme.com"' },
              company_name: { type: 'string', description: 'Alternative to domain' }
            }
          },
          description: 'Contacts to find emails for. Each needs a name AND a company/domain.'
        },
        autoValidateEmails: { type: 'boolean', description: 'Auto-validate found emails', default: false },
        autoFindMobiles: { type: 'boolean', description: 'Auto-find mobile numbers', default: false }
      },
      required: ['contacts']
    }
  },
  {
    name: 'find_mobiles',
    description: 'Find mobile phone numbers from LinkedIn URLs or work emails.',
    inputSchema: {
      type: 'object',
      properties: {
        inputs: { type: 'array', items: { type: 'string' }, description: 'LinkedIn profile URLs or work email addresses' }
      },
      required: ['inputs']
    }
  },
  {
    name: 'find_people',
    description: 'Skip trace / people finder. Look up personal info by name, email, phone, or address.',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'array', items: { type: 'string' }, description: 'Full names to search' },
        email: { type: 'array', items: { type: 'string' }, description: 'Email addresses to search' },
        phone_number: { type: 'array', items: { type: 'string' }, description: 'Phone numbers to search' },
        street_citystatezip: { type: 'array', items: { type: 'string' }, description: 'Addresses (format: "123 Main St, City, ST 12345")' },
        max_results: { type: 'number', description: 'Results per search (default 1)', default: 1 }
      }
    }
  },
  {
    name: 'scrape_store_leads',
    description: 'Get ecommerce store data (Shopify, WooCommerce, etc). Returns domains, emails, phones, social profiles, revenue estimates. Instant results from cached database.',
    inputSchema: {
      type: 'object',
      properties: {
        platform: { type: 'string', description: 'e.g. "shopify", "woocommerce", "bigcommerce"', default: 'shopify' },
        countryCode: { type: 'string', description: 'e.g. "US", "GB", "CA"' },
        category: { type: 'string', description: 'Store category filter' },
        city: { type: 'string', description: 'City filter' },
        technologies: { type: 'string', description: 'Technology filter' },
        apps: { type: 'string', description: 'Installed app filter' },
        emails: { type: 'boolean', description: 'Only stores with emails', default: false },
        phones: { type: 'boolean', description: 'Only stores with phones', default: false },
        instagram: { type: 'boolean', description: 'Only stores with Instagram' },
        facebook: { type: 'boolean', description: 'Only stores with Facebook' },
        totalLeads: { type: 'number', description: 'Number of leads to pull', default: 1000 }
      }
    }
  },
  {
    name: 'scrape_builtwith',
    description: 'Find all websites using a specific technology. Returns domains with contact info. $4.99 per search.',
    inputSchema: {
      type: 'object',
      properties: {
        technology: { type: 'string', description: 'Technology name, e.g. "Shopify", "Stripe", "HubSpot"' },
        fileName: { type: 'string', description: 'Export name' }
      },
      required: ['technology']
    }
  },
  {
    name: 'search_criminal_records',
    description: 'Search criminal records by name. $1 per search, only charged if records found.',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Full name to search' },
        state: { type: 'string', description: 'US state code, e.g. "CA", "TX" (optional, searches all if omitted)' },
        dob: { type: 'string', description: 'Date of birth "MM/DD/YYYY" (optional, improves accuracy)' }
      },
      required: ['name']
    }
  },
  {
    name: 'scrape_airbnb',
    description: 'Scrape Airbnb host emails by city or listing URL. Returns host contact info including email addresses.',
    inputSchema: {
      type: 'object',
      properties: {
        mode: { type: 'string', enum: ['city', 'single', 'bulk'], description: 'Search mode', default: 'city' },
        city: { type: 'array', items: { type: 'string' }, description: 'Cities to search (for city mode), e.g. ["Miami, FL"]' },
        listingUrl: { type: 'string', description: 'Single Airbnb listing URL (for single mode)' },
        bulkListings: { type: 'array', items: { type: 'string' }, description: 'Multiple listing URLs (for bulk mode)' },
        maxResults: { type: 'number', description: 'Max results for billing cap', default: 100 },
        checkin: { type: 'string', description: 'Check-in date YYYY-MM-DD' },
        checkout: { type: 'string', description: 'Check-out date YYYY-MM-DD' },
        maxPages: { type: 'number', description: 'Max pages to crawl per city', default: 1 },
        onlyUniqueEmails: { type: 'boolean', description: 'Deduplicate by email', default: false },
        onlyProHosts: { type: 'boolean', description: 'Only professional hosts', default: false }
      }
    }
  },
  {
    name: 'scrape_youtube_email',
    description: 'Find business emails for YouTube channels. Pass channel handles (@ChannelName) or URLs.',
    inputSchema: {
      type: 'object',
      properties: {
        channels: { type: 'array', items: { type: 'string' }, description: 'YouTube channel handles or URLs, e.g. ["@MrBeast", "https://youtube.com/@Channel"]' }
      },
      required: ['channels']
    }
  },
  {
    name: 'scrape_website_finder',
    description: 'Find contact info (emails, phones, social links) from a list of website domains. Optionally filter by job title.',
    inputSchema: {
      type: 'object',
      properties: {
        domains: { type: 'array', items: { type: 'string' }, description: 'Website domains, e.g. ["acme.com", "example.com"]' },
        jobTitle: { type: 'string', description: 'Filter contacts by job title, e.g. "CEO"' }
      },
      required: ['domains']
    }
  },
  {
    name: 'scrape_yelp',
    description: 'Scrape business listings from Yelp. Search by keyword + location, or provide direct Yelp URLs.',
    inputSchema: {
      type: 'object',
      properties: {
        searchTerms: { type: 'array', items: { type: 'string' }, description: 'Search keywords, e.g. ["plumbers", "dentists"]' },
        locations: { type: 'array', items: { type: 'string' }, description: 'Locations, e.g. ["Denver, CO"]' },
        directUrls: { type: 'array', items: { type: 'string' }, description: 'Direct Yelp search/business URLs' },
        searchLimit: { type: 'number', description: 'Max results per search', default: 10 }
      }
    }
  },
  {
    name: 'scrape_angi',
    description: 'Scrape service provider listings from Angi (Angie\'s List). Search by keyword and zip codes.',
    inputSchema: {
      type: 'object',
      properties: {
        keyword: { type: 'string', description: 'Service type, e.g. "plumbers", "electricians"' },
        zipCodes: { type: 'array', items: { type: 'string' }, description: 'ZIP codes to search, e.g. ["80202", "80203"]' },
        maxItems: { type: 'number', description: 'Max results', default: 100 }
      },
      required: ['keyword']
    }
  },
  {
    name: 'scrape_zillow_agents',
    description: 'Scrape real estate agent listings from Zillow by location.',
    inputSchema: {
      type: 'object',
      properties: {
        location: { type: 'string', description: 'City or area, e.g. "Denver, CO"' },
        specialty: { type: 'string', description: 'Agent specialty, e.g. "buyer", "seller"' },
        language: { type: 'string', description: 'Language filter' },
        searchLimit: { type: 'number', description: 'Max results', default: 10 }
      },
      required: ['location']
    }
  },
  {
    name: 'scrape_bizbuysell',
    description: 'Scrape business-for-sale listings from BizBuySell. Provide search result URLs.',
    inputSchema: {
      type: 'object',
      properties: {
        startUrls: { type: 'array', items: { type: 'string' }, description: 'BizBuySell search URLs' },
        maxItems: { type: 'number', description: 'Max listings to scrape', default: 100 }
      },
      required: ['startUrls']
    }
  },
  {
    name: 'scrape_crexi',
    description: 'Scrape commercial real estate listings from Crexi. Provide search result URLs.',
    inputSchema: {
      type: 'object',
      properties: {
        startUrls: { type: 'array', items: { type: 'string' }, description: 'Crexi search URLs' }
      },
      required: ['startUrls']
    }
  },
  {
    name: 'scrape_property_lookup',
    description: 'Look up property data by address. Optionally include owner contact information. $0.15 per address.',
    inputSchema: {
      type: 'object',
      properties: {
        addresses: { type: 'array', items: { type: 'string' }, description: 'Full addresses, e.g. ["123 Main St, Denver, CO 80202"]' },
        includeOwnerContact: { type: 'boolean', description: 'Include property owner contact info', default: false }
      },
      required: ['addresses']
    }
  },
  {
    name: 'check_run_status',
    description: 'Check the status of a scraper run. Returns status (RUNNING/SUCCEEDED/FAILED/CANCELLED), lead count, and download URL when complete.',
    inputSchema: {
      type: 'object',
      properties: {
        runId: { type: 'string', description: 'The run ID returned when starting a scrape' }
      },
      required: ['runId']
    }
  },
  {
    name: 'download_results',
    description: 'Download the CSV results of a completed scraper run. Only works when status is SUCCEEDED.',
    inputSchema: {
      type: 'object',
      properties: {
        runId: { type: 'string', description: 'The run ID to download results for' },
        outputPath: { type: 'string', description: 'File path to save CSV (default: {runId}.csv)' }
      },
      required: ['runId']
    }
  },
  {
    name: 'cancel_run',
    description: 'Cancel a running scraper job.',
    inputSchema: {
      type: 'object',
      properties: {
        runId: { type: 'string', description: 'The run ID to cancel' }
      },
      required: ['runId']
    }
  },
  {
    name: 'query_lead_database',
    description: 'Query the B2B lead database directly (requires $649/mo plan). Returns contacts with names, emails, phones, titles, companies. 100 per request, paginate with page param.',
    inputSchema: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Job title filter' },
        industry: { type: 'string', description: 'Company industry' },
        country: { type: 'string', description: 'Person country' },
        state: { type: 'string', description: 'Person state' },
        city: { type: 'string', description: 'Person city' },
        companyName: { type: 'string', description: 'Company name' },
        companyDomain: { type: 'string', description: 'Company domain' },
        seniority: { type: 'string', description: 'e.g. "vp", "director", "c_suite"' },
        department: { type: 'string', description: 'e.g. "sales", "engineering"' },
        hasEmail: { type: 'boolean', description: 'Only contacts with email' },
        hasPhone: { type: 'boolean', description: 'Only contacts with phone' },
        page: { type: 'number', description: 'Page number (default 1)', default: 1 },
        limit: { type: 'number', description: 'Results per page (max 100)', default: 50 }
      }
    }
  }
]

// ── Register tool list handler ────────────────────────────────
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS }
})

// ── Tool execution handler ────────────────────────────────────
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params
  try {
    let result
    switch (name) {
      case 'check_wallet':
        result = await sc.wallet()
        break
      case 'list_runs':
        result = await sc.runs(args?.hours || 24, args?.limit || 20)
        break
      case 'scrape_apollo':
        result = await sc.apollo(args.url, args.count || 1000, args.fileName || '')
        result._note = 'Apollo takes 11-48+ hours. Configure webhook at app.scrapercity.com/dashboard/webhooks instead of polling.'
        break
      case 'scrape_apollo_filters':
        result = await sc.apolloFilters(args)
        result._note = 'Apollo takes 11-48+ hours. Configure webhook at app.scrapercity.com/dashboard/webhooks instead of polling.'
        break
      case 'scrape_maps':
        result = await sc.maps(args.query, args.location, args.limit || 500)
        break
      case 'validate_emails':
        result = await sc.emailValidate(args.emails)
        break
      case 'find_emails':
        result = await sc.emailFind(args.contacts, {
          validate: args.autoValidateEmails || false,
          mobiles: args.autoFindMobiles || false
        })
        break
      case 'find_mobiles':
        result = await sc.mobileFinder(args.inputs)
        break
      case 'find_people':
        result = await sc.peopleFinder(args)
        break
      case 'scrape_store_leads':
        result = await sc.storeLeads(args)
        break
      case 'scrape_builtwith':
        result = await sc.builtwith(args.technology, args.fileName)
        break
      case 'search_criminal_records':
        result = await sc.criminal(args.name, args.state, args.dob)
        break
      case 'scrape_airbnb':
        result = await sc.airbnb(args)
        break
      case 'scrape_youtube_email':
        result = await sc.youtubeEmail(args.channels)
        break
      case 'scrape_website_finder':
        result = await sc.websiteFinder(args.domains, args.jobTitle)
        break
      case 'scrape_yelp':
        result = await sc.yelp(args)
        break
      case 'scrape_angi':
        result = await sc.angi(args.keyword, args.zipCodes || [], args.maxItems || 100)
        break
      case 'scrape_zillow_agents':
        result = await sc.zillowAgents(args.location, { specialty: args.specialty, language: args.language, searchLimit: args.searchLimit || 10 })
        break
      case 'scrape_bizbuysell':
        result = await sc.bizbuysell(args.startUrls, args.maxItems || 100)
        break
      case 'scrape_crexi':
        result = await sc.crexi(args.startUrls)
        break
      case 'scrape_property_lookup':
        result = await sc.propertyLookup(args.addresses, args.includeOwnerContact || false)
        break
      case 'check_run_status':
        result = await sc.status(args.runId)
        break
      case 'download_results': {
        const dl = await sc.download(args.runId, args.outputPath)
        result = { success: true, path: dl.path, sizeKB: Math.round(dl.bytes / 1024) }
        break
      }
      case 'cancel_run':
        result = await sc.cancel(args.runId)
        break
      case 'query_lead_database': {
        const params = { ...args }
        if (params.hasEmail) { params.hasEmail = 'true'; }
        if (params.hasPhone) { params.hasPhone = 'true'; }
        result = await sc.dbLeads(params)
        break
      }
      default:
        return { content: [{ type: 'text', text: `Unknown tool: ${name}` }], isError: true }
    }

    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  } catch (e) {
    return { content: [{ type: 'text', text: `Error: ${e.message}` }], isError: true }
  }
})

// ── Start ─────────────────────────────────────────────────────
const transport = new StdioServerTransport()
await server.connect(transport)

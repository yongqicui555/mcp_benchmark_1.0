#!/usr/bin/env node
// bin/cli.mjs - ScraperCity CLI
import * as sc from '../lib/client.mjs'
import fs from 'fs'
import readline from 'readline'

const [,, cmd, ...args] = process.argv
const flag = (name) => { const i = args.indexOf(name); return i !== -1 ? (args.splice(i, 2), args[i] || true) : undefined }
const flagBool = (name) => { const i = args.indexOf(name); if (i !== -1) { args.splice(i, 1); return true } return false }
const json = (d) => JSON.stringify(d, null, 2)

function die(msg) { console.error(`✗ ${msg}`); process.exit(1) }

async function main() {
  try {
    switch (cmd) {

      // ── Auth ──────────────────────────────────────────────
      case 'login': {
        const key = args[0] || await ask('API key: ')
        sc.saveApiKey(key.trim())
        console.log('✓ Saved to ~/.scrapercityrc')
        break
      }

      // ── Wallet ────────────────────────────────────────────
      case 'wallet': {
        const w = await sc.wallet()
        console.log(`Plan:    ${w.plan.name} ($${w.plan.limit_dollars}/cycle)`)
        console.log(`Balance: $${w.wallet.total_balance_dollars}  (subscription: $${w.wallet.balance_dollars} + purchased: $${w.wallet.purchased_credits_dollars})`)
        console.log(`Used:    $${w.plan.used_dollars} (${w.plan.usage_percent}%)`)
        if (w.billing.next_billing_date) console.log(`Renews:  ${w.billing.next_billing_date}`)
        break
      }

      // ── Runs ──────────────────────────────────────────────
      case 'runs': {
        const hours = flag('--hours') || 24
        const limit = flag('--limit') || 20
        const data = await sc.runs(hours, limit)
        if (!data.runs?.length) { console.log('No runs found.'); break }
        for (const r of data.runs) {
          const cost = r.handled && r.price_per_lead_micro ? `$${((r.handled * r.price_per_lead_micro) / 1e6).toFixed(2)}` : ''
          console.log(`${r.status.padEnd(10)} ${r.run_id.substring(0, 12).padEnd(14)} ${String(r.handled || 0).padEnd(6)} leads  ${cost.padEnd(8)}  ${r.file_name || r.url || ''}`)
        }
        break
      }

      // ── Status ────────────────────────────────────────────
      case 'status': {
        if (!args[0]) die('Usage: scrapercity status <runId>')
        const s = await sc.status(args[0])
        console.log(`Status:    ${s.status}`)
        console.log(`Message:   ${s.statusMessage}`)
        console.log(`Handled:   ${s.handled} / ${s.requested}`)
        if (s.outputUrl) console.log(`Download:  scrapercity download ${args[0]}`)
        break
      }

      // ── Download ──────────────────────────────────────────
      case 'download': {
        if (!args[0]) die('Usage: scrapercity download <runId> [--output file.csv]')
        const out = flag('--output') || flag('-o')
        const result = await sc.download(args[0], out)
        console.log(`✓ ${result.path} (${(result.bytes / 1024).toFixed(1)} KB)`)
        break
      }

      // ── Cancel ────────────────────────────────────────────
      case 'cancel': {
        if (!args[0]) die('Usage: scrapercity cancel <runId>')
        const r = await sc.cancel(args[0])
        console.log(`✓ ${r.message}`)
        break
      }

      // ── Logs ──────────────────────────────────────────────
      case 'logs': {
        if (!args[0]) die('Usage: scrapercity logs <runId>')
        const r = await sc.logs(args[0])
        console.log(r.log || r.logs || json(r))
        break
      }

      // ── Apollo (URL-based) ────────────────────────────────
      case 'apollo': {
        const url = args[0]
        if (!url) die('Usage: scrapercity apollo <apollo-url> [--count 1000] [--name "My Export"]')
        const count = flag('--count') || 1000
        const name = flag('--name') || ''
        const r = await sc.apollo(url, +count, name)
        console.log(`✓ Apollo scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  ${r.message || ''}`)
        console.log(`  Note: Apollo takes up to 4 days. Set up a webhook at app.scrapercity.com/dashboard/webhooks to get notified.`)
        console.log(`  Check: scrapercity status ${r.runId}`)
        break
      }

      // ── Apollo Filters ────────────────────────────────────
      case 'apollo-filters': {
        const filters = {}
        for (const f of ['--seniority', '--function', '--industry', '--country', '--state',
                         '--company-country', '--company-state', '--company-size', '--count', '--name', '--has-phone']) {
          const v = flag(f)
          if (v === undefined) continue
          const key = {
            '--seniority': 'seniorityLevel', '--function': 'functionDept',
            '--industry': 'companyIndustry', '--country': 'personCountry',
            '--state': 'personState', '--company-country': 'companyCountry',
            '--company-state': 'companyState', '--company-size': 'companySize',
            '--count': 'count', '--name': 'fileName', '--has-phone': 'hasPhone'
          }[f]
          filters[key] = f === '--has-phone' ? true : (f === '--count' ? +v : v)
        }
        // Array flags
        for (const f of ['--titles', '--domains', '--keywords', '--person-cities', '--company-cities']) {
          const v = flag(f)
          if (!v) continue
          const key = { '--titles': 'personTitles', '--domains': 'companyDomains',
                        '--keywords': 'companyKeywords', '--person-cities': 'personCities',
                        '--company-cities': 'companyCities' }[f]
          filters[key] = v.split(',').map(s => s.trim())
        }
        if (!Object.keys(filters).length) die('At least one filter required. Example: scrapercity apollo-filters --industry "computer software" --country "United States" --count 1000')
        const r = await sc.apolloFilters(filters)
        console.log(`✓ Apollo filter search started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  ${r.message || ''}`)
        console.log(`  Note: Apollo takes up to 4 days. Set up a webhook to get notified.`)
        break
      }

      // ── Maps ──────────────────────────────────────────────
      case 'maps': {
        const query = flag('--query') || flag('-q')
        const location = flag('--location') || flag('-l')
        const limit = flag('--limit') || 500
        if (!query || !location) die('Usage: scrapercity maps --query "plumbers" --location "Denver, CO" [--limit 500]')
        const r = await sc.maps(query, location, +limit)
        console.log(`✓ Maps scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Email Validate ────────────────────────────────────
      case 'email-validate': {
        let emails = args.filter(a => a.includes('@'))
        const file = flag('--file')
        if (file) {
          const content = fs.readFileSync(file, 'utf-8')
          emails = [...emails, ...content.split('\n').map(l => l.trim()).filter(l => l.includes('@'))]
        }
        if (!emails.length) die('Usage: scrapercity email-validate user@example.com ...  OR  --file emails.txt')
        const r = await sc.emailValidate(emails)
        console.log(`✓ Validating ${r.emailCount || emails.length} emails`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Est. cost: $${r.estimatedCost?.toFixed(2) || 'N/A'}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Email Find ────────────────────────────────────────
      case 'email-find': {
        const first = flag('--first')
        const last = flag('--last')
        const fullName = flag('--full-name')
        const domain = flag('--domain')
        const company = flag('--company')
        const file = flag('--file')
        const validate = flagBool('--validate')
        const mobiles = flagBool('--mobiles')

        let contacts = []
        if (file) {
          // Expect CSV: first_name,last_name,domain
          const lines = fs.readFileSync(file, 'utf-8').split('\n').filter(Boolean)
          const header = lines[0].toLowerCase()
          if (header.includes('first')) {
            for (const line of lines.slice(1)) {
              const [fn, ln, d, cn] = line.split(',').map(s => s.trim())
              contacts.push({ first_name: fn, last_name: ln, domain: d, company_name: cn || '' })
            }
          }
        } else if (first || fullName) {
          contacts.push({ first_name: first || '', last_name: last || '', full_name: fullName || '', domain: domain || '', company_name: company || '' })
        }

        if (!contacts.length) die('Usage: scrapercity email-find --first John --last Doe --domain acme.com  OR  --file contacts.csv')
        const r = await sc.emailFind(contacts, { validate, mobiles })
        console.log(`✓ Finding emails for ${r.contactCount || contacts.length} contacts`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Mobile Finder ─────────────────────────────────────
      case 'mobile-find': {
        let inputs = args.filter(a => !a.startsWith('-'))
        const file = flag('--file')
        if (file) {
          inputs = [...inputs, ...fs.readFileSync(file, 'utf-8').split('\n').map(l => l.trim()).filter(Boolean)]
        }
        if (!inputs.length) die('Usage: scrapercity mobile-find linkedin.com/in/johndoe user@company.com  OR  --file inputs.txt')
        const r = await sc.mobileFinder(inputs)
        console.log(`✓ Finding mobiles for ${r.inputCount || inputs.length} inputs`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── People Finder / Skip Trace ────────────────────────
      case 'people-find': {
        const name = flag('--name')
        const email = flag('--email')
        const phone = flag('--phone')
        const address = flag('--address')
        const maxResults = flag('--max-results') || 1
        const params = { max_results: +maxResults }
        if (name) params.name = name.includes(',') ? name.split(',').map(s => s.trim()) : [name]
        if (email) params.email = email.includes(',') ? email.split(',').map(s => s.trim()) : [email]
        if (phone) params.phone_number = phone.includes(',') ? phone.split(',').map(s => s.trim()) : [phone]
        if (address) params.street_citystatezip = address.includes('|') ? address.split('|').map(s => s.trim()) : [address]
        if (!name && !email && !phone && !address) die('Usage: scrapercity people-find --name "John Doe" [--email a@b.com] [--address "123 Main St, City, ST 12345"]')
        const r = await sc.peopleFinder(params)
        console.log(`✓ People finder started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Est. cost: $${r.estimatedCost?.toFixed(2) || 'N/A'}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Store Leads ───────────────────────────────────────
      case 'store-leads': {
        const params = {}
        for (const f of ['--platform', '--country', '--category', '--city', '--technologies', '--apps', '--total-leads', '--name']) {
          const v = flag(f)
          if (v === undefined) continue
          const key = { '--platform': 'platform', '--country': 'countryCode', '--category': 'category',
                        '--city': 'city', '--technologies': 'technologies', '--apps': 'apps',
                        '--total-leads': 'totalLeads', '--name': 'fileName' }[f]
          params[key] = f === '--total-leads' ? +v : v
        }
        for (const f of ['--emails', '--phones', '--instagram', '--facebook', '--tiktok', '--youtube', '--linkedin']) {
          if (flagBool(f)) params[f.slice(2)] = true
        }
        if (!params.totalLeads) params.totalLeads = 1000
        const r = await sc.storeLeads(params)
        console.log(`✓ Store leads started - ${r.totalLeads || 'N/A'} leads`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Est. cost: $${r.estimatedCost?.toFixed(2) || 'N/A'}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── BuiltWith ─────────────────────────────────────────
      case 'builtwith': {
        const tech = args.filter(a => !a.startsWith('-')).join(' ') || flag('--tech')
        if (!tech) die('Usage: scrapercity builtwith "Shopify"')
        const name = flag('--name')
        const r = await sc.builtwith(tech, name)
        console.log(`✓ BuiltWith search started for "${r.technology}"`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Est. cost: $${r.estimatedCost?.toFixed(2) || 'N/A'}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Criminal Records ──────────────────────────────────
      case 'criminal': {
        const name = flag('--name') || args.filter(a => !a.startsWith('-')).join(' ')
        const state = flag('--state')
        const dob = flag('--dob')
        if (!name) die('Usage: scrapercity criminal --name "John Smith" [--state CA] [--dob 02/07/1992]')
        const r = await sc.criminal(name, state, dob)
        console.log(`✓ Criminal search queued: "${r.name}"`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  State: ${r.state || 'all'}`)
        console.log(`  ${r.note || ''}`)
        break
      }

      // ── Airbnb Email ──────────────────────────────────────
      case 'airbnb': {
        const city = flag('--city')
        const listingUrl = flag('--url')
        const maxResults = flag('--max-results') || flag('--limit') || 100
        const mode = listingUrl ? 'single' : 'city'
        const params = { mode, maxResults: +maxResults }
        if (city) params.city = city.split(',').map(s => s.trim())
        if (listingUrl) params.listingUrl = listingUrl
        const checkin = flag('--checkin'); if (checkin) params.checkin = checkin
        const checkout = flag('--checkout'); if (checkout) params.checkout = checkout
        if (!city && !listingUrl) die('Usage: scrapercity airbnb --city "Miami, FL" --limit 100  OR  --url <airbnb-listing-url>')
        const r = await sc.airbnb(params)
        console.log(`✓ Airbnb scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── YouTube Email ─────────────────────────────────────
      case 'youtube-email': {
        let channels = args.filter(a => !a.startsWith('-'))
        const file = flag('--file')
        if (file) {
          channels = [...channels, ...fs.readFileSync(file, 'utf-8').split('\n').map(l => l.trim()).filter(Boolean)]
        }
        if (!channels.length) die('Usage: scrapercity youtube-email @ChannelHandle https://youtube.com/@Channel  OR  --file channels.txt')
        const r = await sc.youtubeEmail(channels)
        console.log(`✓ YouTube email scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Website Finder ────────────────────────────────────
      case 'website-finder': {
        let domains = args.filter(a => !a.startsWith('-'))
        const file = flag('--file')
        const jobTitle = flag('--title')
        if (file) {
          domains = [...domains, ...fs.readFileSync(file, 'utf-8').split('\n').map(l => l.trim()).filter(Boolean)]
        }
        if (!domains.length) die('Usage: scrapercity website-finder acme.com example.com  OR  --file domains.txt [--title "CEO"]')
        const r = await sc.websiteFinder(domains, jobTitle)
        console.log(`✓ Website finder started for ${domains.length} domains`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Yelp ──────────────────────────────────────────────
      case 'yelp': {
        const searchTerms = flag('--query') || flag('-q')
        const locations = flag('--location') || flag('-l')
        const directUrls = flag('--urls')
        const limit = flag('--limit') || 10
        const params = { searchLimit: +limit }
        if (searchTerms) params.searchTerms = searchTerms.split(',').map(s => s.trim())
        if (locations) params.locations = locations.split(',').map(s => s.trim())
        if (directUrls) params.directUrls = directUrls.split(',').map(s => s.trim())
        if (!searchTerms && !directUrls) die('Usage: scrapercity yelp -q "plumbers" -l "Denver, CO" [--limit 10]  OR  --urls <yelp-urls>')
        const r = await sc.yelp(params)
        console.log(`✓ Yelp scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Angi (Angie's List) ───────────────────────────────
      case 'angi': {
        const keyword = flag('--query') || flag('-q')
        const zipCodes = flag('--zips')
        const maxItems = flag('--limit') || 100
        if (!keyword) die('Usage: scrapercity angi -q "plumbers" --zips "80202,80203" [--limit 100]')
        const zips = zipCodes ? zipCodes.split(',').map(s => s.trim()) : []
        const r = await sc.angi(keyword, zips, +maxItems)
        console.log(`✓ Angi scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Zillow Agents ─────────────────────────────────────
      case 'zillow-agents': {
        const location = flag('--location') || flag('-l')
        const specialty = flag('--specialty')
        const language = flag('--language')
        const limit = flag('--limit') || 10
        if (!location) die('Usage: scrapercity zillow-agents -l "Denver, CO" [--specialty "buyer" ] [--limit 10]')
        const r = await sc.zillowAgents(location, { specialty, language, searchLimit: +limit })
        console.log(`✓ Zillow agents scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── BizBuySell ────────────────────────────────────────
      case 'bizbuysell': {
        const urls = args.filter(a => !a.startsWith('-'))
        const limit = flag('--limit') || 100
        if (!urls.length) die('Usage: scrapercity bizbuysell <bizbuysell-search-url> [--limit 100]')
        const r = await sc.bizbuysell(urls, +limit)
        console.log(`✓ BizBuySell scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Crexi ─────────────────────────────────────────────
      case 'crexi': {
        const urls = args.filter(a => !a.startsWith('-'))
        if (!urls.length) die('Usage: scrapercity crexi <crexi-search-url>')
        const r = await sc.crexi(urls)
        console.log(`✓ Crexi scrape started`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Property Lookup ───────────────────────────────────
      case 'property-lookup': {
        let addresses = args.filter(a => !a.startsWith('-'))
        const file = flag('--file')
        const ownerContact = flagBool('--owner-contact')
        if (file) {
          addresses = [...addresses, ...fs.readFileSync(file, 'utf-8').split('\n').map(l => l.trim()).filter(Boolean)]
        }
        if (!addresses.length) die('Usage: scrapercity property-lookup "123 Main St, Denver, CO 80202" [--owner-contact] OR --file addresses.txt')
        const r = await sc.propertyLookup(addresses, ownerContact)
        console.log(`✓ Property lookup started for ${addresses.length} addresses`)
        console.log(`  Run ID: ${r.runId}`)
        console.log(`  Poll: scrapercity status ${r.runId}`)
        break
      }

      // ── Database: Leads ($649) ────────────────────────────
      case 'db-leads': {
        const params = {}
        for (const f of ['--title', '--industry', '--country', '--state', '--city',
                         '--company', '--domain', '--company-size', '--seniority',
                         '--department', '--page', '--limit', '--min-employees', '--max-employees']) {
          const v = flag(f)
          if (v === undefined) continue
          const key = { '--title': 'title', '--industry': 'industry', '--country': 'country',
                        '--state': 'state', '--city': 'city', '--company': 'companyName',
                        '--domain': 'companyDomain', '--company-size': 'companySize',
                        '--seniority': 'seniority', '--department': 'department',
                        '--page': 'page', '--limit': 'limit',
                        '--min-employees': 'minEmployees', '--max-employees': 'maxEmployees' }[f]
          params[key] = v
        }
        if (flagBool('--has-email')) params.hasEmail = 'true'
        if (flagBool('--has-phone')) params.hasPhone = 'true'
        const r = await sc.dbLeads(params)
        console.log(`${r.pagination?.total || '?'} total leads, page ${r.pagination?.page || 1} of ${r.pagination?.totalPages || '?'}`)
        console.log(json(r.data?.slice(0, 3) || r))
        if (r.data?.length > 3) console.log(`... and ${r.data.length - 3} more`)
        break
      }

      // ── Poll (convenience) ────────────────────────────────
      case 'poll': {
        if (!args[0]) die('Usage: scrapercity poll <runId> [--interval 15]')
        const interval = +(flag('--interval') || 15) * 1000
        console.log(`Polling ${args[0]} every ${interval / 1000}s...`)
        const result = await sc.pollUntilDone(args[0], {
          interval,
          onStatus: (s) => process.stdout.write(`\r  ${s.status} - ${s.handled}/${s.requested} leads`)
        })
        console.log(`\n✓ Done: ${result.handled} leads`)
        console.log(`  Download: scrapercity download ${args[0]}`)
        break
      }

      // ── Help ──────────────────────────────────────────────
      case 'help': case '--help': case '-h': case undefined: {
        console.log(`
ScraperCity CLI - B2B lead generation from your terminal

  Auth:
    scrapercity login [key]                  Save API key to ~/.scrapercityrc
    scrapercity wallet                       Check balance and plan

  Scrapers:
    scrapercity apollo <url> [--count N]     Apollo scrape (URL-based, ~4 day delivery)
    scrapercity apollo-filters [filters]     Apollo scrape (filter-based)
    scrapercity maps -q <query> -l <loc>     Google Maps scrape
    scrapercity email-validate <emails>      Validate email addresses
    scrapercity email-find --first X --last Y --domain Z    Find business emails
    scrapercity mobile-find <linkedin/email> Find mobile numbers
    scrapercity people-find --name "X"       Skip trace / people finder
    scrapercity store-leads [--platform X]   Ecommerce store leads
    scrapercity builtwith "Technology"       Sites using a technology
    scrapercity criminal --name "X"          Criminal records search
    scrapercity airbnb --city "Miami, FL"    Airbnb host emails
    scrapercity youtube-email @Channel       YouTuber business emails
    scrapercity website-finder acme.com      Contact info from domains
    scrapercity yelp -q "query" -l "City"    Yelp business scraper
    scrapercity angi -q "query" --zips X     Angi (Angie's List) scraper
    scrapercity zillow-agents -l "City"      Zillow real estate agents
    scrapercity bizbuysell <url>             BizBuySell listings
    scrapercity crexi <url>                  Crexi commercial real estate
    scrapercity property-lookup "address"    Property data + owner contact

  Status:
    scrapercity status <runId>               Check run status
    scrapercity poll <runId>                 Poll until complete
    scrapercity download <runId> [-o f.csv]  Download results CSV
    scrapercity cancel <runId>               Cancel a running scrape
    scrapercity logs <runId>                 View run logs
    scrapercity runs [--hours 24]            List recent runs

  Database ($649 plan):
    scrapercity db-leads [filters]           Query lead database

  Env: SCRAPERCITY_API_KEY=...  or  scrapercity login
  Docs: https://scrapercity.com/agents
`)
        break
      }

      default:
        die(`Unknown command: ${cmd}. Run: scrapercity help`)
    }
  } catch (e) {
    die(e.message)
  }
}

function ask(prompt) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stderr })
  return new Promise(resolve => rl.question(prompt, (a) => { rl.close(); resolve(a) }))
}

main()

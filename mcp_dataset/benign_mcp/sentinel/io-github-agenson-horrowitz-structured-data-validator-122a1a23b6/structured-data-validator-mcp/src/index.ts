#!/usr/bin/env node

/**
 * Structured Data Validator & Transformer MCP Server
 * Built by Agenson Horrowitz for the AI agent ecosystem
 * 
 * Provides tools for validating, transforming, and normalizing structured data
 * Specifically designed for AI agents processing messy, inconsistent data
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import Ajv from 'ajv';
import { parse as parseCsv } from 'csv-parse/sync';
import { parsePhoneNumber } from 'libphonenumber-js';
import * as validator from 'validator';
import { format as formatDate, parse as parseDate, isValid } from 'date-fns';

const server = new Server(
  {
    name: 'structured-data-validator',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const ajv = new Ajv({ allErrors: true });

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'validate_json_schema',
        description: 'Validate JSON data against a schema with detailed error reporting. Perfect for agents receiving API responses or user data that needs validation before processing.',
        inputSchema: {
          type: 'object',
          properties: {
            data: {
              type: 'object',
              description: 'The JSON data to validate'
            },
            schema: {
              type: 'object', 
              description: 'JSON Schema to validate against (supports Draft 7)'
            }
          },
          required: ['data', 'schema']
        }
      },
      {
        name: 'transform_csv_to_json',
        description: 'Convert CSV data to structured JSON with intelligent type inference. Handles messy CSV data, auto-detects delimiters, infers data types (numbers, dates, booleans).',
        inputSchema: {
          type: 'object',
          properties: {
            csv_data: {
              type: 'string',
              description: 'Raw CSV data as string'
            },
            options: {
              type: 'object',
              properties: {
                delimiter: { type: 'string', description: 'Column delimiter (auto-detected if not specified)' },
                has_headers: { type: 'boolean', default: true, description: 'Whether first row contains headers' },
                infer_types: { type: 'boolean', default: true, description: 'Whether to infer and convert data types' }
              },
              additionalProperties: false
            }
          },
          required: ['csv_data']
        }
      },
      {
        name: 'normalize_data',
        description: 'Standardize common data formats like dates, phone numbers, currencies, and addresses. Essential for agents processing user input or scraped data with inconsistent formatting.',
        inputSchema: {
          type: 'object',
          properties: {
            data: {
              type: 'array',
              items: { type: 'object' },
              description: 'Array of objects containing data to normalize'
            },
            fields: {
              type: 'object',
              properties: {
                dates: { type: 'array', items: { type: 'string' }, description: 'Field names containing dates to normalize' },
                phones: { type: 'array', items: { type: 'string' }, description: 'Field names containing phone numbers to normalize' },
                currencies: { type: 'array', items: { type: 'string' }, description: 'Field names containing currency amounts to normalize' },
                emails: { type: 'array', items: { type: 'string' }, description: 'Field names containing emails to validate and normalize' }
              },
              additionalProperties: false
            },
            target_formats: {
              type: 'object',
              properties: {
                date_format: { type: 'string', default: 'yyyy-MM-dd', description: 'Target date format (date-fns format)' },
                phone_country: { type: 'string', default: 'US', description: 'Default country for phone number parsing' },
                currency_symbol: { type: 'string', default: '$', description: 'Target currency symbol' }
              },
              additionalProperties: false
            }
          },
          required: ['data', 'fields']
        }
      },
      {
        name: 'clean_text',
        description: 'Remove HTML tags, fix encoding issues, normalize whitespace, and extract clean text from messy input. Perfect for agents processing scraped web content or user-submitted text.',
        inputSchema: {
          type: 'object',
          properties: {
            text: {
              type: 'string',
              description: 'Text to clean and normalize'
            },
            options: {
              type: 'object',
              properties: {
                remove_html: { type: 'boolean', default: true, description: 'Remove HTML tags and entities' },
                normalize_whitespace: { type: 'boolean', default: true, description: 'Normalize whitespace (collapse multiple spaces, trim)' },
                fix_encoding: { type: 'boolean', default: true, description: 'Fix common encoding issues' },
                preserve_paragraphs: { type: 'boolean', default: false, description: 'Preserve paragraph breaks when normalizing' }
              },
              additionalProperties: false
            }
          },
          required: ['text']
        }
      },
      {
        name: 'merge_datasets',
        description: 'Merge multiple JSON datasets with deduplication and conflict resolution. Handles overlapping data intelligently, perfect for agents combining data from multiple sources.',
        inputSchema: {
          type: 'object',
          properties: {
            datasets: {
              type: 'array',
              items: {
                type: 'array',
                items: { type: 'object' }
              },
              description: 'Array of datasets (each dataset is an array of objects)'
            },
            merge_key: {
              type: 'string',
              description: 'Field name to use for identifying duplicate records (e.g., "id", "email")'
            },
            conflict_resolution: {
              type: 'string',
              enum: ['first_wins', 'last_wins', 'merge_fields'],
              default: 'last_wins',
              description: 'How to resolve conflicts when same record appears in multiple datasets'
            }
          },
          required: ['datasets', 'merge_key']
        }
      }
    ]
  };
});

// Tool implementation handlers
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'validate_json_schema': {
        const { data, schema } = args as { data: any; schema: any };
        
        const validate = ajv.compile(schema);
        const isValid = validate(data);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                valid: isValid,
                errors: validate.errors || [],
                data: isValid ? data : null,
                error_summary: validate.errors?.length 
                  ? `Found ${validate.errors.length} validation errors`
                  : null
              }, null, 2)
            }
          ]
        };
      }

      case 'transform_csv_to_json': {
        const { csv_data, options = {} } = args as { 
          csv_data: string; 
          options?: { 
            delimiter?: string; 
            has_headers?: boolean; 
            infer_types?: boolean; 
          } 
        };
        
        const parseOptions: any = {
          columns: options.has_headers !== false,
          skip_empty_lines: true,
          trim: true
        };
        
        if (options.delimiter) {
          parseOptions.delimiter = options.delimiter;
        }
        
        let records = parseCsv(csv_data, parseOptions);
        
        // Type inference
        if (options.infer_types !== false && records.length > 0) {
          records = records.map((record: any) => {
            const transformed: any = {};
            for (const [key, value] of Object.entries(record)) {
              transformed[key] = inferType(value as string);
            }
            return transformed;
          });
        }
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                data: records,
                row_count: records.length,
                columns: records.length > 0 ? Object.keys(records[0]) : []
              }, null, 2)
            }
          ]
        };
      }

      case 'normalize_data': {
        const { data, fields, target_formats = {} } = args as {
          data: any[];
          fields: {
            dates?: string[];
            phones?: string[];
            currencies?: string[];
            emails?: string[];
          };
          target_formats?: {
            date_format?: string;
            phone_country?: string;
            currency_symbol?: string;
          };
        };
        
        const normalized = data.map(record => {
          const normalizedRecord = { ...record };
          
          // Normalize dates
          if (fields.dates) {
            for (const field of fields.dates) {
              if (normalizedRecord[field]) {
                normalizedRecord[field] = normalizeDate(
                  normalizedRecord[field],
                  target_formats.date_format || 'yyyy-MM-dd'
                );
              }
            }
          }
          
          // Normalize phone numbers
          if (fields.phones) {
            for (const field of fields.phones) {
              if (normalizedRecord[field]) {
                normalizedRecord[field] = normalizePhone(
                  normalizedRecord[field],
                  target_formats.phone_country || 'US'
                );
              }
            }
          }
          
          // Normalize currencies
          if (fields.currencies) {
            for (const field of fields.currencies) {
              if (normalizedRecord[field]) {
                normalizedRecord[field] = normalizeCurrency(
                  normalizedRecord[field],
                  target_formats.currency_symbol || '$'
                );
              }
            }
          }
          
          // Normalize emails
          if (fields.emails) {
            for (const field of fields.emails) {
              if (normalizedRecord[field]) {
                normalizedRecord[field] = normalizeEmail(normalizedRecord[field]);
              }
            }
          }
          
          return normalizedRecord;
        });
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                data: normalized,
                processed_count: normalized.length
              }, null, 2)
            }
          ]
        };
      }

      case 'clean_text': {
        const { text, options = {} } = args as {
          text: string;
          options?: {
            remove_html?: boolean;
            normalize_whitespace?: boolean;
            fix_encoding?: boolean;
            preserve_paragraphs?: boolean;
          };
        };
        
        let cleaned = text;
        
        if (options.remove_html !== false) {
          // Remove HTML tags and decode entities
          cleaned = cleaned.replace(/<[^>]*>/g, '');
          cleaned = cleaned.replace(/&quot;/g, '"')
                          .replace(/&apos;/g, "'")
                          .replace(/&lt;/g, '<')
                          .replace(/&gt;/g, '>')
                          .replace(/&amp;/g, '&');
        }
        
        if (options.fix_encoding !== false) {
          // Fix common encoding issues
          cleaned = cleaned.replace(/â€™/g, "'")
                          .replace(/â€œ/g, '"')
                          .replace(/â€/g, '"')
                          .replace(/â€"/g, '—');
        }
        
        if (options.normalize_whitespace !== false) {
          if (options.preserve_paragraphs) {
            // Preserve double line breaks but normalize other whitespace
            cleaned = cleaned.replace(/[ \t]+/g, ' ')
                            .replace(/\n[ \t]*/g, '\n')
                            .replace(/\n{3,}/g, '\n\n')
                            .trim();
          } else {
            // Collapse all whitespace
            cleaned = cleaned.replace(/\s+/g, ' ').trim();
          }
        }
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                original_length: text.length,
                cleaned_length: cleaned.length,
                cleaned_text: cleaned
              }, null, 2)
            }
          ]
        };
      }

      case 'merge_datasets': {
        const { datasets, merge_key, conflict_resolution = 'last_wins' } = args as {
          datasets: any[][];
          merge_key: string;
          conflict_resolution?: 'first_wins' | 'last_wins' | 'merge_fields';
        };
        
        const merged = new Map();
        let totalProcessed = 0;
        
        for (const dataset of datasets) {
          for (const record of dataset) {
            totalProcessed++;
            const key = record[merge_key];
            
            if (!key) {
              // Skip records without merge key
              continue;
            }
            
            if (merged.has(key)) {
              const existing = merged.get(key);
              
              switch (conflict_resolution) {
                case 'first_wins':
                  // Keep existing, skip new
                  break;
                case 'last_wins':
                  // Replace with new
                  merged.set(key, record);
                  break;
                case 'merge_fields':
                  // Merge fields, new values override existing
                  merged.set(key, { ...existing, ...record });
                  break;
              }
            } else {
              merged.set(key, record);
            }
          }
        }
        
        const result = Array.from(merged.values());
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                data: result,
                total_processed: totalProcessed,
                final_count: result.length,
                duplicates_resolved: totalProcessed - result.length,
                merge_strategy: conflict_resolution
              }, null, 2)
            }
          ]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            tool: name
          }, null, 2)
        }
      ],
      isError: true
    };
  }
});

// Helper functions
function inferType(value: string): any {
  if (!value || typeof value !== 'string') return value;
  
  const trimmed = value.trim();
  if (!trimmed) return trimmed;
  
  // Boolean
  if (trimmed.toLowerCase() === 'true') return true;
  if (trimmed.toLowerCase() === 'false') return false;
  
  // Number
  if (!isNaN(Number(trimmed)) && !isNaN(parseFloat(trimmed))) {
    return trimmed.includes('.') ? parseFloat(trimmed) : parseInt(trimmed, 10);
  }
  
  // Date (ISO format)
  if (/^\d{4}-\d{2}-\d{2}/.test(trimmed)) {
    const date = new Date(trimmed);
    if (!isNaN(date.getTime())) {
      return date.toISOString();
    }
  }
  
  return trimmed;
}

function normalizeDate(dateStr: string, targetFormat: string): string {
  try {
    // Common date formats to try
    const formats = [
      'yyyy-MM-dd',
      'MM/dd/yyyy', 
      'dd/MM/yyyy',
      'yyyy/MM/dd',
      'MM-dd-yyyy',
      'dd-MM-yyyy',
      'MMM dd, yyyy',
      'MMMM dd, yyyy'
    ];
    
    for (const format of formats) {
      try {
        const parsed = parseDate(dateStr, format, new Date());
        if (isValid(parsed)) {
          return formatDate(parsed, targetFormat);
        }
      } catch {
        continue;
      }
    }
    
    // Try as ISO date
    const isoDate = new Date(dateStr);
    if (isValid(isoDate)) {
      return formatDate(isoDate, targetFormat);
    }
    
    return dateStr; // Return original if can't parse
  } catch {
    return dateStr;
  }
}

function normalizePhone(phoneStr: string, country: string): string {
  try {
    const parsed = parsePhoneNumber(phoneStr, country as any);
    if (parsed && parsed.isValid()) {
      return parsed.formatInternational();
    }
    return phoneStr;
  } catch {
    return phoneStr;
  }
}

function normalizeCurrency(currencyStr: string, symbol: string): string {
  // Extract numeric value
  const match = currencyStr.match(/[\d,]+\.?\d*/);
  if (match) {
    const numericStr = match[0].replace(/,/g, '');
    const value = parseFloat(numericStr);
    if (!isNaN(value)) {
      return `${symbol}${value.toFixed(2)}`;
    }
  }
  return currencyStr;
}

function normalizeEmail(emailStr: string): string {
  const trimmed = emailStr.trim().toLowerCase();
  if (validator.isEmail(trimmed)) {
    return trimmed;
  }
  return emailStr; // Return original if invalid
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Structured Data Validator MCP server running on stdio');
}

if (require.main === module) {
  main().catch(console.error);
}
import { Tool } from '@modelcontextprotocol/sdk/types.js'

export const TOOL_DEFINITIONS: Tool[] = [
  // --- Read-only tools ---
  {
    name: 'get_screenshot',
    description:
      'Capture a screenshot of the active browser window in Selenix playback. Returns a base64-encoded JPEG image.',
    inputSchema: {
      type: 'object' as const,
      properties: {},
    },
  },
  {
    name: 'get_page_html',
    description:
      'Get the HTML of the web page in the active playback window, with interactive elements annotated. Scripts and styles are removed.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        tab_id: {
          type: 'string',
          description:
            'Optional tab/window ID. Use "all" for all tabs. Omit for active tab.',
        },
      },
    },
  },
  {
    name: 'get_search_html',
    description:
      'Search page HTML by regex pattern and return surrounding HTML context for matches.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        regex: {
          type: 'string',
          description: 'Regular expression pattern to search for',
        },
        index: {
          type: 'number',
          description: 'Optional 0-based index of which match to return',
        },
        tab_id: { type: 'string', description: 'Optional tab/window ID' },
      },
      required: ['regex'],
    },
  },
  {
    name: 'get_selected_command_info',
    description:
      'Get comprehensive context about a command target element: DOM hierarchy, accessibility info, surrounding HTML, interactive properties.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        command_id: {
          type: 'string',
          description:
            'Optional command ID. If omitted, uses the currently selected command.',
        },
      },
    },
  },
  {
    name: 'get_current_test',
    description:
      'Get the commands of the current test (or a specific test by ID). Returns test name, ID, and all commands with their targets and values.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        test_id: {
          type: 'string',
          description: 'Optional test ID. If omitted, returns the active test.',
        },
      },
    },
  },
  {
    name: 'get_test_list',
    description:
      'List all tests in the current Selenix project with their IDs, names, and command counts.',
    inputSchema: { type: 'object' as const, properties: {} },
  },
  {
    name: 'get_test_by_name',
    description:
      'Get a specific test by its name, including all commands.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        test_name: {
          type: 'string',
          description: 'The name of the test to retrieve',
        },
      },
      required: ['test_name'],
    },
  },
  {
    name: 'get_command_list',
    description:
      'List all available Selenix commands (click, type, open, etc.) with descriptions.',
    inputSchema: { type: 'object' as const, properties: {} },
  },
  {
    name: 'get_command_info',
    description:
      'Get detailed documentation for a specific Selenix command, including target and value parameter descriptions.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        command_name: {
          type: 'string',
          description:
            'The camelCase command name (e.g., "click", "executeScript")',
        },
      },
      required: ['command_name'],
    },
  },
  {
    name: 'get_project_info',
    description:
      'Get metadata about the current Selenix project: name, base URL, test count, suite count.',
    inputSchema: { type: 'object' as const, properties: {} },
  },
  {
    name: 'get_active_suite',
    description:
      'Get information about the currently active test suite and its tests.',
    inputSchema: { type: 'object' as const, properties: {} },
  },
  {
    name: 'get_step_results',
    description:
      'Get pass/fail/error results for each command in the last test run.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        test_id: {
          type: 'string',
          description: 'Optional test ID. If omitted, uses the active test.',
        },
      },
    },
  },
  {
    name: 'get_logs',
    description:
      'Get recent logs from Selenix (all types). Returns 20 logs per page, most recent first. Use page parameter to paginate (0 = most recent, 1 = next 20, etc.).',
    inputSchema: {
      type: 'object' as const,
      properties: {
        page: {
          type: 'number',
          description: 'Page number (0 = most recent 20 logs, 1 = next 20, etc.). Defaults to 0.',
        },
      },
    },
  },
  {
    name: 'get_workspace_context',
    description:
      'Get a summary of the current Selenix workspace: project name, active test, test count, selected command count.',
    inputSchema: { type: 'object' as const, properties: {} },
  },

  // --- Write tools ---
  {
    name: 'add_commands',
    description:
      'Add one or more commands to a test at a specific index. Commands use camelCase names (e.g., "click", "type", "open", "executeScript").',
    inputSchema: {
      type: 'object' as const,
      properties: {
        test_id: {
          type: 'string',
          description: 'The test ID to add commands to',
        },
        index: {
          type: 'number',
          description: 'The 0-based index at which to insert commands',
        },
        commands: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              command: { type: 'string' },
              target: { type: 'string' },
              value: { type: 'string' },
            },
            required: ['command'],
          },
          description: 'Array of commands to add',
        },
      },
      required: ['test_id', 'index', 'commands'],
    },
  },
  {
    name: 'run_test',
    description:
      'Run a test and wait for it to complete. Returns the pass/fail result for each command. This operation may take up to 2 minutes.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        test_id: {
          type: 'string',
          description: 'Optional test ID. If omitted, runs the active test.',
        },
      },
    },
  },
  {
    name: 'clear_and_replace_commands',
    description:
      'Replace ALL commands in a test with a new set. This removes all existing commands first.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        test_id: {
          type: 'string',
          description: 'The test ID',
        },
        commands: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              command: { type: 'string' },
              target: { type: 'string' },
              value: { type: 'string' },
            },
            required: ['command'],
          },
          description: 'The new set of commands for the test',
        },
      },
      required: ['test_id', 'commands'],
    },
  },
  {
    name: 'fix_commands',
    description:
      'Apply targeted fixes to commands in a test: update, remove, or insert at specific indexes. Indexes refer to the current command list BEFORE any fixes are applied.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        test_id: {
          type: 'string',
          description: 'The test ID',
        },
        fixes: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              action: {
                type: 'string',
                enum: ['update', 'remove', 'insert'],
              },
              index: {
                type: 'number',
                description: '0-based command index',
              },
              command: { type: 'string' },
              target: { type: 'string' },
              value: { type: 'string' },
            },
            required: ['action', 'index'],
          },
        },
      },
      required: ['test_id', 'fixes'],
    },
  },
]

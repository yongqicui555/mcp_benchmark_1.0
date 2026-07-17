/**
 * Basic functionality tests for Structured Data Validator MCP Server
 * These tests verify the core tools work as expected
 */

const { spawn } = require('child_process');
const path = require('path');

// Helper function to test MCP server via stdio
async function testMCPTool(toolName, args) {
  return new Promise((resolve, reject) => {
    const serverPath = path.join(__dirname, '../dist/index.js');
    const server = spawn('node', [serverPath]);
    
    let stdout = '';
    let stderr = '';
    
    server.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    server.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    // Send MCP requests
    const listToolsRequest = {
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/list',
      params: {}
    };
    
    const callToolRequest = {
      jsonrpc: '2.0', 
      id: 2,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      }
    };
    
    server.stdin.write(JSON.stringify(listToolsRequest) + '\n');
    server.stdin.write(JSON.stringify(callToolRequest) + '\n');
    server.stdin.end();
    
    server.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Server exited with code ${code}. stderr: ${stderr}`));
      } else {
        // Parse the stdout to extract responses
        const lines = stdout.split('\n').filter(line => line.trim());
        const responses = lines.map(line => {
          try {
            return JSON.parse(line);
          } catch {
            return null;
          }
        }).filter(Boolean);
        
        resolve(responses);
      }
    });
    
    // Timeout after 10 seconds
    setTimeout(() => {
      server.kill();
      reject(new Error('Test timeout'));
    }, 10000);
  });
}

// Test JSON Schema Validation
async function testJsonSchemaValidation() {
  console.log('Testing JSON Schema Validation...');
  
  const args = {
    data: { name: 'John', age: 25 },
    schema: {
      type: 'object',
      properties: {
        name: { type: 'string' },
        age: { type: 'number' }
      },
      required: ['name', 'age']
    }
  };
  
  try {
    const responses = await testMCPTool('validate_json_schema', args);
    const toolResponse = responses.find(r => r.id === 2);
    
    if (toolResponse && toolResponse.result) {
      const result = JSON.parse(toolResponse.result.content[0].text);
      console.log('✅ JSON Schema Validation:', result.valid ? 'PASS' : 'FAIL');
      return result.valid;
    }
  } catch (error) {
    console.log('❌ JSON Schema Validation: ERROR -', error.message);
    return false;
  }
  
  return false;
}

// Test CSV to JSON conversion
async function testCsvToJson() {
  console.log('Testing CSV to JSON conversion...');
  
  const args = {
    csv_data: 'name,age,active\nJohn,25,true\nJane,30,false',
    options: {
      infer_types: true,
      has_headers: true
    }
  };
  
  try {
    const responses = await testMCPTool('transform_csv_to_json', args);
    const toolResponse = responses.find(r => r.id === 2);
    
    if (toolResponse && toolResponse.result) {
      const result = JSON.parse(toolResponse.result.content[0].text);
      console.log('✅ CSV to JSON:', result.success ? 'PASS' : 'FAIL');
      console.log('   Processed rows:', result.row_count);
      return result.success && result.row_count === 2;
    }
  } catch (error) {
    console.log('❌ CSV to JSON: ERROR -', error.message);
    return false;
  }
  
  return false;
}

// Test text cleaning
async function testTextCleaning() {
  console.log('Testing text cleaning...');
  
  const args = {
    text: '<p>Hello &quot;world&quot;</p>\n\n\nExtra   spaces',
    options: {
      remove_html: true,
      normalize_whitespace: true
    }
  };
  
  try {
    const responses = await testMCPTool('clean_text', args);
    const toolResponse = responses.find(r => r.id === 2);
    
    if (toolResponse && toolResponse.result) {
      const result = JSON.parse(toolResponse.result.content[0].text);
      console.log('✅ Text Cleaning:', result.success ? 'PASS' : 'FAIL');
      console.log('   Cleaned text:', `"${result.cleaned_text}"`);
      return result.success;
    }
  } catch (error) {
    console.log('❌ Text Cleaning: ERROR -', error.message);
    return false;
  }
  
  return false;
}

// Run all tests
async function runTests() {
  console.log('🧪 Running Structured Data Validator MCP Server Tests\n');
  
  const results = {
    jsonSchema: await testJsonSchemaValidation(),
    csvToJson: await testCsvToJson(),
    textCleaning: await testTextCleaning()
  };
  
  const totalTests = Object.keys(results).length;
  const passedTests = Object.values(results).filter(Boolean).length;
  
  console.log(`\n📊 Test Results: ${passedTests}/${totalTests} passed`);
  
  if (passedTests === totalTests) {
    console.log('🎉 All tests passed! Server is ready for deployment.');
    process.exit(0);
  } else {
    console.log('❌ Some tests failed. Check server implementation.');
    process.exit(1);
  }
}

// Only run tests if this file is executed directly
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { testMCPTool, runTests };
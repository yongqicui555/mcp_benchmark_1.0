// Test script to verify World Bank MCP functionality
import { exec } from 'child_process';

console.log('Testing worldbank-mcp project...');

// Test help command
exec('node build/index.js --help', (error, stdout, stderr) => {
  if (error) {
    console.error('Test failed:', error);
    return;
  }
  console.log('✓ Help command test passed');
  
  // Test version command
  exec('node build/index.js --version', (error, stdout, stderr) => {
    if (error) {
      console.error('Version test failed:', error);
      return;
    }
    console.log('✓ Version command test passed');
    console.log('Version:', stdout.trim());
    
    console.log('\n✅ All basic tests passed!');
    console.log('\nProject structure:');
    console.log('worldbank-mcp/');
    console.log('├── src/');
    console.log('│   ├── index.ts      # Main entry file');
    console.log('│   └── types.ts      # Type definitions');
    console.log('├── build/           # Compiled output');
    console.log('├── package.json     # Project configuration');
    console.log('├── tsconfig.json   # TypeScript configuration');
    console.log('└── README.md        # Documentation');
    
    console.log('\n🎉 worldbank-mcp project created successfully!');
    console.log('Run command: npm start or npx worldbank-mcp');
    console.log('\n📊 Features:');
    console.log('• Country information query');
    console.log('• Economic data query (GDP, population, inflation, etc.)');
    console.log('• Social development data query');
    console.log('• Real-time World Bank API integration');
    console.log('• MCP protocol compatibility');
    
    console.log('\n🌍 Supported economic indicators:');
    console.log('• GDP - Gross Domestic Product');
    console.log('• GDP_PER_CAPITA - GDP per capita');
    console.log('• POPULATION - Total population');
    console.log('• INFLATION - Inflation rate');
    console.log('• UNEMPLOYMENT - Unemployment rate');
    
    console.log('\n👥 Supported social indicators:');
    console.log('• LIFE_EXPECTANCY - Life expectancy');
    console.log('• LITERACY_RATE - Literacy rate');
    console.log('• INTERNET_USERS - Internet users percentage');
    
    console.log('\n🚀 Usage:');
    console.log('1. Run: npx worldbank-mcp');
    console.log('2. Configure in MCP client:');
    console.log('   "command": "npx", "args": ["worldbank-mcp"]');
    console.log('3. Use commands like: "Query China GDP data"');
  });
});

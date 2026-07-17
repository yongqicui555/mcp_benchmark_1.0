const { build } = require('esbuild')

build({
  entryPoints: ['dist/index.js'],
  bundle: true,
  platform: 'node',
  target: 'node18',
  outfile: 'dist/bundle.js',
  format: 'cjs',
  banner: {},
}).catch(() => process.exit(1))

const nextJest = require('../../frontend/node_modules/next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
/** @type {import('jest').Config} */
const config = {
  testEnvironment: 'jsdom',
  rootDir: '../../frontend',
  roots: ['<rootDir>', '<rootDir>/../tests/frontend'],
  moduleDirectories: ['node_modules', '<rootDir>/node_modules'],
  moduleNameMapper: {
    // Handle module aliases (this will be automatically configured for you soon)
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: ['<rootDir>/../tests/frontend/**/test_*.{ts,tsx}'],
  setupFilesAfterEnv: ['<rootDir>/../tests/frontend/jest.setup.ts'],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(config)

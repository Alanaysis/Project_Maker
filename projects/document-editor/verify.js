/**
 * Document Editor - Verification Script
 *
 * This script verifies the project structure and code quality.
 * Run with: node verify.js
 */

const fs = require('fs');
const path = require('path');

console.log('=== Document Editor - Verification ===\n');

const rootDir = __dirname;
let passed = 0;
let failed = 0;

function check(condition, message) {
  if (condition) {
    passed++;
    console.log(`✓ ${message}`);
  } else {
    failed++;
    console.log(`✗ ${message}`);
  }
}

// Check project structure
console.log('\n1. Checking project structure...');
check(fs.existsSync(path.join(rootDir, 'package.json')), 'package.json exists');
check(fs.existsSync(path.join(rootDir, 'tsconfig.json')), 'tsconfig.json exists');
check(fs.existsSync(path.join(rootDir, 'README.md')), 'README.md exists');
check(fs.existsSync(path.join(rootDir, 'LEARNING_NOTES.md')), 'LEARNING_NOTES.md exists');

// Check source files
console.log('\n2. Checking source files...');
check(fs.existsSync(path.join(rootDir, 'src/index.ts')), 'src/index.ts exists');
check(fs.existsSync(path.join(rootDir, 'src/crdt/CRDTDocument.ts')), 'CRDTDocument.ts exists');
check(fs.existsSync(path.join(rootDir, 'src/formatting/FormatTypes.ts')), 'FormatTypes.ts exists');
check(fs.existsSync(path.join(rootDir, 'src/history/VersionHistory.ts')), 'VersionHistory.ts exists');
check(fs.existsSync(path.join(rootDir, 'src/collaboration/CollaborationManager.ts')), 'CollaborationManager.ts exists');
check(fs.existsSync(path.join(rootDir, 'src/editor/DocumentEditor.ts')), 'DocumentEditor.ts exists');

// Check test files
console.log('\n3. Checking test files...');
check(fs.existsSync(path.join(rootDir, 'tests/run-tests.ts')), 'run-tests.ts exists');
check(fs.existsSync(path.join(rootDir, 'tests/CRDTDocument.test.ts')), 'CRDTDocument.test.ts exists');
check(fs.existsSync(path.join(rootDir, 'tests/FormatManager.test.ts')), 'FormatManager.test.ts exists');
check(fs.existsSync(path.join(rootDir, 'tests/VersionHistory.test.ts')), 'VersionHistory.test.ts exists');
check(fs.existsSync(path.join(rootDir, 'tests/DocumentEditor.test.ts')), 'DocumentEditor.test.ts exists');

// Check examples
console.log('\n4. Checking example files...');
check(fs.existsSync(path.join(rootDir, 'examples/basic-editing.ts')), 'basic-editing.ts exists');
check(fs.existsSync(path.join(rootDir, 'examples/collaborative-editing.ts')), 'collaborative-editing.ts exists');
check(fs.existsSync(path.join(rootDir, 'examples/version-history.ts')), 'version-history.ts exists');

// Check documentation
console.log('\n5. Checking documentation...');
check(fs.existsSync(path.join(rootDir, 'docs/01-RESEARCH.md')), '01-RESEARCH.md exists');
check(fs.existsSync(path.join(rootDir, 'docs/02-REQUIREMENTS.md')), '02-REQUIREMENTS.md exists');
check(fs.existsSync(path.join(rootDir, 'docs/03-DESIGN.md')), '03-DESIGN.md exists');
check(fs.existsSync(path.join(rootDir, 'docs/04-PRODUCT.md')), '04-PRODUCT.md exists');
check(fs.existsSync(path.join(rootDir, 'docs/05-DEVELOPMENT.md')), '05-DEVELOPMENT.md exists');

// Check code quality
console.log('\n6. Checking code quality...');
const crdtCode = fs.readFileSync(path.join(rootDir, 'src/crdt/CRDTDocument.ts'), 'utf8');
check(crdtCode.includes('class CRDTDocument'), 'CRDTDocument class defined');
check(crdtCode.includes('insert('), 'insert method exists');
check(crdtCode.includes('delete('), 'delete method exists');
check(crdtCode.includes('applyRemoteOp('), 'applyRemoteOp method exists');

const formatCode = fs.readFileSync(path.join(rootDir, 'src/formatting/FormatTypes.ts'), 'utf8');
check(formatCode.includes('class FormatManager'), 'FormatManager class defined');
check(formatCode.includes('applyMark('), 'applyMark method exists');

const historyCode = fs.readFileSync(path.join(rootDir, 'src/history/VersionHistory.ts'), 'utf8');
check(historyCode.includes('class VersionHistory'), 'VersionHistory class defined');
check(historyCode.includes('commit('), 'commit method exists');

const editorCode = fs.readFileSync(path.join(rootDir, 'src/editor/DocumentEditor.ts'), 'utf8');
check(editorCode.includes('class DocumentEditor'), 'DocumentEditor class defined');
check(editorCode.includes('insertText('), 'insertText method exists');

// Summary
console.log('\n=== Verification Summary ===');
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log(`Total: ${passed + failed}`);

if (failed === 0) {
  console.log('\n✓ All checks passed! Project is properly structured.');
  console.log('\nTo run the project:');
  console.log('1. npm install');
  console.log('2. npm test');
  console.log('3. npm run example:basic');
} else {
  console.log('\n✗ Some checks failed. Please review the issues above.');
  process.exit(1);
}

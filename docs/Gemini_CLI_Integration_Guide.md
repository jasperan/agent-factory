# Gemini CLI Integration - Implementation Guide

## 🔌 Connecting BridgeCode to Gemini CLI

### Overview

This guide shows you exactly how to integrate Gemini CLI with BridgeCode so they work together seamlessly.

---

## 🛠️ Prerequisites

### 1. Ollama Running
```bash
# Start Ollama server
ollama serve

# In another terminal, verify
curl http://localhost:11434/api/tags
# Should see: "models": [{"name": "codegemma:7b", ...}]
```

### 2. Gemini CLI Installed
```bash
# Install Gemini CLI
npm install -g @google/genai-cli

# Or from GitHub
git clone https://github.com/google/genai.git
cd genai
npm install -g .

# Verify installation
gemini --version
```

### 3. Gemini Authentication
```bash
# Get your API key from: https://ai.google.dev/
# Then authenticate
gemini auth --api-key sk-... 
# Or set environment variable
export GOOGLE_GENAI_API_KEY=sk-...

# Verify authentication
gemini list-models
```

---

## 📝 Implementation Steps

### Step 1: Create Gemini CLI Bridge Interface

Create `src/types/gemini-cli.ts`:

```typescript
/**
 * Type definitions for Gemini CLI operations
 */

export interface ProjectConfig {
  name: string;
  description: string;
  language: 'typescript' | 'python' | 'go' | 'rust' | 'java' | 'kotlin';
  framework?: string;
  template?: string;
  outputDir: string;
}

export interface GeminiCLIResponse {
  success: boolean;
  output: string;
  projectPath?: string;
  errors?: string[];
}

export interface GeminiScaffoldOptions {
  type: 'api' | 'web' | 'cli' | 'library' | 'service';
  language: string;
  pattern?: 'mvc' | 'layered' | 'hexagonal' | 'modular';
  includeTests?: boolean;
  includeDocs?: boolean;
}

export interface ScaffoldedProject {
  files: string[];
  structure: {
    [key: string]: string | { [key: string]: string };
  };
  readme: string;
  packageJson: Record<string, any>;
}
```

---

### Step 2: Create Enhanced Gemini CLI Bridge

Replace earlier version in `src/gemini-cli-bridge.ts`:

```typescript
import { execSync, exec } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';
import { ProjectConfig, GeminiCLIResponse, ScaffoldedProject } from './types/gemini-cli';

const execAsync = promisify(exec);

/**
 * Enhanced Gemini CLI Bridge with full integration
 * Automatically connects to Gemini CLI and executes scaffolding commands
 */
export class GeminiCLIBridge {
  private geminiCmd: string;
  private apiKey?: string;
  private maxRetries = 3;
  private retryDelay = 2000;
  private outputBuffer: string[] = [];

  constructor(geminiPath: string = 'gemini', apiKey?: string) {
    this.geminiCmd = geminiPath;
    this.apiKey = apiKey || process.env.GOOGLE_GENAI_API_KEY;
    this.verifyGeminiCLI();
  }

  /**
   * Verify Gemini CLI is installed and authenticated
   */
  private verifyGeminiCLI(): void {
    try {
      const versionResult = execSync(`${this.geminiCmd} --version`, { encoding: 'utf-8' });
      console.log(`✅ Gemini CLI: ${versionResult.trim()}`);

      if (!this.apiKey) {
        const listResult = execSync(`${this.geminiCmd} list-models`, { encoding: 'utf-8' });
        if (!listResult || listResult.includes('error')) {
          throw new Error('Gemini CLI authentication failed');
        }
        console.log(`✅ Gemini CLI authenticated`);
      }
    } catch (error) {
      throw new Error(
        `❌ Gemini CLI setup failed. Check: 1) Installation 2) Authentication 3) API key`
      );
    }
  }

  /**
   * Generate complete new project structure
   */
  async generateProject(config: ProjectConfig): Promise<GeminiCLIResponse> {
    console.log(`\n🔷 Gemini CLI: Generating ${config.name}...`);
    this.outputBuffer = [];

    try {
      const cmd = this.buildProjectCommand(config);
      this.logCommand(cmd);

      const output = await this.executeCommand(cmd);
      
      // Validate generated project
      if (!fs.existsSync(config.outputDir)) {
        throw new Error(`Project directory not created: ${config.outputDir}`);
      }

      console.log(`✅ Project generated at: ${config.outputDir}`);

      return {
        success: true,
        output,
        projectPath: config.outputDir
      };
    } catch (error: any) {
      console.error(`❌ Project generation failed:`, error.message);
      return {
        success: false,
        output: error.message,
        errors: [error.message]
      };
    }
  }

  /**
   * Scaffold specific project type with pattern
   */
  async scaffoldProject(config: ProjectConfig): Promise<ScaffoldedProject> {
    console.log(`\n🔷 Gemini CLI: Scaffolding ${config.framework || 'project'}...`);

    try {
      const cmd = `${this.geminiCmd} scaffold ${config.language} --framework ${config.framework || 'standard'} --output ${config.outputDir}`;
      
      this.logCommand(cmd);
      await this.executeCommand(cmd);

      // Read generated structure
      return this.readScaffoldedProject(config.outputDir);
    } catch (error: any) {
      throw new Error(`Scaffolding failed: ${error.message}`);
    }
  }

  /**
   * Create API boilerplate
   */
  async createAPIBoilerplate(
    language: string,
    framework: string,
    outputDir: string
  ): Promise<string[]> {
    console.log(`\n🔷 Gemini CLI: Creating ${language} ${framework} API...`);

    try {
      const cmd = `${this.geminiCmd} create-api --language ${language} --framework ${framework} --output ${outputDir}`;
      
      this.logCommand(cmd);
      await this.executeCommand(cmd);

      return this.listGeneratedFiles(outputDir);
    } catch (error: any) {
      throw new Error(`API boilerplate creation failed: ${error.message}`);
    }
  }

  /**
   * Create web application boilerplate
   */
  async createWebBoilerplate(
    framework: string,
    outputDir: string
  ): Promise<string[]> {
    console.log(`\n🔷 Gemini CLI: Creating ${framework} web app...`);

    try {
      const cmd = `${this.geminiCmd} create-web --framework ${framework} --output ${outputDir}`;
      
      this.logCommand(cmd);
      await this.executeCommand(cmd);

      return this.listGeneratedFiles(outputDir);
    } catch (error: any) {
      throw new Error(`Web boilerplate creation failed: ${error.message}`);
    }
  }

  /**
   * Generate test scaffolding
   */
  async generateTests(
    language: string,
    framework: string,
    sourceDir: string
  ): Promise<string[]> {
    console.log(`\n🔷 Gemini CLI: Generating ${language} tests with ${framework}...`);

    try {
      const cmd = `${this.geminiCmd} generate-tests --language ${language} --framework ${framework} --source ${sourceDir}`;
      
      this.logCommand(cmd);
      await this.executeCommand(cmd);

      return this.listGeneratedFiles(path.join(sourceDir, '../tests'));
    } catch (error: any) {
      throw new Error(`Test generation failed: ${error.message}`);
    }
  }

  /**
   * Generate documentation
   */
  async generateDocumentation(
    language: string,
    sourceDir: string,
    outputDir: string
  ): Promise<string> {
    console.log(`\n🔷 Gemini CLI: Generating documentation...`);

    try {
      const cmd = `${this.geminiCmd} generate-docs --language ${language} --source ${sourceDir} --output ${outputDir}`;
      
      this.logCommand(cmd);
      return await this.executeCommand(cmd);
    } catch (error: any) {
      throw new Error(`Documentation generation failed: ${error.message}`);
    }
  }

  /**
   * Build project command
   */
  private buildProjectCommand(config: ProjectConfig): string {
    const parts = [
      this.geminiCmd,
      'generate-project',
      `"${config.description || config.name}"`,
      `--name ${config.name}`,
      `--language ${config.language}`,
      `--output ${config.outputDir}`
    ];

    if (config.framework) parts.push(`--framework ${config.framework}`);
    if (config.template) parts.push(`--template ${config.template}`);

    return parts.join(' ');
  }

  /**
   * Execute Gemini CLI command with retry logic
   */
  private async executeCommand(cmd: string, attempt = 1): Promise<string> {
    try {
      console.log(`[Attempt ${attempt}/${this.maxRetries}] Executing...`);
      
      const { stdout, stderr } = await execAsync(cmd, {
        timeout: 120000, // 2 minute timeout for generation
        maxBuffer: 20 * 1024 * 1024, // 20MB buffer
        env: {
          ...process.env,
          GOOGLE_GENAI_API_KEY: this.apiKey
        }
      });

      if (stderr && !stderr.includes('warning')) {
        console.warn(`⚠️ ${stderr}`);
      }

      this.outputBuffer.push(stdout);
      return stdout;
    } catch (error: any) {
      if (attempt < this.maxRetries) {
        console.warn(`⚠️ Attempt ${attempt} failed, retrying...`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.executeCommand(cmd, attempt + 1);
      }
      throw error;
    }
  }

  /**
   * Read and parse scaffolded project structure
   */
  private readScaffoldedProject(projectPath: string): ScaffoldedProject {
    const files: string[] = [];
    const structure: any = {};

    const walkDir = (dir: string, prefix = '') => {
      const entries = fs.readdirSync(dir);
      for (const entry of entries) {
        const fullPath = path.join(dir, entry);
        const relativePath = path.join(prefix, entry);
        
        if (fs.statSync(fullPath).isDirectory()) {
          structure[relativePath] = {};
          walkDir(fullPath, relativePath);
        } else {
          files.push(relativePath);
          structure[relativePath] = fs.readFileSync(fullPath, 'utf-8').substring(0, 100);
        }
      }
    };

    walkDir(projectPath);

    const readme = this.readFileIfExists(path.join(projectPath, 'README.md'), '');
    const packageJson = this.readJsonIfExists(path.join(projectPath, 'package.json'), {});

    return {
      files,
      structure,
      readme,
      packageJson
    };
  }

  /**
   * List all generated files
   */
  private listGeneratedFiles(dir: string): string[] {
    if (!fs.existsSync(dir)) return [];

    const files: string[] = [];
    const walkDir = (currentPath: string) => {
      for (const file of fs.readdirSync(currentPath)) {
        const fullPath = path.join(currentPath, file);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
          walkDir(fullPath);
        } else {
          files.push(path.relative(dir, fullPath));
        }
      }
    };

    walkDir(dir);
    return files;
  }

  /**
   * Utility: Read file or return default
   */
  private readFileIfExists(filePath: string, defaultValue: string): string {
    try {
      return fs.readFileSync(filePath, 'utf-8');
    } catch {
      return defaultValue;
    }
  }

  /**
   * Utility: Read JSON or return default
   */
  private readJsonIfExists(filePath: string, defaultValue: any): any {
    try {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    } catch {
      return defaultValue;
    }
  }

  /**
   * Validate project structure
   */
  async validateProject(projectPath: string): Promise<{
    valid: boolean;
    missingFiles: string[];
    issues: string[];
  }> {
    const required = ['package.json', 'README.md', 'src'];
    const missing: string[] = [];
    const issues: string[] = [];

    for (const file of required) {
      const fullPath = path.join(projectPath, file);
      if (!fs.existsSync(fullPath)) {
        missing.push(file);
      }
    }

    if (missing.length > 0) {
      issues.push(`Missing required files: ${missing.join(', ')}`);
    }

    return {
      valid: missing.length === 0,
      missingFiles: missing,
      issues
    };
  }

  /**
   * Log command for debugging
   */
  private logCommand(cmd: string): void {
    console.log(`   $ ${cmd}`);
  }

  /**
   * Get execution output
   */
  getOutput(): string {
    return this.outputBuffer.join('\n');
  }

  /**
   * Clear output buffer
   */
  clearOutput(): void {
    this.outputBuffer = [];
  }
}
```

---

### Step 3: Create Orchestrator Integration

Create `src/orchestrator-gemini-integration.ts`:

```typescript
import { GeminiCLIBridge } from './gemini-cli-bridge';
import { Orchestrator } from './orchestrator';
import { CodeModel } from './code-model';
import { FileManager } from './file-manager';
import { ProjectConfig } from './types/gemini-cli';

/**
 * Full orchestration with Gemini CLI integration
 */
export class FullOrchestratorWithGemini {
  private geminiBridge: GeminiCLIBridge;
  private orchestrator: Orchestrator;
  private model: CodeModel;
  private fileManager: FileManager;

  constructor(
    model: CodeModel,
    fileManager: FileManager,
    numAgents = 4
  ) {
    this.model = model;
    this.fileManager = fileManager;
    this.geminiBridge = new GeminiCLIBridge();
    this.orchestrator = new Orchestrator(model, fileManager, numAgents);
  }

  /**
   * Complete workflow: Generate + Improve
   */
  async completeWorkflow(projectConfig: ProjectConfig): Promise<void> {
    console.log(`\n╔════════════════════════════════════════╗`);
    console.log(`║  🌉 BridgeCode + Gemini CLI Complete   ║`);
    console.log(`╚════════════════════════════════════════╝\n`);

    // Phase 1: Generate
    console.log(`📍 PHASE 1: Initial Project Generation\n`);
    const genResult = await this.geminiBridge.generateProject(projectConfig);

    if (!genResult.success) {
      throw new Error(`Project generation failed: ${genResult.errors?.join(', ')}`);
    }

    // Phase 2: Validate
    console.log(`\n📍 PHASE 2: Validation\n`);
    const validation = await this.geminiBridge.validateProject(projectConfig.outputDir);
    
    if (!validation.valid) {
      console.warn(`⚠️ Validation issues:`, validation.issues);
    }

    // Phase 3: Analyze
    console.log(`\n📍 PHASE 3: Code Analysis\n`);
    const files = this.fileManager.listFiles(projectConfig.outputDir);
    console.log(`Found ${files.length} files to analyze`);

    // Phase 4: Improve
    console.log(`\n📍 PHASE 4: Multi-Agent Improvement\n`);
    const tasks = this.generateImprovementTasks(files, projectConfig);
    this.orchestrator.addTasks(tasks);
    await this.orchestrator.run();

    console.log(`\n✅ COMPLETE! Project ready in: ${projectConfig.outputDir}`);
  }

  /**
   * Two-phase workflow: Analyze existing + improve
   */
  async analyzeAndImprove(projectPath: string): Promise<void> {
    console.log(`\n╔════════════════════════════════════════╗`);
    console.log(`║   🌉 BridgeCode Improvement Workflow   ║`);
    console.log(`╚════════════════════════════════════════╝\n`);

    console.log(`📍 PHASE 1: Code Analysis\n`);
    const files = this.fileManager.listFiles(projectPath);
    
    console.log(`📍 PHASE 2: Improvement Execution\n`);
    const tasks = files.map((file, i) => ({
      id: `improve-${i}`,
      title: `Improve ${file}`,
      description: 'Add error handling, validation, documentation',
      type: 'refactor',
      priority: 'high',
      affected_files: [file],
      effort_hours: 1
    }));

    this.orchestrator.addTasks(tasks);
    await this.orchestrator.run();

    console.log(`\n✅ Improvement complete!`);
  }

  /**
   * Generate improvement tasks
   */
  private generateImprovementTasks(files: string[], config: ProjectConfig) {
    return files.map((file, i) => ({
      id: `improve-${i}`,
      title: `Improve ${file}`,
      description: `Add error handling, validation, tests, and documentation for ${file}`,
      type: 'refactor',
      priority: i < 5 ? 'high' : 'medium',
      affected_files: [file],
      effort_hours: 1
    }));
  }
}
```

---

### Step 4: Create Complete Example

Create `src/main-gemini-complete.ts`:

```typescript
import 'dotenv/config';
import { FullOrchestratorWithGemini } from './orchestrator-gemini-integration';
import { CodeModel } from './code-model';
import { FileManager } from './file-manager';

async function main() {
  console.log('╔════════════════════════════════════════╗');
  console.log('║   🌉 BridgeCode + Gemini Complete     ║');
  console.log('║      Full Workflow Example             ║');
  console.log('╚════════════════════════════════════════╝\n');

  // Initialize
  const model = new CodeModel();
  const fileManager = new FileManager('.');
  const orchestrator = new FullOrchestratorWithGemini(model, fileManager, 4);

  // Complete workflow: Generate new project + improve
  await orchestrator.completeWorkflow({
    name: 'my-awesome-api',
    description: 'Production-grade Node.js REST API',
    language: 'typescript',
    framework: 'express',
    outputDir: './generated-api',
  });

  console.log('\n✅ Generated and improved project ready!');
  console.log('📁 Location: ./generated-api/');
  console.log('\n🚀 Next steps:');
  console.log('   1. cd generated-api');
  console.log('   2. npm install');
  console.log('   3. npm run dev');
}

main().catch(console.error);
```

---

## 🧪 Testing the Integration

### Test 1: Verify Gemini CLI Connection

```bash
npx ts-node src/test-gemini-connection.ts
```

Create `src/test-gemini-connection.ts`:

```typescript
import { GeminiCLIBridge } from './gemini-cli-bridge';

async function test() {
  console.log('Testing Gemini CLI connection...\n');

  try {
    const bridge = new GeminiCLIBridge();
    console.log('✅ Gemini CLI connected successfully!');
    
    // Test can be expanded with actual commands
  } catch (error) {
    console.error('❌ Connection failed:', error);
  }
}

test();
```

### Test 2: Generate Sample Project

```bash
npx ts-node src/main-gemini-complete.ts
```

---

## 📊 Command Reference

### Common Gemini CLI Commands

```bash
# Generate complete project
gemini generate-project "Node.js REST API" --output ./my-api

# Scaffold specific type
gemini scaffold typescript --framework express

# Create API boilerplate
gemini create-api --language typescript --framework express

# Create web app
gemini create-web --framework react

# Generate tests
gemini generate-tests --language typescript --framework jest

# Generate documentation
gemini generate-docs --language typescript --source ./src

# List available templates
gemini list-templates

# List models
gemini list-models
```

---

## ✅ Integration Checklist

- [ ] Ollama running (port 11434)
- [ ] CodeGemma 7B pulled
- [ ] Gemini CLI installed globally
- [ ] Gemini API key set
- [ ] `gemini list-models` works
- [ ] `src/types/gemini-cli.ts` created
- [ ] `src/gemini-cli-bridge.ts` created
- [ ] `src/orchestrator-gemini-integration.ts` created
- [ ] `src/main-gemini-complete.ts` created
- [ ] Test connection works
- [ ] Generate sample project works
- [ ] Multi-agent improvement executes

---

## 🚀 You're Ready!

Both systems are now connected:
- ✅ Gemini CLI for scaffolding
- ✅ Ollama for improvement
- ✅ Automatic integration

Start with: `npx ts-node src/main-gemini-complete.ts`
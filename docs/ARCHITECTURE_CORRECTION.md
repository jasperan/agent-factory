# CRITICAL UPDATE: BridgeCode Architecture - Ollama ONLY + Gemini CLI Integration

## ⚠️ MAJOR CLARIFICATION

### What BridgeCode Actually Is

**NOT:**
- ❌ Cloud-based Gemini API system
- ❌ Optional AI backend choice
- ❌ Hybrid system

**IS:**
- ✅ **Ollama-only** for all code operations
- ✅ **Gemini CLI** for codebase generation ONLY
- ✅ **Two separate systems** that can interoperate

---

## 🏗️ Corrected Architecture

### System 1: BridgeCode Agents (Ollama-Only)
```
Your Code Project
    ↓
BridgeCode Analyzer (Ollama)
    ↓
Generate Tasks
    ↓
Multi-Agent Executor (Ollama)
    ├─ Agent 1 (Ollama)
    ├─ Agent 2 (Ollama)
    ├─ Agent 3 (Ollama)
    └─ Agent N (Ollama)
    ↓
Improved Code Output
```

**Features:**
- ✅ Runs 100% locally on Ollama
- ✅ No API calls
- ✅ No costs
- ✅ Uses CodeGemma 7B model
- ✅ Fully autonomous

---

### System 2: Gemini CLI Integration
```
BridgeCode → "Generate boilerplate for project X"
    ↓
Gemini CLI Interface
    ↓
Command Router
    ├─ gemini generate-project ...
    ├─ gemini create-structure ...
    └─ gemini scaffold-codebase ...
    ↓
Initial Codebase (from Gemini)
    ↓
Feed to BridgeCode Agents (Ollama)
    ↓
Improvement & Enhancement Loop
```

**Features:**
- ✅ Initial codebase scaffolding ONLY
- ✅ Uses Gemini CLI locally
- ✅ Generates boilerplate, structure, templates
- ✅ Then BridgeCode agents refine it
- ✅ One-time generation per project

---

## 🔌 Gemini CLI Connection Layer

### What We're Building

**A bridge between:**
1. **BridgeCode** (local Ollama agents)
2. **Gemini CLI** (codebase generation)

### How It Works

```typescript
class GeminiCLIBridge {
  private geminiCmd = 'gemini';  // Local CLI command
  
  async generateCoreStructure(projectSpec: string): Promise<string> {
    // Execute: gemini generate-project "Node.js API" --output ./generated
    const output = await execSync(`${this.geminiCmd} generate-project "${projectSpec}"`);
    return output;
  }
  
  async createFileStructure(template: string): Promise<void> {
    // Execute: gemini scaffold-typescript --pattern mvc
    await execSync(`${this.geminiCmd} scaffold-${template}`);
  }
  
  async generateBoilerplate(language: string): Promise<string> {
    // Execute: gemini create-boilerplate --language typescript
    return await execSync(`${this.geminiCmd} create-boilerplate --language ${language}`);
  }
}
```

### Workflow

```
1. User: "Generate a Node.js API project"
   ↓
2. BridgeCode detects: needs initial scaffolding
   ↓
3. GeminiCLIBridge executes:
   $ gemini generate-project "Node.js REST API" --output ./my-api
   ↓
4. Gemini CLI creates:
   - src/
   - tests/
   - config/
   - package.json
   - README.md
   - etc.
   ↓
5. BridgeCode loads generated structure
   ↓
6. Ollama agents analyze and improve:
   - Add error handling
   - Optimize database queries
   - Add tests
   - Add documentation
   ↓
7. Final production-ready code
```

---

## 💻 Implementation Details

### Prerequisites

**1. Ollama Running**
```bash
ollama serve
# In another terminal:
ollama pull codegemma:7b
```

**2. Gemini CLI Installed**
```bash
# Install Gemini CLI locally
npm install -g @google/genai-cli
# Or get from: https://github.com/google/genai

# Authenticate
gemini auth --api-key YOUR_API_KEY
```

**3. Verify Both Work**
```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test Gemini CLI
gemini --version
gemini list-models
```

---

### BridgeCode + Gemini CLI Integration Code

#### src/gemini-cli-bridge.ts

```typescript
import { execSync, exec } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface GenerationOptions {
  projectName: string;
  outputDir: string;
  language?: string;
  template?: string;
  description?: string;
}

/**
 * Bridge between BridgeCode and Gemini CLI
 * Handles initial codebase generation via Gemini CLI
 */
export class GeminiCLIBridge {
  private geminiCmd: string;
  private maxRetries = 3;
  private retryDelay = 2000;

  constructor(geminiPath: string = 'gemini') {
    this.geminiCmd = geminiPath;
    this.verifyGeminiCLI();
  }

  /**
   * Verify Gemini CLI is installed and accessible
   */
  private verifyGeminiCLI(): void {
    try {
      const result = execSync(`${this.geminiCmd} --version`, { encoding: 'utf-8' });
      console.log(`✅ Gemini CLI detected: ${result.trim()}`);
    } catch (error) {
      throw new Error(
        `❌ Gemini CLI not found. Install with: npm install -g @google/genai-cli`
      );
    }
  }

  /**
   * Generate complete project structure via Gemini CLI
   */
  async generateProject(options: GenerationOptions): Promise<string> {
    console.log(`\n🔷 Gemini CLI: Generating ${options.projectName}...`);

    const cmd = this.buildGenerateCommand(options);
    
    try {
      const output = await this.executeCommand(cmd);
      console.log(`✅ Project generated in: ${options.outputDir}`);
      return output;
    } catch (error) {
      console.error(`❌ Generation failed:`, error);
      throw error;
    }
  }

  /**
   * Build Gemini CLI command for project generation
   */
  private buildGenerateCommand(options: GenerationOptions): string {
    const parts = [
      this.geminiCmd,
      'generate-project',
      `"${options.description || options.projectName}"`,
      `--output ${options.outputDir}`,
      `--name ${options.projectName}`
    ];

    if (options.language) parts.push(`--language ${options.language}`);
    if (options.template) parts.push(`--template ${options.template}`);

    return parts.join(' ');
  }

  /**
   * Generate specific file scaffolding
   */
  async scaffoldFile(
    fileType: string,
    options?: Record<string, string>
  ): Promise<string> {
    console.log(`\n🔷 Gemini CLI: Scaffolding ${fileType}...`);

    const optionsStr = options
      ? Object.entries(options)
          .map(([key, val]) => `--${key} ${val}`)
          .join(' ')
      : '';

    const cmd = `${this.geminiCmd} scaffold ${fileType} ${optionsStr}`;

    try {
      return await this.executeCommand(cmd);
    } catch (error) {
      console.error(`❌ Scaffolding failed:`, error);
      throw error;
    }
  }

  /**
   * Create boilerplate code for specific language
   */
  async createBoilerplate(language: string, pattern?: string): Promise<string> {
    console.log(`\n🔷 Gemini CLI: Creating ${language} boilerplate...`);

    const cmd = pattern
      ? `${this.geminiCmd} create-boilerplate --language ${language} --pattern ${pattern}`
      : `${this.geminiCmd} create-boilerplate --language ${language}`;

    try {
      return await this.executeCommand(cmd);
    } catch (error) {
      console.error(`❌ Boilerplate creation failed:`, error);
      throw error;
    }
  }

  /**
   * List available templates
   */
  async listTemplates(type?: string): Promise<string[]> {
    console.log(`\n🔷 Gemini CLI: Listing available templates...`);

    const cmd = type
      ? `${this.geminiCmd} list-templates --type ${type}`
      : `${this.geminiCmd} list-templates`;

    try {
      const output = await this.executeCommand(cmd);
      return output.split('\n').filter(line => line.trim());
    } catch (error) {
      console.error(`❌ List templates failed:`, error);
      return [];
    }
  }

  /**
   * Execute command with retry logic
   */
  private async executeCommand(cmd: string, attempt = 1): Promise<string> {
    try {
      console.log(`[Attempt ${attempt}/${this.maxRetries}] Executing: ${cmd}`);
      
      const { stdout, stderr } = await execAsync(cmd, {
        timeout: 60000, // 60 second timeout
        maxBuffer: 10 * 1024 * 1024 // 10MB buffer
      });

      if (stderr) console.warn(`⚠️ Warning:`, stderr);
      return stdout;
    } catch (error: any) {
      if (attempt < this.maxRetries) {
        console.warn(`⚠️ Attempt ${attempt} failed, retrying in ${this.retryDelay}ms...`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.executeCommand(cmd, attempt + 1);
      }
      throw error;
    }
  }

  /**
   * Validate generated project structure
   */
  async validateGeneratedProject(projectPath: string): Promise<boolean> {
    console.log(`\n🔍 Validating generated project...`);

    const requiredFiles = [
      'package.json',
      'README.md'
    ];

    for (const file of requiredFiles) {
      const filePath = path.join(projectPath, file);
      if (!fs.existsSync(filePath)) {
        console.warn(`⚠️ Missing: ${file}`);
        return false;
      }
    }

    console.log(`✅ Project structure valid`);
    return true;
  }

  /**
   * Get project metadata from generated code
   */
  getProjectMetadata(projectPath: string): Record<string, any> {
    const packageJsonPath = path.join(projectPath, 'package.json');
    
    if (fs.existsSync(packageJsonPath)) {
      const content = fs.readFileSync(packageJsonPath, 'utf-8');
      return JSON.parse(content);
    }

    return {};
  }
}
```

---

### Integration with BridgeCode Orchestrator

#### src/orchestrator-with-gemini.ts

```typescript
import { GeminiCLIBridge } from './gemini-cli-bridge';
import { Orchestrator } from './orchestrator';
import { CodeModel } from './code-model';
import { FileManager } from './file-manager';

interface ProjectInitOptions {
  name: string;
  description: string;
  language: string;
  outputDir: string;
  useGeminiScaffold?: boolean; // Default: true
}

/**
 * Extended Orchestrator with Gemini CLI integration
 */
export class OrchestratorWithGemini {
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
   * Initialize new project with Gemini scaffold + BridgeCode improvement
   */
  async initializeProject(options: ProjectInitOptions): Promise<void> {
    console.log(`\n╔════════════════════════════════════════╗`);
    console.log(`║   🌉 BridgeCode + Gemini CLI Setup     ║`);
    console.log(`╚════════════════════════════════════════╝\n`);

    // Step 1: Use Gemini CLI to generate initial structure
    if (options.useGeminiScaffold !== false) {
      console.log(`📍 PHASE 1: Initial Codebase Generation (Gemini CLI)\n`);
      
      await this.geminiBridge.generateProject({
        projectName: options.name,
        outputDir: options.outputDir,
        language: options.language,
        description: options.description
      });

      // Validate the generated project
      const isValid = await this.geminiBridge.validateGeneratedProject(options.outputDir);
      if (!isValid) {
        throw new Error('Generated project validation failed');
      }

      // Get metadata
      const metadata = this.geminiBridge.getProjectMetadata(options.outputDir);
      console.log(`\n📊 Project Metadata:`, metadata);
    }

    // Step 2: Analyze generated code and prepare improvement tasks
    console.log(`\n📍 PHASE 2: Code Analysis & Task Generation (Ollama)\n`);

    const codebaseFiles = this.fileManager.listFiles(options.outputDir);
    console.log(`Found ${codebaseFiles.length} files to analyze`);

    // Step 3: BridgeCode agents improve the generated code
    console.log(`\n📍 PHASE 3: Multi-Agent Improvement (Ollama)\n`);

    const improvementTasks = this.generateImprovementTasks(codebaseFiles);
    this.orchestrator.addTasks(improvementTasks);
    
    await this.orchestrator.run();

    console.log(`\n✅ Complete! Generated project with improvements ready in: ${options.outputDir}`);
  }

  /**
   * Generate improvement tasks for generated codebase
   */
  private generateImprovementTasks(files: string[]) {
    return files.map((file, index) => ({
      id: `improve-${index}`,
      title: `Improve ${file}`,
      description: 'Add error handling, validation, and documentation',
      type: 'refactor',
      priority: 'high',
      affected_files: [file],
      effort_hours: 1
    }));
  }

  /**
   * Add custom tasks after project initialization
   */
  async addCustomTasks(tasks: any[]): Promise<void> {
    console.log(`\n📍 PHASE 4: Custom Enhancement Tasks\n`);
    this.orchestrator.addTasks(tasks);
    await this.orchestrator.run();
  }
}
```

---

### Complete Workflow Example

#### src/main-with-gemini.ts

```typescript
import 'dotenv/config';
import { OrchestratorWithGemini } from './orchestrator-with-gemini';
import { CodeModel } from './code-model';
import { FileManager } from './file-manager';

async function main() {
  console.log('╔════════════════════════════════════════╗');
  console.log('║   🌉 BridgeCode + Gemini CLI          ║');
  console.log('║   Complete Workflow Example            ║');
  console.log('╚════════════════════════════════════════╝\n');

  // Initialize
  const model = new CodeModel();
  const fileManager = new FileManager('.');
  const orchestrator = new OrchestratorWithGemini(model, fileManager, 4);

  // Step 1: Initialize new Node.js API project
  console.log('🚀 Starting project initialization...\n');

  await orchestrator.initializeProject({
    name: 'my-rest-api',
    description: 'Production-grade Node.js REST API with TypeScript',
    language: 'typescript',
    outputDir: './generated-api',
    useGeminiScaffold: true // Generate structure with Gemini CLI
  });

  // Step 2: Add custom improvement tasks
  console.log('\n📋 Adding custom enhancement tasks...\n');

  const customTasks = [
    {
      id: 'add-tests',
      title: 'Add comprehensive test suite',
      description: 'Generate unit and integration tests with Jest',
      type: 'testing',
      priority: 'high',
      affected_files: ['generated-api/src/**/*.ts'],
      effort_hours: 2
    },
    {
      id: 'add-logging',
      title: 'Add structured logging',
      description: 'Implement Winston logging with different levels',
      type: 'enhancement',
      priority: 'medium',
      affected_files: ['generated-api/src/**/*.ts'],
      effort_hours: 1
    },
    {
      id: 'add-validation',
      title: 'Add request validation',
      description: 'Use Joi/Zod for request schema validation',
      type: 'security',
      priority: 'high',
      affected_files: ['generated-api/src/**/*.ts'],
      effort_hours: 1.5
    }
  ];

  await orchestrator.addCustomTasks(customTasks);

  console.log('\n✅ Project complete and ready for deployment!');
  console.log('📁 Location: ./generated-api/');
}

main().catch(console.error);
```

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ USER INITIATES: "Generate Node.js REST API"                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Gemini CLI Scaffolding (ONE-TIME)                 │
│ $ gemini generate-project "Node.js REST API"               │
│ $ gemini scaffold typescript --pattern mvc                 │
│                                                              │
│ Output:                                                      │
│ ├── src/                                                     │
│ ├── tests/                                                   │
│ ├── config/                                                  │
│ ├── package.json ✅                                          │
│ └── README.md                                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: BridgeCode Analysis (Ollama)                       │
│ • Scan generated files                                       │
│ • Identify improvement opportunities                         │
│ • Generate 10-20 improvement tasks                           │
│ • Estimate effort (40-50 agent-hours)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Multi-Agent Improvement (4 Ollama Agents)         │
│                                                              │
│ Agent 1: Add error handling        Agent 3: Add logging     │
│ Agent 2: Add documentation         Agent 4: Optimize DB     │
│                                                              │
│ Each agent runs in parallel, processing 10+ tasks           │
│ Total time: 5-10 minutes (vs 40-50 hours manual)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Custom Tasks (Optional)                            │
│ • Add tests + coverage                                       │
│ • Add validation                                             │
│ • Add monitoring                                             │
│ • Security hardening                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ✅ PRODUCTION-READY CODE                                    │
│ • 1,000+ lines of improved code                             │
│ • Full test coverage                                         │
│ • Error handling everywhere                                  │
│ • Documentation complete                                     │
│ • Ready to deploy                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Updated Architecture

### Before (What We're NOT Doing)
```
❌ Single AI backend
❌ Choose between Gemini or Ollama
❌ Hybrid system
```

### After (What We ARE Doing)
```
✅ Gemini CLI: Initial scaffolding ONLY
✅ Ollama: All agent work, analysis, improvement
✅ Two separate systems: perfectly divided
```

### Key Points

- **Gemini CLI** = One-time project initialization
- **Ollama** = Continuous improvement and analysis
- **No API calls** = All agent work is local and free
- **No conflicts** = Each system has clear responsibility

---

## 💰 Cost Breakdown (Corrected)

### One Project Lifecycle

| Phase | Tool | Cost | Time |
|-------|------|------|------|
| Generate Structure | Gemini CLI | ~$0.10 | 30 sec |
| Analyze & Task Gen | Ollama | $0 | 2 min |
| 4-Agent Improvement | Ollama | $0 | 8 min |
| Custom Tasks | Ollama | $0 | 5 min |
| **TOTAL** | | **~$0.10** | **15 min** |

### Per Month (5 projects)
- Gemini CLI calls: ~$0.50
- **Total: ~$0.50/month**

### ROI: Infinite (essentially free) 📈

---

## ✅ Implementation Checklist

- [ ] Install Ollama locally
- [ ] Pull CodeGemma 7B
- [ ] Install Gemini CLI
- [ ] Authenticate Gemini CLI with API key
- [ ] Create src/gemini-cli-bridge.ts
- [ ] Create src/orchestrator-with-gemini.ts
- [ ] Create src/main-with-gemini.ts
- [ ] Update tsconfig.json
- [ ] Test Ollama connection
- [ ] Test Gemini CLI connection
- [ ] Run main.ts
- [ ] Verify generated project improvements

---

**Corrected November 2026 | BridgeCode Architecture v2.0**
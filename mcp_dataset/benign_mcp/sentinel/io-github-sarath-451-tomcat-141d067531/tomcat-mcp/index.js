import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema
} from "@modelcontextprotocol/sdk/types.js";

import { exec } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const config = JSON.parse(
  fs.readFileSync(path.join(__dirname, "config.json"), "utf-8")
);

const server = new Server(
  { name: "tomcat-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

function classifyTomcatError(logText) {
  if (/Address already in use|BindException/i.test(logText))
    return "Port conflict: another process is using the Tomcat port";

  if (/UnsupportedClassVersionError/i.test(logText))
    return "Java version mismatch (compiled with newer Java)";

  if (/OutOfMemoryError/i.test(logText))
    return "JVM out of memory";

  if (/NoClassDefFoundError|ClassNotFoundException/i.test(logText))
    return "Missing or conflicting JARs";

  if (/Permission denied|Access is denied/i.test(logText))
    return "File or folder permission issue";

  return "Unknown startup issue – check stack trace";
}

/* -----------------------------
   TOOL DEFINITIONS
-------------------------------- */

const tools = {
  start_tomcat: async () => {
  return new Promise((resolve) => {
    exec(
      `cmd /c "${config.BIN_DIR}\\startup.bat" >> "${config.LOG_DIR}\\catalina-combined.log" 2>&1`,
      {
        cwd: config.TOMCAT_HOME,
        env: {
          ...process.env,
          JAVA_HOME: config.JAVA_HOME,
          CATALINA_HOME: config.TOMCAT_HOME
        }
      },
      (err) => {
        if (err) {
          return resolve("Tomcat startup failed.");
        }
        resolve("Tomcat started with combined logging.");
      }
    );
  });
  },

  stop_tomcat: async () => {
    return new Promise((resolve) => {
      exec(
        `jcmd | findstr /i "org.apache.catalina.startup.Bootstrap"`,
        (err, stdout) => {
          if (!stdout) {
            return resolve("Tomcat process not found.");
          }
  
          const pid = stdout.trim().split(/\s+/)[0];
  
          exec(`taskkill /PID ${pid} /F`, (killErr) => {
            if (killErr) {
              return resolve("Failed to kill Tomcat process.");
            }
  
            resolve(`Tomcat process ${pid} terminated successfully.`);
          });
        }
      );
    });
  },

  check_tomcat_status: async () => {
    return new Promise((resolve) => {
      exec(`netstat -ano | findstr :${config.PORT}`, (_, stdout) => {
        resolve(
          stdout && stdout.length > 0
            ? `Tomcat is running on port ${config.PORT}`
            : "Tomcat is NOT running"
        );
      });
    });
  },

  read_latest_catalina_log: async () => {
    const files = fs
      .readdirSync(config.LOG_DIR)
      .filter(f => f.startsWith("catalina"))
      .sort()
      .reverse();

    if (!files.length) return "No catalina logs found";

    const logPath = path.join(config.LOG_DIR, files[0]);
    return fs.readFileSync(logPath, "utf-8")
      .split("\n")
      .slice(-200)
      .join("\n");
  },

  diagnose_startup_failure: async () => {
  const portStatus = await tools.check_tomcat_status();

  const files = fs.readdirSync(config.LOG_DIR)
    .filter(f => f.startsWith("catalina"))
    .sort()
    .reverse();

  if (!files.length) {
    return "Tomcat is not running and no catalina logs were found.";
  }

  const logPath = path.join(config.LOG_DIR, files[0]);
  const logText = fs.readFileSync(logPath, "utf-8");
  const lastLines = logText.split("\n").slice(-200).join("\n");

  const diagnosis = classifyTomcatError(logText);

  return `
STATUS:
${portStatus}

DIAGNOSIS:
${diagnosis}

LAST LOGS:
${lastLines}
`;
},

deploy_war: async ({ warPath }) => {
  if (!warPath || !warPath.endsWith(".war")) {
    throw new Error("You must provide a valid .war file path");
  }

  if (!fs.existsSync(warPath)) {
    throw new Error("WAR file does not exist");
  }

  const warName = path.basename(warPath);
  const targetPath = path.join(config.WEBAPPS_DIR, warName);

  // Backup existing WAR if present
  if (fs.existsSync(targetPath)) {
    const backupPath = path.join(
      config.BACKUP_DIR,
      `${warName}.${Date.now()}.bak`
    );
    fs.copyFileSync(targetPath, backupPath);
  }

  // Copy new WAR
  fs.copyFileSync(warPath, targetPath);

  // Restart Tomcat
  await tools.stop_tomcat();
  await new Promise(r => setTimeout(r, 3000));
  await tools.start_tomcat();

  return `WAR deployed and Tomcat restarted: ${warName}`;
},

thread_dump: async () => {
  return new Promise((resolve, reject) => {
    exec(
      `jcmd | findstr /i "org.apache.catalina.startup.Bootstrap"`,
      (err, stdout) => {
        if (!stdout) {
          return resolve("Tomcat JVM process not found");
        }

        const pid = stdout.trim().split(/\s+/)[0];

        exec(`jcmd ${pid} Thread.print`, (err, output) => {
          if (err) reject(err);
          resolve(output);
        });
      }
    );
  });
},

analyze_gc_log: async () => {
  if (!fs.existsSync(config.GC_LOG)) {
    return "GC log not found";
  }

  const log = fs.readFileSync(config.GC_LOG, "utf-8");

  let fullGCs = (log.match(/Full GC/g) || []).length;
  let youngGCs = (log.match(/Pause Young/g) || []).length;

  return `
GC ANALYSIS:
Young GCs: ${youngGCs}
Full GCs: ${fullGCs}

INTERPRETATION:
${fullGCs > 5
  ? "High Full GC count – possible memory pressure"
  : "GC activity looks normal"}
`;
},

rollback_last_deployment: async () => {
  const backups = fs.readdirSync(config.BACKUP_DIR)
    .filter(f => f.endsWith(".bak"))
    .sort()
    .reverse();

  if (!backups.length) {
    return "No backup WARs available for rollback";
  }

  const latestBackup = backups[0];
  const originalWar = latestBackup.replace(/\.\d+\.bak$/, "");
  const target = path.join(config.WEBAPPS_DIR, originalWar);

  fs.copyFileSync(
    path.join(config.BACKUP_DIR, latestBackup),
    target
  );

  await tools.stop_tomcat();
  await new Promise(r => setTimeout(r, 3000));
  await tools.start_tomcat();

  return `Rollback completed using ${latestBackup}`;
},

heap_dump: async () => {
  return new Promise((resolve) => {
    exec(
      `jcmd | findstr /i "org.apache.catalina.startup.Bootstrap"`,
      (err, stdout) => {
        if (!stdout) {
          return resolve("Tomcat JVM process not found");
        }

        const pid = stdout.trim().split(/\s+/)[0];
        const dumpPath = path.join(
          config.HEAP_DUMP_DIR,
          `heap-${Date.now()}.hprof`
        );

        exec(`jcmd ${pid} GC.heap_dump "${dumpPath}"`);
        resolve(`Heap dump created at ${dumpPath}`);
      }
    );
  });
}


};

/* -----------------------------
   MCP HANDLERS
-------------------------------- */

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: Object.keys(tools).map(name => ({
    name,
    description: name.replace(/_/g, " "),
    inputSchema: { type: "object", properties: {} }
  }))
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const fn = tools[request.params.name];
  if (!fn) {
    throw new Error(`Unknown tool: ${request.params.name}`);
  }

  const result = await fn();
  return {
    content: [{ type: "text", text: result }]
  };
});

/* -----------------------------
   START SERVER
-------------------------------- */

const transport = new StdioServerTransport();
await server.connect(transport);

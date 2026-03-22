const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;
let flaskProcess;
const FLASK_PORT = 5000;
const FLASK_URL = `http://localhost:${FLASK_PORT}`;

function startFlaskServer() {
  const serverPath = path.join(__dirname, "server.py");
  const env = { ...process.env, PORT: String(FLASK_PORT), FLASK_DEBUG: "0" };

  flaskProcess = spawn("python", [serverPath], { env, stdio: "pipe" });

  flaskProcess.stdout.on("data", (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.stderr.on("data", (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.on("error", (err) => {
    console.error("Failed to start Flask server:", err.message);
  });

  flaskProcess.on("close", (code) => {
    console.log(`Flask server exited with code ${code}`);
  });
}

function waitForServer(url, timeout = 15000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const http = require("http");
      http
        .get(url + "/health", (res) => {
          if (res.statusCode === 200) resolve();
          else if (Date.now() - start > timeout) reject(new Error("Server timeout"));
          else setTimeout(check, 300);
        })
        .on("error", () => {
          if (Date.now() - start > timeout) reject(new Error("Server timeout"));
          else setTimeout(check, 300);
        });
    };
    check();
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: "MIDAS Gen Dashboard",
    backgroundColor: "#0d1117",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.setMenuBarVisibility(false);

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  await mainWindow.loadURL(FLASK_URL);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  startFlaskServer();

  try {
    await waitForServer(FLASK_URL);
    await createWindow();
  } catch (err) {
    console.error("Could not start:", err.message);
    app.quit();
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (flaskProcess && !flaskProcess.killed) {
    flaskProcess.kill();
  }
});

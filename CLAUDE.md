- Always warn about context remaining and before starting a new task, make sure the left over context is enough for the task or not. If Not ask the user to compact.
- Write all Documentation files that are in MarkDown format to the /md/ directory.

## Server Configuration

### LiMOS Unified API Server
- **Port:** 9000 (ALWAYS)
- **Launcher:** `/Users/ksd/Projects/LiMOS/projects/api/run_unified_api.py`
- **URLs:**
  - Base: http://localhost:9000
  - Health: http://localhost:9000/health
  - Docs: http://localhost:9000/docs
- **Modules:**
  - Orchestrator: `/api/orchestrator/command`
  - Accounting: `/api/accounting/*`
  - Fleet: `/api/fleet/*`

### Web UIs
- **Fleet Management:** http://localhost:5173
- **Accounting:** http://localhost:5174

### Starting Servers
When asked to reload or start servers:
1. Unified API: `cd /Users/ksd/Projects/LiMOS/projects/api && python3 run_unified_api.py`
2. Fleet Web UI: `cd /Users/ksd/Projects/LiMOS/projects/fleet/web-ui && npm run dev`
3. Accounting Web UI: `cd /Users/ksd/Projects/LiMOS/projects/accounting/web-ui && npm run dev`
# GenAI-Logic API Logic Server - Auto-Generated Microservice

**🎯 What's Automatically Created:**
- ✅ **Admin Web App** - Multi-page React app at `http://localhost:5656`
    * Customize at `ui/admin/admin.yaml`
    * You can also create a fully customizabe react app: `gail genai-add-app --app-name=react-app --vibe`
- ✅ **JSON:API Endpoints** - REST API for all database tables at `/api/*`
- ✅ **Swagger Documentation** - Interactive API docs at `/api`
- ✅ **Business Logic Engine** - Declarative rules in `logic/declare_logic.py`
- ✅ **Security Framework** - Authentication/authorization in `security/`
- ✅ **Database Models** - SQLAlchemy ORM in `database/models.py`

See readme files under api, logic and security.

**🚀 Ready to Run:** This is a complete, working system. Just press F5 or run `python api_logic_server_run.py`

<br>

---

# 🚀 Quick Start

**Bootstrap Copilot by pasting the following into the chat:**
```
Please load `.github/.copilot-instructions.md`.
```

<br>

**Microservice Automation Complete -- run to verify:** for **VSCode** projects except those downloaded from Web/GenAI:
1. `Press F5 to Run` (your venv is defaulted)  

&emsp;&emsp;&emsp;&emsp;For **other IDEs,** please follow the [Setup and Run](#1-setup-and-run) procedure, below.

<br>

> 💡 **Tip:** Create the sample app for customization examples:  
> `ApiLogicServer create --project-name=nw_sample --db_url=nw+`

&nbsp;


# This illustrates the power of the allocation rule

```text
Departments own a series of General Ledger Accounts.

Departments also own Department Charge Definitions — each defines what percent
of an allocated cost flows to each of the Department's GL Accounts.
An active Department Charge Definition must cover exactly 100% (derived: 
total_percent = sum of lines; is_active = 1 when total_percent == 100).

Project Funding Definitions define which Departments fund a designated percent
of a Project's costs, and which Department Charge Definition each Department
applies. An active Project Funding Definition must cover exactly 100% (derived:
total_percent = sum of lines; is_active = 1 when total_percent == 100).

Projects are assigned to a Project Funding Definition.

When a Charge is received against a Project, cascade-allocate it in two levels:
  Level 1 — allocate the Charge amount to each Department per their 
             Project Funding Line percent → creates ChargeDeptAllocation rows
  Level 2 — allocate each ChargeDeptAllocation amount to that Department's 
             GL Accounts per their Charge Definition line percents
             → creates ChargeGlAllocation rows

Constraint: a Charge may only be posted if the Project's 
Project Funding Definition is active.
```
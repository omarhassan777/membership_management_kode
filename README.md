# Membership Management Module for KODE Sports Club

Custom Odoo 16 module for managing member data, renewals, branch relationships, and approval workflows.

## Setup Instructions

### Prerequisites
- Docker and Docker Compose installed.
- Git (optional for GitHub upload).


#### Alternative Setup (Manual Installation with Existing Odoo Addons)
If you have an Odoo 16 environment with an `addons` directory and prefer not to use Docker, follow these steps:
1. **Copy the Module**:
   - Download or clone the module folder `membership_management_kode` from the GitHub repository (https://github.com/omarhass777/membership_management_kode).
   - Place the `membership_management_kode` folder inside the `addons` directory of your Odoo 16 installation (e.g., `/path/to/odoo-16/addons/`).

2. **Update Addons Path**:
   - Ensure the `addons_path` in your Odoo configuration file (e.g., `odoo.conf`) includes the path to your custom `addons` directory. Add or modify the line:
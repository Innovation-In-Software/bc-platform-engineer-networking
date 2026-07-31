# Lab 9 – Config with RESTCONF

**Course:** Network Automation Tools — Day 3  
**Prerequisite:** Lab 8 complete — `~/python-lab` with an active virtual environment; Loopback0 configured on both routers (Lab 3)  
**Objective:** Move from the CLI to a programmatic API. Enable RESTCONF on the routers, read interface data as JSON with the `requests` library, change a description with a PATCH, and verify the result — then compare the approach to `ios_config`.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

RESTCONF exposes the device's configuration as a web API. Data comes back as structured JSON, so there is nothing to scrape. In this lab you will:

1. Enable RESTCONF and create an API user on both routers
2. Install `requests` in your virtual environment
3. GET an interface's configuration as JSON
4. PATCH the interface description with a new value
5. Verify the change with another GET
6. Compare the API approach to `ios_config`

Your Lab 1 security group already allows HTTPS on port 443, so RESTCONF is reachable from the control node.

---

## Part 1 — Enable RESTCONF on the Routers

RESTCONF uses HTTPS basic authentication, so it needs its own username and password on the device — separate from how you log in over SSH. Enable the feature, tell the HTTP server to authenticate against the local user database, and create an API user on **each** router.

### Step 1. SSH to the first router

Connect with the `ansible` login (password `Cisco123!`):

```bash
ssh ansible@<c8kv-1-private-ip>
```

You land at the privileged-exec prompt, `c8kv-1#`.

### Step 2. Enter config mode, enable RESTCONF, and add a user

The block below **starts with `configure terminal`** — the RESTCONF and `username` commands are configuration commands and only work in config mode. After the first line your prompt must read `c8kv-1(config)#`; if it still shows `c8kv-1#`, the later commands will be rejected with `% Invalid input detected`.

```
configure terminal
ip http secure-server
ip http authentication local
restconf
username apiuser privilege 15 secret L@bRestconf123
end
write memory
```

Then type `exit` to close the SSH session. Repeat Steps 1–2 on `c8kv-2`. Both routers now accept RESTCONF calls authenticated as `apiuser`.

> **Note:** `restconf` requires `ip http secure-server` to be enabled — RESTCONF only listens over HTTPS. The `privilege 15` user is what the API authenticates as. The `ip http authentication local` line is important: without it the HTTP server may fall back to enable-password authentication and reject `apiuser` with **401 Unauthorized**. This line tells it to authenticate RESTCONF calls against the local `username` database, which is where `apiuser` lives.

> **Important — RESTCONF takes a few minutes to start.** Enabling `restconf` launches a set of background "yang-management" processes (nginx, confd, pubd, dmiauthd, …). Until they finish coming up — typically **2–5 minutes** — your RESTCONF calls will return **`502 Bad Gateway`** even though the configuration is completely correct. A `502` is not an error in your script or credentials; it just means the backend isn't ready yet. Wait a couple of minutes and try again.
>
> You can watch the processes come up. SSH to the router and run:
> ```
> show platform software yang-management process
> ```
> The RESTCONF-relevant processes should all read `Running`:
> ```
> confd            : Running
> nesd             : Running
> syncfd           : Running
> dmiauthd         : Running
> nginx            : Running
> ndbmand          : Running
> pubd             : Running
> ```
> **`ncsshd : Not Running` is fine** — that is the NETCONF-over-SSH daemon (port 830), which RESTCONF does not use. You only need it if you later enable `netconf-yang`. Once `nginx`, `dmiauthd`, `confd`, and `pubd` are `Running`, RESTCONF will answer.

---

## Part 2 — Read Interface Data

### Step 3. Activate your environment and install requests

```bash
cd ~/python-lab
source venv/bin/activate
pip install requests
```

### Step 4. Create a GET script

The routers use self-signed certificates, so you disable certificate verification for the lab and silence the resulting warning. Replace the IP with `c8kv-1`.

```bash
cat > restconf_get.py << 'EOF'
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HOST = "10.0.1.X"
AUTH = ("apiuser", "L@bRestconf123")
HEADERS = {"Accept": "application/yang-data+json"}

url = f"https://{HOST}/restconf/data/ietf-interfaces:interfaces/interface=Loopback0"

response = requests.get(url, auth=AUTH, headers=HEADERS, verify=False)

print("Status code:", response.status_code)
print(response.json())
EOF
```

### Step 5. Run it

```bash
python3 restconf_get.py
```

**Expected output (abridged):**
```
Status code: 200
{'ietf-interfaces:interface': [{'name': 'Loopback0', 'type': 'iana-if-type:softwareLoopback', 'enabled': True, 'ietf-ip:ipv4': {'address': [{'ip': '172.16.1.x', 'netmask': '255.255.255.255'}]}, ...}]}
```

> **Note the list.** The interface comes back wrapped in a JSON **array** — `'ietf-interfaces:interface': [{...}]` — not a bare object. That is the strict YANG-to-JSON encoding (a list is always an array, even for a single entry). Keep this in mind for the PATCH in Step 6: the payload must use the same list shape.

| Element | What it does |
|---------|-------------|
| `https://.../restconf/data/...` | The RESTCONF URL identifying a resource |
| `interface=Loopback0` | Selects one specific interface |
| `Accept: application/yang-data+json` | Ask the device to reply in JSON |
| `auth=(user, pass)` | HTTPS basic authentication |
| `verify=False` | Accept the device's self-signed certificate |
| status `200` | The request succeeded |

> **Troubleshooting:**
> - **`502 Bad Gateway`** → RESTCONF is enabled but its backend processes are still starting. Wait 2–5 minutes and retry; see the startup note under Step 2 and check `show platform software yang-management process`.
> - **`401 Unauthorized`** → the HTTP server isn't using local authentication. Confirm `ip http authentication local` is configured (Step 2) and that `apiuser` exists with `privilege 15`.
> - **Connection refused / timeout** → `ip http secure-server` isn't enabled, or the security group isn't allowing HTTPS (443) from the control node (Lab 1).
> - **`404` on the interface** → `Loopback0` doesn't exist on that router; confirm Lab 3 configured it.

---

## Part 3 — Change a Description

### Step 6. Create a PATCH script

`PATCH` updates part of a resource. Here it sets a new description on Loopback0 without touching anything else.

```bash
cat > restconf_patch.py << 'EOF'
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HOST = "10.0.1.X"
AUTH = ("apiuser", "L@bRestconf123")
HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}

url = f"https://{HOST}/restconf/data/ietf-interfaces:interfaces/interface=Loopback0"

payload = {
    "ietf-interfaces:interface": [
        {
            "name": "Loopback0",
            "description": "Configured via RESTCONF",
        }
    ]
}

response = requests.patch(url, auth=AUTH, headers=HEADERS, json=payload, verify=False)
print("Status code:", response.status_code)   # 204 means success, no content
if response.status_code >= 400:
    print(response.text)
EOF
```

> **Why the list form?** The payload mirrors the array you saw in the GET response — `"ietf-interfaces:interface": [ {...} ]`. On this IOS-XE version the interface is a YANG list, so the PATCH body must be a list too; a bare object can be rejected. The `if response.status_code >= 400` line prints the device's error body so you can see the reason if anything goes wrong.

### Step 7. Run it

```bash
python3 restconf_patch.py
```

**Expected output:**
```
Status code: 204
```

A `204` means the change was applied and there is no response body — the RESTCONF equivalent of a successful config push.

---

## Part 4 — Verify and Reflect

### Step 8. Confirm the change two ways

Re-run the GET script and look for the new description in the JSON:

```bash
python3 restconf_get.py
```

Then confirm on the device itself:

```bash
ssh ansible@<c8kv-1-private-ip>
show running-config interface Loopback0
exit
```

You should see `description Configured via RESTCONF`.

### Step 9. Compare to ios_config

You have now made the same kind of change three ways across the course: `ios_config` in Ansible (Day 1), Netmiko `send_config_set` (Lab 7 concept), and RESTCONF here.

> **Note:** RESTCONF is idempotent by nature — sending the same PATCH again returns `204` and changes nothing, because you are declaring desired state, not issuing commands. This mirrors the idempotency you saw with `ios_config`.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| RESTCONF enabled on both routers | `restconf` and `ip http secure-server` present | |
| API user created | `apiuser` with privilege 15 | |
| `requests` installed | `pip list` shows requests | |
| GET returns data | Status `200`, JSON for Loopback0 | |
| PATCH applies change | Status `204` | |
| Change verified | Description visible via GET and CLI | |

---

## Reflection Questions

1. RESTCONF authenticates with its own `apiuser` credentials over HTTPS. Why keep a separate API user rather than reusing the `ansible` login, and why does the HTTP server need `ip http authentication local`?
2. What do HTTP status codes `200` and `204` tell you about a request?
3. Why is a repeated PATCH idempotent, and how does that compare to `ios_config`?
4. When would you choose an API like RESTCONF over Netmiko or Ansible — and when would you not?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| RESTCONF | Exposes device config as an HTTPS/JSON API |
| `ip http secure-server` + `restconf` | Required to enable RESTCONF |
| `ip http authentication local` | Makes the HTTP server authenticate RESTCONF against local users — without it `apiuser` gets 401 |
| `requests.get()` | Reads a resource as structured JSON |
| `requests.patch()` | Updates part of a resource |
| `verify=False` | Accepts the device's self-signed certificate |
| Status `200` / `204` | Read succeeded / change applied, no body |
| Idempotent by design | Re-sending the same PATCH changes nothing |

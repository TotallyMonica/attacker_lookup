# Attacker Lookup

Find out who keeps attacking your server

## Usage

```bash
git clone https://github.com/TotallyMonica/attacker_lookup
pip install -r requirements.txt
python3 identify.py
```

## Arguments

- `--log`/`--log-file`: specify a log file to be used
  - Required
  - So long as it has IP addresses within it it should work, tested with `journalctl` logs
  - Usage: `--log journalctl.log`

- `--ipinfo-token`: Specify an access token with [ipinfo.io](https://ipinfo.io)
  - Optional
  - If no token is provided, you're limited to the following details:
    - IP
    - City
    - Region
    - Country
    - Location (Based off of GeoIP)
    - Organization (ISP)
    - Postal code
    - Timezone

- `--no-isp-queries`: Disable looking up ISP information
  - Optional

- `--no-rdns`: Disable rDNS querying
  - Optional

## To-do list

- Have `--no-isp-queries` and `--ipinfo-token` conflict with each other
- Have an option for exporting to JSON files
- Break up the main function more
- Consider finding a replacement API for `ipinfo` that provides information without the need for a key

## Credits

Thanks to [Amy](https://github.com/amyipdev) for being the recipient of a brute force SSH attack that prompted me to start writing this.
